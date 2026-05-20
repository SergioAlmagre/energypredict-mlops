# 16. HTTPS Ingress + cert-manager Runbook (AKS)

This runbook documents the exact operational process used to make the project work end-to-end over HTTPS in AKS, including real troubleshooting patterns and manual validation commands.

## Objective

Expose the backend API in `prod` with a valid TLS certificate, so the Static Web App frontend (HTTPS) can call the backend without mixed-content errors.

Target example:

- Public API host: `api.<public-ip-dashed>.nip.io`
- Public API base URL: `https://api.<public-ip-dashed>.nip.io/api/v1`

## Deployment order (mandatory)

1. `azure-pipelines-infra.yml`
2. `azure-pipelines-app.yml`
3. `azure-pipelines-frontend.yml`

If frontend runs before backend is healthy/online, UI calls fail (`Failed to fetch`, mixed content, or timeout).

## Required Azure DevOps variables

In `Library > Variable groups > energypredict-shared`:

- `LETSENCRYPT_EMAIL` (required for cert-manager ACME issuer).
- `FRONTEND_PROD_API_BASE_URL` (must be HTTPS when frontend is published).
- `FRONTEND_API_SCHEME_PROD=https` (recommended explicit safety).
- Existing AKS/ACR/Key Vault/workload identity variables must already be correct.

## Core HTTPS flow in prod

### 1) Confirm ingress-nginx service and external IP

```bash
kubectl -n ingress-nginx get svc ingress-nginx-controller -o wide
```

Expected:
- `TYPE` is `LoadBalancer`.
- `EXTERNAL-IP` is populated.
- Ports include `80` and `443`.

### 2) Ensure Azure LB health probe path annotation

```bash
kubectl -n ingress-nginx annotate svc ingress-nginx-controller service.beta.kubernetes.io/azure-load-balancer-health-probe-request-path=/healthz --overwrite
kubectl -n ingress-nginx get svc ingress-nginx-controller -o jsonpath='{.metadata.annotations}'
```

Expected annotation:
- `"service.beta.kubernetes.io/azure-load-balancer-health-probe-request-path":"/healthz"`

Why:
- Without this, Azure LB can mark backends unhealthy and external traffic can timeout.

### 3) Ensure inbound NSG rules for 80/443 (Internet -> nodepool NSG)

PowerShell-safe commands:

```powershell
$nodeRg = az aks show -g rg-energypredict-prod -n aks-energypredict-prod --query nodeResourceGroup -o tsv
$nsg = az network nsg list -g $nodeRg --query "[0].name" -o tsv
az network nsg rule create -g $nodeRg --nsg-name $nsg -n Allow-HTTP-80 --priority 300 --access Allow --direction Inbound --protocol Tcp --source-address-prefixes Internet --source-port-ranges '*' --destination-address-prefixes '*' --destination-port-ranges 80
az network nsg rule create -g $nodeRg --nsg-name $nsg -n Allow-HTTPS-443 --priority 301 --access Allow --direction Inbound --protocol Tcp --source-address-prefixes Internet --source-port-ranges '*' --destination-address-prefixes '*' --destination-port-ranges 443
az network nsg rule list -g $nodeRg --nsg-name $nsg --query "[?name=='Allow-HTTP-80' || name=='Allow-HTTPS-443'].{name:name,priority:priority,access:access,direction:direction}" -o table
```

Expected:
- Both rules exist and `Allow` inbound.

### 4) Check ACME reachability over HTTP

```bash
curl -I --max-time 10 http://api.<public-ip-dashed>.nip.io/
```

Expected successful pattern:
- `HTTP/1.1 308 Permanent Redirect` (or another non-timeout response).

If this still times out:
- ACME HTTP-01 will fail with `Timeout during connect (likely firewall problem)`.

### 5) Reset certificate resources and retry issuance

```bash
kubectl -n energypredict-prod delete secret energypredict-api-prod-tls --ignore-not-found
kubectl -n energypredict-prod delete certificate energypredict-api-prod-tls --ignore-not-found
kubectl -n energypredict-prod delete certificaterequest,order,challenge --all
```

Watch resources (one kind at a time when using `-w`):

