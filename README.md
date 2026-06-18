# EnergyPredict MLOps API

EnergyPredict es una API de mantenimiento predictivo industrial con FastAPI, desplegable en AKS y operada con CI/CD en Azure DevOps.

## What this project includes
- API FastAPI (`/api/v1`) con auth JWT y RBAC.
- Endpoints de prediccion, entrenamiento y health/readiness operativo.
- Despliegue en AKS con `k8s/base` + overlays `dev/prod`.
- Secretos en Key Vault y consumo desde Kubernetes.
- Entrenamiento cloud desacoplado mediante Kubernetes Jobs.
- Drift monitoring batch con Kubernetes CronJob y retraining trigger configurable.
- Predicciones automáticas vía Event Hub + data-processor; `/predict` queda como fallback/demo manual.
- Observabilidad Prometheus/Grafana con `/metrics`, ServiceMonitor, alert rules y dashboard.
- Databricks MLflow/Unity Catalog para tracking y registro formal del modelo.
- Azure Blob Storage para cache operativo de modelos, registry y datasets procesados.
- Frontend estatico para demo funcional del simulador.
- Terraform por stacks (`dev`, `prod`, `devops`) con backend remoto de state.
- Pipelines separados:
  - `azure-pipelines-infra.yml`
  - `azure-pipelines-app.yml`
  - `azure-pipelines-frontend.yml`

## Recruiter / reviewer snapshot

This repository demonstrates a production-oriented MLOps platform rather than a single notebook demo:

- FastAPI service with JWT auth, RBAC, rate limiting and structured request tracing.
- AKS deployment with Kustomize overlays, rolling updates, HPA and startup/readiness/liveness probes.
- Azure DevOps CI/CD split by infrastructure, backend and frontend.
- Terraform-managed Azure platform: AKS, ACR, Key Vault, Databricks, PostgreSQL, Static Web App and model storage.
- MLOps flow with remote training Jobs, Blob-backed model artifacts, Databricks MLflow tracking and Unity Catalog model registration.
- Batch data drift monitor with PSI-based thresholds, stored drift reports, optional alerts and optional retraining trigger.
- Event-driven automatic inference through Event Hub/data-processor plus Prometheus/Grafana runtime observability.
- Public docs and runbooks under `docs/`; private interview prep is intentionally ignored from the public repo.

Generated model artifacts and local runtime registries are not committed. See `models/registry.example.json` for the registry shape.

## E2E replication guide
Esta seccion esta ordenada para replicar el proyecto de forma secuencial en tu entorno.

### 1. Prepare Azure DevOps inputs
1. Configura el Variable Group `energypredict-shared`.
2. No subas `terraform.tfvars` al repo.
3. Genera `TFVARS_DEV_B64` y `TFVARS_PROD_B64`:
```powershell
.\scripts\generate_tfvars_b64.ps1
```
4. Sube esos valores como secretos en Library.

### 2. Run infrastructure pipeline first
Ejecuta `azure-pipelines-infra.yml` para crear backend de Terraform, recursos base y entornos.

Evidencia del paso:
- Pipeline de infra en verde.
![Infra pipeline OK](docs/media/infra-pipeline-ok_censurada.jpg)

- Storage de tfstate remoto en Azure.
![TFState storage resource](docs/media/storage-tfstate-resource_censurada.jpg)

- Resource groups separados por entorno y stack.
![All resource groups](docs/media/all-resource-groups_censurada.jpg)

### 3. Verify provisioned platform
Cuando `infra` termina, revisa que los recursos principales existan antes de desplegar app/frontend.

Evidencia del paso:
- Recursos del entorno productivo.
![EnergyPredict prod resources](docs/media/energypredict-resources-prod_censurada.jpg)

- Recursos de AKS y red asociados.
![AKS resources](docs/media/aks-resources_censurada.jpg)

- Recursos de Databricks (si la opcion esta habilitada).
![Databricks prod resources](docs/media/databricks-prod-resources_censurada.jpg)

- Base de datos PostgreSQL provisionada.
![Azure Database for PostgreSQL dashboard](docs/media/azure-database-for-postgres-sql-dashboard_censurada.jpg)

### 4. Deploy backend to AKS
Ejecuta `azure-pipelines-app.yml` despues de `infra`.

Este pipeline:
- ejecuta lint, tests y security checks,
- construye y publica imagen en ACR,
- despliega en AKS dev/prod segun branch.

