#!/usr/bin/env bash
set -euo pipefail

ENVIRONMENT="${1:?Usage: prepare_public_api_endpoint.sh <dev|prod>}"
if [[ "$ENVIRONMENT" != "dev" && "$ENVIRONMENT" != "prod" ]]; then
  echo "ENVIRONMENT must be dev or prod."
  exit 1
fi

NAMESPACE="${NAMESPACE:-energypredict-${ENVIRONMENT}}"
INGRESS_NAME="${INGRESS_NAME:-energypredict-api-${ENVIRONMENT}}"
INGRESS_CLASS="${INGRESS_CLASS:-nginx}"
WILDCARD_DNS_DOMAIN="${WILDCARD_DNS_DOMAIN:-nip.io}"
ENABLE_HTTPS="${ENABLE_HTTPS:-true}"
CERT_MANAGER_VERSION="${CERT_MANAGER_VERSION:-v1.20.2}"
LETSENCRYPT_EMAIL="${LETSENCRYPT_EMAIL:-}"
TLS_SECRET_NAME="${TLS_SECRET_NAME:-${INGRESS_NAME}-tls}"
if [[ "$ENVIRONMENT" == "prod" ]]; then
  HOST_PREFIX="${HOST_PREFIX:-api}"
  ACME_SERVER="${ACME_SERVER:-https://acme-v02.api.letsencrypt.org/directory}"
  CLUSTER_ISSUER_NAME="${CLUSTER_ISSUER_NAME:-letsencrypt-prod}"
else
  HOST_PREFIX="${HOST_PREFIX:-api-dev}"
  ACME_SERVER="${ACME_SERVER:-https://acme-staging-v02.api.letsencrypt.org/directory}"
  CLUSTER_ISSUER_NAME="${CLUSTER_ISSUER_NAME:-letsencrypt-staging}"
fi

echo "Ensuring ingress-nginx controller is installed..."
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx >/dev/null 2>&1 || true
helm repo update >/dev/null

# Helm sometimes times out on first install in small/new clusters.
# We avoid hard fail on short rollout by retrying and handling readiness in the
# explicit "Waiting for public IP" loop below.
for attempt in 1 2 3; do
  if helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
    --namespace ingress-nginx \
    --create-namespace \
    --set controller.ingressClassResource.name="${INGRESS_CLASS}" \
    --set controller.ingressClassResource.controllerValue="k8s.io/ingress-nginx" \
    --set controller.service.type=LoadBalancer \
    --set controller.replicaCount=2 \
    --timeout 15m; then
    break
  fi

  if [[ "$attempt" -lt 3 ]]; then
    echo "Helm install/upgrade failed (attempt $attempt). Retrying in 20s..."
    sleep 20
  else
    echo "Helm install/upgrade failed after 3 attempts."
    exit 1
  fi
done

echo "Waiting for ingress-nginx controller to be ready..."
kubectl -n ingress-nginx rollout status deployment/ingress-nginx-controller --timeout=10m

echo "Waiting for ingress-nginx admission endpoints..."
for _ in $(seq 1 40); do
  ADMISSION_ENDPOINTS="$(kubectl -n ingress-nginx get endpoints ingress-nginx-controller-admission -o jsonpath='{.subsets[0].addresses[0].ip}' 2>/dev/null || true)"
  if [[ -n "${ADMISSION_ENDPOINTS}" ]]; then
    break
  fi
  sleep 15
done

if [[ -z "${ADMISSION_ENDPOINTS:-}" ]]; then
  echo "ingress-nginx admission webhook has no endpoints yet."
  exit 1
fi

echo "Waiting for public IP from ingress-nginx service..."
LB_IP=""
for _ in $(seq 1 40); do
  LB_IP="$(kubectl -n ingress-nginx get svc ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || true)"
  if [[ -n "$LB_IP" ]]; then
    break
  fi
  sleep 15
done

if [[ -z "$LB_IP" ]]; then
  echo "Ingress controller has no public IP yet. Check: kubectl -n ingress-nginx get svc ingress-nginx-controller"
  exit 1
fi