```bash
kubectl -n energypredict-prod get challenge -w
kubectl -n energypredict-prod get order -w
kubectl -n energypredict-prod get certificate -w
```

Important:
- `kubectl ... -w` can fail if multiple resource types are specified in one command.

### 6) Verify certificate and TLS secret

```bash
kubectl -n energypredict-prod get certificate,order,challenge
kubectl -n energypredict-prod get secret energypredict-api-prod-tls
```

Expected:
- Certificate `READY=True`.
- Secret `energypredict-api-prod-tls` exists with `TYPE kubernetes.io/tls` and `DATA 2`.

### 7) Validate ingress rule is not broken

```bash
kubectl -n energypredict-prod describe ingress energypredict-api-prod
```

Expected:
- Host is `api.<public-ip-dashed>.nip.io`.
- Path `/` routes to `energypredict-api-prod:80`.

If you see:
- `Host *  Path *  <default>`

Then patch ingress rules:

```bash
kubectl -n energypredict-prod patch ingress energypredict-api-prod --type='merge' -p '{"spec":{"ingressClassName":"nginx","tls":[{"hosts":["api.<public-ip-dashed>.nip.io"],"secretName":"energypredict-api-prod-tls"}],"rules":[{"host":"api.<public-ip-dashed>.nip.io","http":{"paths":[{"path":"/","pathType":"Prefix","backend":{"service":{"name":"energypredict-api-prod","port":{"number":80}}}}]}}]}}'
```

### 8) Validate backend over HTTPS

Use `GET` validation (not HEAD-only checks):

```bash
curl -i https://api.<public-ip-dashed>.nip.io/api/v1/health/ready
```

Expected real successful response:

```text
HTTP/2 200
...
{"status":"ready","database":"ok","model":"ok"}
```

Note:
- `curl -I` can return `405 Method Not Allowed` on endpoints that do not accept `HEAD`. That is not necessarily a service outage.

## Frontend final wiring (SWA)

Set in Library:

- `FRONTEND_PROD_API_BASE_URL=https://api.<public-ip-dashed>.nip.io`
- `FRONTEND_API_SCHEME_PROD=https`

Then re-run:

1. `azure-pipelines-frontend.yml` on `main`.

Expected:
- Register/login and API calls from SWA work without mixed-content errors.

## Common failure patterns and fixes

1. `Mixed Content ... requested insecure resource http://...`
- Cause: frontend on HTTPS calling backend on HTTP.
- Fix: frontend API base URL must be HTTPS.

2. `Challenge invalid ... Timeout during connect (likely firewall problem)`
- Cause: Internet cannot reach `http://<host>/.well-known/acme-challenge/...`.
- Fix:
  - NSG allow 80/443.
  - `azure-load-balancer-health-probe-request-path=/healthz` annotation on ingress service.

3. `you may only specify a single resource type` with `kubectl ... -w`
- Cause: watcher limitation for your CLI version.
- Fix: watch one resource kind per command.

4. PowerShell command errors with `VAR=$(...)`
- Cause: bash syntax used in PowerShell.
- Fix: use `$var = ...` syntax.

5. `echo` prompts for input in PowerShell after jsonpath command
- Cause: PowerShell `echo`/`Write-Output` behavior in pipelines.
- Fix: use `Write-Host ""`.

## Optional manual diagnostics

```bash
kubectl -n energypredict-prod get events --sort-by=.metadata.creationTimestamp | tail -n 60
kubectl -n cert-manager logs deploy/cert-manager --tail=200
kubectl -n ingress-nginx get endpoints ingress-nginx-controller-admission
kubectl -n energypredict-prod get ingress -l acme.cert-manager.io/http01-solver=true -o wide
```

## Proven success checkpoint

A production HTTPS setup is considered complete when all are true:

1. `curl -I http://api.<public-ip-dashed>.nip.io/` returns non-timeout (for example `308`).
2. `kubectl -n energypredict-prod get certificate` shows `READY=True`.
3. `kubectl -n energypredict-prod describe ingress energypredict-api-prod` shows host + backend rule (not wildcard default).
4. `curl -i https://api.<public-ip-dashed>.nip.io/api/v1/health/ready` returns `200` with:
   - `{"status":"ready","database":"ok","model":"ok"}`
5. Frontend registration/login works from SWA.