Evidencia del paso:
- Vista general del pipeline backend.
![Backend pipeline overview](docs/media/general-pipeline-app_censurada.jpg)

- Auditoria de dependencias en CI.
![Dependency audit in app pipeline](docs/media/dependency-audit-pipeline-app_censurada.jpg)

### 5. Validate backend runtime in Kubernetes
Una vez desplegado el backend, valida estado operativo en AKS.

Evidencia del paso:
- Rollout y estado del deployment.
![Deployment status](docs/media/status-deploy_censurada.jpg)

- Service + Endpoints + Pods conectados.
![Service, endpoints and pods](docs/media/svc-endpoints-pods_censurada.jpg)

- Diagnostico detallado de pod.
![Describe pod output](docs/media/describe-pod_censurada.jpg)

- Eventos de scheduling/mount/pull para troubleshooting.
![Pod events](docs/media/pod-events_censurada.jpg)

- Escalado y consumo (`HPA`, `top`).
![HPA and top metrics](docs/media/hpa-top_censurada.jpg)

- Health checks de API correctos.
![API health status OK](docs/media/health-status-ok_censurada.jpg)

### 6. Deploy frontend last
Ejecuta `azure-pipelines-frontend.yml` despues de confirmar backend sano.

Evidencia del paso:
- Pipeline frontend (vista general).
![Frontend pipeline overview](docs/media/general-front-deploy-pipeline_censurada.jpg)

- Pipeline frontend (detalle de job).
![Frontend deploy details](docs/media/details-front-deploy-pipeline_censurada.jpg)

- Pantalla de login independiente (acceso obligatorio antes del portal).
![Frontend login page](docs/media/login-page.jpg)

- Portal autenticado con nueva distribucion (registro, salud, estado de riesgo y secciones operativas).
![Predictive simulator portal (authenticated view)](docs/media/predictive-simulator-ui-no-data_censurada-1.jpg)

- Vista complementaria del portal con foco en prediccion manual y controles admin.
![Predictive simulator portal (manual prediction and admin area)](docs/media/predictive-simulator-ui-no-data_censurada-2.jpg)

### 7. Frontend functional validation
Validacion recomendada en este orden. Cada captura confirma un bloque funcional concreto.

1. Health endpoints desde UI (`/health/live` y `/health/ready`).
Resultado esperado: estado `ok/ready` en la salida JSON.
![Check liveness and readiness](docs/media/check-liveness.jpg)

2. Estado de integraciones (`/models/integrations/status`).
Resultado esperado: respuesta del estado de conectores y modo de ejecucion.
![Check integrations](docs/media/check-integrations.jpg)

3. Panel de riesgo en vivo (probabilidad, nivel de riesgo y recomendacion).
Resultado esperado: refresco periodico y barras de sensores actualizadas.
![Live risk state panel](docs/media/live-risk-state.jpg)

4. Prediccion manual con respuesta JSON de backend.
Resultado esperado: `prediction_id`, `risk_level` y `failure_probability` presentes.
![Manual prediction result](docs/media/predict-failure-risk.jpg)

5. Controles admin para simulacion y ajuste de umbrales.
Resultado esperado: cambio de estado de simulacion y actualizacion de thresholds.
![Admin controls panel](docs/media/admin-controls.jpg)

### 8. Observe full CI/CD flow
Vista conjunta de ejecuciones en Azure DevOps:

![Pipelines running](docs/media/pipelines-running_censurada.jpg)

## Quick validation commands
```bash
kubectl get pods -n energypredict-dev
kubectl get pods -n energypredict-prod
kubectl get ingress -n energypredict-prod
kubectl rollout status deploy/energypredict-api-prod -n energypredict-prod
```

For the full HTTPS operational guide (AKS ingress, cert-manager, ACME challenge troubleshooting, NSG/LB checks and frontend HTTPS wiring), see:
- `docs/16_HTTPS_INGRESS_CERT_MANAGER_RUNBOOK.md`

