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
if [[ "$ENVIRONMENT" == "prod" ]]; then
  HOST_PREFIX="${HOST_PREFIX:-api}"
else
  HOST_PREFIX="${HOST_PREFIX:-api-dev}"
fi

echo "Ensuring ingress-nginx controller is installed..."
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx >/dev/null 2>&1 || true
helm repo update >/dev/null
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.ingressClassResource.name="${INGRESS_CLASS}" \
  --set controller.ingressClassResource.controllerValue="k8s.io/ingress-nginx" \
  --set controller.service.type=LoadBalancer \
  --set controller.replicaCount=1 \
  --wait

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
PUBLIC_API_BASE_URL="http://${PUBLIC_API_HOST}/api/v1"

echo "Patching ingress host ${NAMESPACE}/${INGRESS_NAME} -> ${PUBLIC_API_HOST}"
kubectl -n "${NAMESPACE}" patch ingress "${INGRESS_NAME}" --type='json' \
  -p="[ {\"op\":\"replace\",\"path\":\"/spec/rules/0/host\",\"value\":\"${PUBLIC_API_HOST}\"} ]"

kubectl -n "${NAMESPACE}" annotate ingress "${INGRESS_NAME}" \
  "nginx.ingress.kubernetes.io/ssl-redirect=false" \
  --overwrite

echo "Public API host: ${PUBLIC_API_HOST}"
echo "Public API base URL: ${PUBLIC_API_BASE_URL}"

# Export for Azure DevOps steps
echo "##vso[task.setvariable variable=PUBLIC_API_HOST]${PUBLIC_API_HOST}"
echo "##vso[task.setvariable variable=PUBLIC_API_BASE_URL]${PUBLIC_API_BASE_URL}"