DASHED_IP="${LB_IP//./-}"
PUBLIC_API_HOST="${HOST_PREFIX}.${DASHED_IP}.${WILDCARD_DNS_DOMAIN}"

echo "Patching ingress host ${NAMESPACE}/${INGRESS_NAME} -> ${PUBLIC_API_HOST}"
kubectl -n "${NAMESPACE}" patch ingress "${INGRESS_NAME}" --type='json' \
  -p="[ {\"op\":\"replace\",\"path\":\"/spec/rules/0/host\",\"value\":\"${PUBLIC_API_HOST}\"} ]"

if [[ "${ENABLE_HTTPS}" == "true" ]]; then
  if [[ -z "${LETSENCRYPT_EMAIL}" ]]; then
    echo "LETSENCRYPT_EMAIL is required when ENABLE_HTTPS=true"
    exit 1
  fi

  echo "Ensuring cert-manager is installed..."
  helm repo add jetstack https://charts.jetstack.io >/dev/null 2>&1 || true
  helm repo update >/dev/null
  helm upgrade --install cert-manager jetstack/cert-manager \
    --namespace cert-manager \
    --create-namespace \
    --version "${CERT_MANAGER_VERSION}" \
    --set crds.enabled=true \
    --timeout 15m

  kubectl -n cert-manager rollout status deployment/cert-manager --timeout=10m
  kubectl -n cert-manager rollout status deployment/cert-manager-webhook --timeout=10m
  kubectl -n cert-manager rollout status deployment/cert-manager-cainjector --timeout=10m

  echo "Applying ClusterIssuer ${CLUSTER_ISSUER_NAME}..."
  cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: ${CLUSTER_ISSUER_NAME}
spec:
  acme:
    email: ${LETSENCRYPT_EMAIL}
    server: ${ACME_SERVER}
    privateKeySecretRef:
      name: ${CLUSTER_ISSUER_NAME}-account-key
    solvers:
      - http01:
          ingress:
            class: ${INGRESS_CLASS}
EOF

  echo "Patching ingress for TLS..."
  kubectl -n "${NAMESPACE}" patch ingress "${INGRESS_NAME}" --type='merge' -p "{
    \"metadata\":{
      \"annotations\":{
        \"cert-manager.io/cluster-issuer\":\"${CLUSTER_ISSUER_NAME}\",
        \"acme.cert-manager.io/http01-ingress-class\":\"${INGRESS_CLASS}\",
        \"nginx.ingress.kubernetes.io/ssl-redirect\":\"true\"
      }
    },
    \"spec\":{
      \"tls\":[
        {
          \"hosts\":[\"${PUBLIC_API_HOST}\"],
          \"secretName\":\"${TLS_SECRET_NAME}\"
        }
      ]
    }
  }"

  echo "Waiting for certificate secret ${NAMESPACE}/${TLS_SECRET_NAME}..."
  for _ in $(seq 1 60); do
    if kubectl -n "${NAMESPACE}" get secret "${TLS_SECRET_NAME}" >/dev/null 2>&1; then
      break
    fi
    sleep 10
  done

  if ! kubectl -n "${NAMESPACE}" get secret "${TLS_SECRET_NAME}" >/dev/null 2>&1; then
    echo "TLS secret ${TLS_SECRET_NAME} not created yet. Check cert-manager Certificate/Challenge resources."
    exit 1
  fi

  PUBLIC_API_BASE_URL="https://${PUBLIC_API_HOST}/api/v1"
else
  kubectl -n "${NAMESPACE}" annotate ingress "${INGRESS_NAME}" \
    "nginx.ingress.kubernetes.io/ssl-redirect=false" \
    --overwrite
  PUBLIC_API_BASE_URL="http://${PUBLIC_API_HOST}/api/v1"
fi

echo "Public API host: ${PUBLIC_API_HOST}"
echo "Public API base URL: ${PUBLIC_API_BASE_URL}"

# Export for Azure DevOps steps
echo "##vso[task.setvariable variable=PUBLIC_API_HOST]${PUBLIC_API_HOST}"
echo "##vso[task.setvariable variable=PUBLIC_API_BASE_URL]${PUBLIC_API_BASE_URL}"