## API key endpoints
- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/predict`
- `POST /api/v1/models/train`

## Cleanup and cost control
Para apagar todo el laboratorio:
```powershell
.\scripts\destroy_all.ps1
```

## Additional documentation
- `docs/02_ARCHITECTURE.md`
- `docs/05_SECURITY_AUTH_ENCRYPTION.md`
- `docs/06_MLOPS_DATABRICKS_MLFLOW.md`
- `docs/07_AKS_PRODUCTION_CICD.md`
- `docs/09_FRONTEND_STATIC_SIMULATOR.md`
- `docs/14_SECURITY_HARDENING_PLAN.md`
- `docs/15_AKS_WORKLOAD_IDENTITY_KEYVAULT_CSI.md`
- `docs/16_HTTPS_INGRESS_CERT_MANAGER_RUNBOOK.md`
- `docs/17_STREAMING_PREDICTIONS_LLM_DATABRICKS_IMPLEMENTATION_PLAN.md`
- `docs/18_STREAMING_EVENTHUB_DATABRICKS_RUNBOOK.md`
- `docs/19_ARCHITECTURE_DECISIONS.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`

## Full operational runbook (integrated)
Esta seccion integra en el README todo el runbook operativo para ejecutar, validar y mantener el proyecto end-to-end en Azure DevOps.

### Pipeline architecture
1. `azure-pipelines-infra.yml`
- Provisiona infraestructura con Terraform.
- Stages: plan/apply de `dev` y plan/apply de `prod` (prod solo en branch `main`).

2. `azure-pipelines-app.yml`
- CI/CD backend FastAPI en AKS.
- CI: lint, tests, build imagen, push ACR (no en PR).
- CD: deploy `dev` desde branch `dev`, deploy `prod` desde branch `main`.

3. `azure-pipelines-frontend.yml`
- CI/CD del portal estatico (`frontend/simulator-portal`).
- Deploy a Azure Static Web App con HTTPS.

### Ordered execution
Orden operativo recomendado:
1. `azure-pipelines-infra.yml`
2. `azure-pipelines-app.yml`
3. `azure-pipelines-frontend.yml`

Importante:
- Aunque `app` y `frontend` tengan trigger por commit en `dev/main`, Azure DevOps no garantiza ejecucion secuencial estricta entre pipelines distintos.
- El pipeline de frontend valida que el backend en AKS este `available` antes de publicar.

### Expected Azure resources
Provisionados por `infra/terraform/modules/platform`:

1. Core
- Resource Group
- Log Analytics
- ACR
- AKS
- Key Vault

2. Data/ML
- Databricks (opcional)
- PostgreSQL Flexible Server (opcional)

3. Frontend
- Azure Static Web App (opcional)

### Pre-flight checklist
Herramientas:
- `terraform`
- `az`
- `kubectl`

Validaciones locales:
```powershell
python -m ruff check app tests
python -m pytest -q

cd infra/terraform/envs/dev
terraform validate
terraform plan -out tfplan

cd ../prod
terraform validate
terraform plan -out tfplan

cd ../../devops
terraform validate
terraform plan -out tfplan
```

### Terraform variable files
- `infra/terraform/envs/dev/terraform.tfvars`
- `infra/terraform/envs/prod/terraform.tfvars`
- `infra/terraform/devops/terraform.tfvars`
- Plantillas publicables:
- `infra/terraform/envs/dev/terraform.tfvars.example`
- `infra/terraform/envs/prod/terraform.tfvars.example`
- `infra/terraform/devops/terraform.tfvars.example`

### Azure DevOps preparation
Service connection:
1. Manual en Azure DevOps y referenciar su nombre en `AZURE_SERVICE_CONNECTION`.
2. Crear por Terraform en `infra/terraform/devops` con `create_azure_service_connection=true`.

Variable Group `energypredict-shared` minimo:

Backend:
- `ACR_NAME`
- `AKS_DEV_RESOURCE_GROUP`
- `AKS_DEV_CLUSTER_NAME`
- `AKS_PROD_RESOURCE_GROUP`
- `AKS_PROD_CLUSTER_NAME`
- `AKS_WORKLOAD_IDENTITY_CLIENT_ID_DEV`
- `AKS_WORKLOAD_IDENTITY_CLIENT_ID_PROD`
- `KEY_VAULT_NAME_DEV`
- `KEY_VAULT_NAME_PROD`
- `AZURE_TENANT_ID`
- `CORS_ALLOWED_ORIGINS_DEV`
- `CORS_ALLOWED_ORIGINS_PROD`

Frontend:
- `STATIC_WEB_APP_DEV_NAME`
- `STATIC_WEB_APP_DEV_RESOURCE_GROUP`
- `STATIC_WEB_APP_PROD_NAME`
- `STATIC_WEB_APP_PROD_RESOURCE_GROUP`
- `FRONTEND_DEV_API_BASE_URL`
- `FRONTEND_PROD_API_BASE_URL`
- `FRONTEND_API_SCHEME_DEV` (recomendado: `https`)
- `FRONTEND_API_SCHEME_PROD` (recomendado: `https`)
- `LETSENCRYPT_EMAIL`

Streaming + LLM:
- `STREAM_INGESTION_ENABLED_DEV`
- `STREAM_INGESTION_ENABLED_PROD`
- `PREDICTION_LOOP_INTERVAL_SECONDS`
- `EVENTHUB_NAMESPACE_NAME_DEV`
- `EVENTHUB_NAMESPACE_NAME_PROD`
- `EVENTHUB_NAME_DEV`
- `EVENTHUB_NAME_PROD`
- `EVENTHUB_CONSUMER_GROUP`
- `LLM_PROVIDER`
- `LLM_MODEL`
- `LLM_ENDPOINT`
- `LLM_API_KEY` (secret)

Groq recommended values:
- `LLM_PROVIDER=groq`
- `LLM_MODEL=llama-3.1-70b-versatile`
- `LLM_ENDPOINT=https://api.groq.com/openai/v1/chat/completions`

Terraform remote state:
- `TF_STATE_RESOURCE_GROUP`
- `TF_STATE_LOCATION`
- `TF_STATE_STORAGE_ACCOUNT`
- `TF_STATE_CONTAINER`
- `TF_STATE_KEY_DEV`
- `TF_STATE_KEY_PROD`

Terraform tfvars via Library (opcional):
- `TFVARS_DEV_B64`
- `TFVARS_PROD_B64`

Generacion automatica:
```powershell
.\scripts\generate_tfvars_b64.ps1
```

Pasos en Azure DevOps:
1. Ir a `Pipelines > Library > Variable groups > energypredict-shared`.
2. Crear/actualizar:
- `TFVARS_DEV_B64` (secret).
- `TFVARS_PROD_B64` (secret).
3. Guardar y relanzar `azure-pipelines-infra.yml`.

### Variable Group as code (recommended)
```powershell
cd infra/terraform/devops
terraform init
terraform plan -out tfplan
terraform apply tfplan
```

El pipeline de infraestructura:
1. Crea/verifica backend remoto en Azure Storage.
2. Ejecuta `terraform init -reconfigure` con backend `azurerm`.
3. Si existen `TFVARS_*_B64`, reconstruye `terraform.tfvars` en el agente.

### Recommended Azure DevOps environments
- `energypredict-dev-infra`
- `energypredict-prod-infra`
- `energypredict-dev`
- `energypredict-prod`
- `energypredict-frontend-dev`
- `energypredict-frontend-prod`

### Terraform apply by environment
Dev:
```powershell
cd infra/terraform/envs/dev
terraform init
terraform validate
terraform plan -out tfplan
terraform apply tfplan
```

Prod:
```powershell
cd infra/terraform/envs/prod
terraform init
terraform validate
terraform plan -out tfplan
terraform apply tfplan
```

Outputs utiles:
```powershell
cd infra/terraform/envs/dev
terraform output identity_client_id
terraform output tenant_id
terraform output static_web_app_default_host_name

cd ../prod
terraform output identity_client_id
terraform output static_web_app_default_host_name
```

Variables nuevas de plataforma:
- `enable_static_web_app`
- `static_web_app_name`
- `static_web_app_sku_tier`
- `static_web_app_sku_size`
- `enable_workload_identity`
- `enable_key_vault_csi`
- `kubernetes_namespace`
- `workload_identity_service_account_name`

### Key Vault behavior in dev/prod
Configuracion recomendada:
- `dev`: `key_vault_purge_protection_enabled = false`
- `prod`: `key_vault_purge_protection_enabled = true`

Nota:
- Azure Key Vault mantiene soft-delete obligatorio.
- Si purge protection esta activa, Azure puede impedir purge inmediato.

### Common IaC blockers and fixes
1. Pipeline still uses old Key Vault name:
- Regenerar `TFVARS_DEV_B64` o `TFVARS_PROD_B64`.
- Actualizar `KEY_VAULT_NAME_DEV`/`KEY_VAULT_NAME_PROD` en Library.

2. `roleAssignments/write` forbidden:
- El Service Principal necesita permisos para asignar roles.
- Recomendado en practica: `Owner`.
- Alternativa: `Contributor` + `User Access Administrator`.

3. Access policy already exists but not in state:
- El pipeline de infra intenta auto-import de `module.platform.azurerm_key_vault_access_policy.terraform_operator` antes del apply.

Comando orientativo de permisos:
```powershell
az role assignment create `
  --assignee-object-id "<service-principal-object-id>" `
  --assignee-principal-type ServicePrincipal `
  --role "User Access Administrator" `
  --scope "/subscriptions/<subscription-id>"
```

### Backend deployment details
Pipeline: `azure-pipelines-app.yml`

CI:
- Instala dependencias.
- Ejecuta `ruff` y `pytest`.
- Ejecuta `docker build` y publica imagen versionada en ACR.

CD dev/prod:
- Reutiliza imagen de CI (sin rebuild).
- Sustituye placeholders de Workload Identity/Key Vault.
- `kubectl apply -k k8s/overlays/<env>`.
- Ejecuta `scripts/prepare_public_api_endpoint.sh <env>`.
- `kubectl set image` por SHA.
- `kubectl set env` para CORS.
- `kubectl rollout status`.

Endpoint online generado:
- Dev: `http://api-dev.<public-ip-dashed>.nip.io/api/v1`
- Prod: `https://api.<public-ip-dashed>.nip.io/api/v1`

### Frontend deployment details
Pipeline: `azure-pipelines-frontend.yml`

1. Valida archivos del portal.
2. Genera `config.js` desde `config.template.js`.
3. Obtiene token SWA con `az staticwebapp secrets list`.
4. Publica con `AzureStaticWebApp@0`.

Nota:
- SWA se sirve en HTTPS.
- Si API queda en HTTP, puede haber mixed-content en navegador.

### Operational validation commands
AKS:
```bash
az aks get-credentials -g <RG> -n <AKS_NAME> --overwrite-existing
kubectl get nodes
kubectl get ns
kubectl get pods -A
kubectl get pods -n energypredict-dev
kubectl get pods -n energypredict-prod
```

Deployment / rollout:
```bash
kubectl -n energypredict-prod get deploy,rs,pods
kubectl -n energypredict-prod rollout status deploy/energypredict-api-prod
kubectl -n energypredict-prod rollout history deploy/energypredict-api-prod
```

Service / ingress / DNS:
```bash
kubectl -n energypredict-prod get svc,ingress
kubectl -n energypredict-prod describe ingress energypredict-api-prod
nslookup <host-del-ingress>
```

Health checks:
```bash
kubectl port-forward svc/energypredict-api-dev 8080:80 -n energypredict-dev
curl http://localhost:8080/api/v1/health/live
curl http://localhost:8080/api/v1/health/ready

kubectl port-forward svc/energypredict-api-prod 8081:80 -n energypredict-prod
curl http://localhost:8081/api/v1/health/live
curl http://localhost:8081/api/v1/health/ready
```

HPA and metrics:
```bash
kubectl -n energypredict-prod get hpa
kubectl top nodes
kubectl -n energypredict-prod top pods
```

Troubleshooting:
```bash
kubectl -n energypredict-prod get events --sort-by=.metadata.creationTimestamp | tail -n 40
kubectl -n energypredict-prod describe deploy energypredict-api-prod
kubectl -n energypredict-prod describe pod <pod-name>
kubectl -n energypredict-prod logs <pod-name> --tail=200
kubectl -n energypredict-prod logs <pod-name> --previous --tail=200
```

CSI + Workload Identity (dev):
```bash
kubectl apply -k k8s/overlays/dev
kubectl get sa -n energypredict-dev
kubectl get secretproviderclass -n energypredict-dev
kubectl get pods -n energypredict-dev
kubectl get secret energypredict-secrets -n energypredict-dev
kubectl describe pod -n energypredict-dev <pod-name>
```

CSI + Workload Identity (prod):
```bash
kubectl get sa -n energypredict-prod
kubectl get secretproviderclass -n energypredict-prod
kubectl get secret energypredict-secrets -n energypredict-prod
kubectl describe pod -n energypredict-prod <pod-name>
```

CI/CD validation in Azure DevOps:
1. `azure-pipelines-infra.yml` en verde.
2. `azure-pipelines-app.yml` en verde.
3. `azure-pipelines-frontend.yml` en verde.

### Frontend functional checks
1. Abrir URL HTTPS de SWA.
2. Registrar usuario (`Create User`).
3. Iniciar sesion.
4. Ejecutar prediccion y revisar respuesta JSON.

Registro desde UI:
1. Completar `Create User` (email, password, role).
2. Pulsar `Create user`.
3. Verificar mensaje de exito.
4. Hacer login con ese usuario.

Validacion API equivalente:
```bash
curl -X POST "<API_BASE_URL>/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"demo.user@energypredict.local","password":"DemoPass!123","role":"operator"}'
```

Conectividad online SWA -> API:
1. Abrir DevTools (`Network`) y verificar peticiones a `<API_BASE_URL>`.
2. Confirmar ausencia de errores CORS/mixed content.
3. Si SWA (HTTPS) llama a API HTTP, el navegador puede bloquear la llamada.
4. Solucion profesional: API con HTTPS valido en Ingress.

### HTTP traceability check
La API registra por request:
- `trace_id`
- `method`
- `route`
- `status`
- `latency_ms`
- `user`
- `role`

Comprobacion:
```bash
kubectl logs -n energypredict-dev deploy/energypredict-api-dev --tail=200
curl -H "X-Trace-Id: demo-trace-001" http://localhost:8080/api/v1/health/live
```

### Rollback commands
```bash
kubectl rollout history deployment/energypredict-api-dev -n energypredict-dev
kubectl rollout undo deployment/energypredict-api-dev -n energypredict-dev
kubectl rollout status deployment/energypredict-api-dev -n energypredict-dev

kubectl rollout history deployment/energypredict-api-prod -n energypredict-prod
kubectl rollout undo deployment/energypredict-api-prod -n energypredict-prod
kubectl rollout status deployment/energypredict-api-prod -n energypredict-prod
```

### Cleanup and cost control
Script unificado:
```powershell
.\scripts\destroy_all.ps1
```

Comportamiento:
- Intenta `terraform destroy` en `prod` y `dev` usando backend remoto.
- Limpia y purga secretos conocidos de Key Vault (best-effort).
- Si falla destroy, elimina RGs explicitos del proyecto.
- Borra tambien RG de tfstate por defecto.

RGs objetivo:
- `rg-energypredict-prod`
- `rg-energypredict-dev`
- `rg-energypredict-tfstate`

Opciones:
```powershell
.\scripts\destroy_all.ps1 -IncludeDevOps
.\scripts\destroy_all.ps1 -DeleteNetworkWatcherRG
```

Si backend remoto usa otros nombres:
```powershell
.\scripts\destroy_all.ps1 `
  -TfStateResourceGroup "<rg-tfstate>" `
  -TfStateStorageAccount "<storage-account-tfstate>" `
  -TfStateContainer "<container-tfstate>" `
  -TfStateKeyDev "<dev-key>" `
  -TfStateKeyProd "<prod-key>"
```

Opciones adicionales:
```powershell
.\scripts\destroy_all.ps1 -EmergencyDeleteResourceGroups
.\scripts\destroy_all.ps1 -IncludeDevOps
```

Limitaciones y notas:
- Si Key Vault tiene purge protection activa, Azure puede impedir purge inmediato.
- Azure mantiene soft-delete obligatorio.
- En laboratorio, si un vault queda bloqueado, rotar nombre (`...-01` -> `...-02`) y regenerar `TFVARS_*_B64`.
- Si ejecutas desde la raiz del repo usa `.\scripts\destroy_all.ps1`; si estas dentro de `scripts`, usa `.\destroy_all.ps1`.

### Apply strategy (from most conservative to least)
1. Opcion A: mantener region de `prod` y pedir cuota vCPU.
2. Opcion B: mantener region y reducir temporalmente `node_vm_size`/`node_count`.
3. Opcion C: mover solo `prod` a region con cuota.
4. Opcion D: destruir temporalmente `dev`, aplicar `prod`, recrear `dev`.

Comandos utiles:
```bash
az vm list-usage -l westeurope -o table
az aks get-versions -l westeurope -o table
```

### Security baseline
1. Key Vault
- Secretos runtime en Key Vault.
- En Key Vault, nombres con `-` (no `_`).
- En AKS, consumo via Key Vault CSI + Workload Identity.

2. Git hygiene
- Fuera de git: `terraform.tfvars`, `*.tfstate`, `.terraform/`, `tfplan`, `.env`, `*.db`.

3. Operacion
- Rotar secretos usados en pruebas.
- No copiar secretos reales a `.example` ni docs publicas.

### Final release checklist
1. IaC:
- Terraform modular por entorno con core + data + frontend.
2. CI/CD:
- Pipelines separados para infra, backend y frontend.
3. Kubernetes:
- Overlays dev/prod + rolling updates + probes.
4. Seguridad:
- Key Vault CSI + Workload Identity sin secretos en git.
5. Observabilidad:
- Trazabilidad request-level con `trace_id` y latencia.





