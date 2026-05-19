# RUNBOOK E2E - Azure DevOps (Infra + API + Frontend)

Este runbook describe el flujo completo para operar EnergyPredict en Azure con separacion por entornos, AKS y portal HTTPS.

## 1. Arquitectura de pipelines

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

## 2. Recursos Azure esperados

Provisionados por Terraform (modulo `infra/terraform/modules/platform`):

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

## 3. Pre-flight antes de `apply`

## 3.1 Herramientas
- `terraform`
- `az`
- `kubectl`
- Acceso al proyecto Azure DevOps

## 3.2 Validaciones locales recomendadas
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

## 3.3 Archivos de variables por stack
- `infra/terraform/envs/dev/terraform.tfvars`
- `infra/terraform/envs/prod/terraform.tfvars`
- `infra/terraform/devops/terraform.tfvars`
- Plantillas publicables (sin secretos):
- `infra/terraform/envs/dev/terraform.tfvars.example`
- `infra/terraform/envs/prod/terraform.tfvars.example`
- `infra/terraform/devops/terraform.tfvars.example`

Cada stack usa su propio `terraform.tfvars` segun el directorio donde ejecutes Terraform.

## 4. Preparacion en Azure DevOps

## 4.1 Service Connection
Opciones:
1. Manual en Azure DevOps y referenciar su nombre en `AZURE_SERVICE_CONNECTION`.
2. Crear por Terraform en `infra/terraform/devops` con `create_azure_service_connection=true`.

## 4.2 Variable Group `energypredict-shared`

Variables minimas:

1. Backend
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

2. Frontend
- `STATIC_WEB_APP_DEV_NAME`
- `STATIC_WEB_APP_DEV_RESOURCE_GROUP`
- `STATIC_WEB_APP_PROD_NAME`
- `STATIC_WEB_APP_PROD_RESOURCE_GROUP`
- `FRONTEND_DEV_API_BASE_URL`
- `FRONTEND_PROD_API_BASE_URL`

## 4.3 Environments recomendados
- `energypredict-dev-infra`
- `energypredict-prod-infra`
- `energypredict-dev`
- `energypredict-prod`
- `energypredict-frontend-dev`
- `energypredict-frontend-prod`

## 4.4 Variable Group como codigo (recomendado)
```powershell
cd infra/terraform/devops
terraform init
terraform plan -out tfplan
terraform apply tfplan
```

## 5. Terraform por entorno

## 5.1 Dev
```powershell
cd infra/terraform/envs/dev
terraform init
terraform validate
terraform plan -out tfplan
terraform apply tfplan
```

## 5.2 Prod
```powershell
cd infra/terraform/envs/prod
terraform init
terraform validate
terraform plan -out tfplan
terraform apply tfplan
```

## 5.3 Variables nuevas de plataforma
- `enable_static_web_app`
- `static_web_app_name`
- `static_web_app_sku_tier`
- `static_web_app_sku_size`
- `enable_workload_identity`
- `enable_key_vault_csi`
- `kubernetes_namespace`
- `workload_identity_service_account_name`

## 5.4 Outputs utiles para completar DevOps
```powershell
cd infra/terraform/envs/dev
terraform output identity_client_id
terraform output tenant_id
terraform output static_web_app_default_host_name

cd ../prod
terraform output identity_client_id
terraform output static_web_app_default_host_name
```

Campos tipicos a actualizar en `infra/terraform/devops/terraform.tfvars` despues del primer deploy:
- `AKS_WORKLOAD_IDENTITY_CLIENT_ID_DEV`
- `AKS_WORKLOAD_IDENTITY_CLIENT_ID_PROD`
- `CORS_ALLOWED_ORIGINS_DEV`
- `CORS_ALLOWED_ORIGINS_PROD`
- `FRONTEND_DEV_API_BASE_URL`
- `FRONTEND_PROD_API_BASE_URL`

## 5.5 Limpieza completa (destroy)

Destroy Dev:
```powershell
cd infra/terraform/envs/dev
terraform destroy
```

Destroy Prod:
```powershell
cd infra/terraform/envs/prod
terraform destroy
```

Sin confirmacion interactiva:
```powershell
terraform destroy -auto-approve
```

## 5.6 Estrategia de apply en orden (de mas conservadora a menos conservadora)

1. Opcion A (mas conservadora): mantener `prod` en la misma region y pedir cuota
- No cambia arquitectura ni nombres.
- Requiere subida de cuota vCPU en Azure para la region de `prod`.
- Comandos utiles:
```bash
az vm list-usage -l westeurope -o table
az aks get-versions -l westeurope -o table
```

2. Opcion B: mantener region, bajar tamano temporal de AKS `prod`
- Reducir en `infra/terraform/envs/prod/terraform.tfvars`:
- `node_count = 1`
- `node_vm_size` a un SKU permitido por tu suscripcion.
- Reintentar `plan/apply`.

3. Opcion C: mover solo `prod` a una region con cuota disponible
- Cambiar `location` en `infra/terraform/envs/prod/terraform.tfvars`.
- Recomendada cuando la cuota en region actual es 0.
- Requiere recreacion parcial o total de recursos de `prod`.

4. Opcion D (menos conservadora): liberar cuota destruyendo temporalmente `dev`
- Ejecutar `terraform destroy` en `envs/dev`.
- Aplicar `prod`.
- Volver a crear `dev`.
- Es valida para demo/practica, no ideal para operacion continua.

## 6. Despliegue backend en AKS

Pipeline: `azure-pipelines-app.yml`

1. CI
- Instala dependencias.
- Ejecuta lint (`ruff`) y tests (`pytest`).
- Ejecuta `docker build` y publica una imagen versionada en ACR.

2. CD dev/prod
- Reutiliza la misma imagen de CI (sin rebuild).
- Sustituye placeholders de Workload Identity/Key Vault en overlays.
- `kubectl apply -k k8s/overlays/<env>`.
- `kubectl set image` por SHA (`Build.SourceVersion`).
- `kubectl set env` para `CORS_ALLOWED_ORIGINS`.
- `kubectl rollout status`.

## 7. Despliegue frontend HTTPS

Pipeline: `azure-pipelines-frontend.yml`

1. Valida archivos del portal.
2. Genera `config.js` desde `config.template.js` con URL API por entorno.
3. Obtiene token SWA con `az staticwebapp secrets list`.
4. Publica contenido estatico con `AzureStaticWebApp@0`.

## 8. Validacion operativa

## 8.1 AKS
```bash
az aks get-credentials -g <RG> -n <AKS_NAME> --overwrite-existing
kubectl get ns
kubectl get pods -n energypredict-dev
kubectl get pods -n energypredict-prod
```

## 8.2 Health API
```bash
kubectl port-forward svc/energypredict-api-dev 8080:80 -n energypredict-dev
curl http://localhost:8080/api/v1/health/live
curl http://localhost:8080/api/v1/health/ready
```

## 8.3 Portal frontend
- Abrir URL HTTPS de SWA.
- Confirmar login.
- Ejecutar prediccion desde UI.
- Revisar salida JSON.

## 8.4 CSI + Workload Identity (dev)
```bash
kubectl apply -k k8s/overlays/dev
kubectl get sa -n energypredict-dev
kubectl get secretproviderclass -n energypredict-dev
kubectl get pods -n energypredict-dev
kubectl get secret energypredict-secrets -n energypredict-dev
kubectl describe pod -n energypredict-dev <pod-name>
```

## 8.5 CI/CD en Azure DevOps
1. Verificar estado exitoso de:
- `azure-pipelines-infra.yml`
- `azure-pipelines-app.yml`
- `azure-pipelines-frontend.yml`

2. Verificar imagen desplegada:
```bash
kubectl get deploy energypredict-api-dev -n energypredict-dev -o jsonpath="{.spec.template.spec.containers[0].image}"
```

3. Verificar CORS inyectado:
```bash
kubectl get deploy energypredict-api-dev -n energypredict-dev -o jsonpath="{.spec.template.spec.containers[0].env}"
```

## 8.6 Trazabilidad HTTP (middleware)
La API incluye middleware de trazabilidad por request. Loguea:
- `trace_id`
- `method`
- `route`
- `status`
- `latency_ms`
- `user`
- `role`

Validacion rapida:
```bash
kubectl logs -n energypredict-dev deploy/energypredict-api-dev --tail=200
```

Prueba con trace id explicito:
```bash
curl -H "X-Trace-Id: demo-trace-001" http://localhost:8080/api/v1/health/live
```

Debes ver `X-Trace-Id` en respuesta y el mismo `trace_id` en logs.

## 8.7 Rollback
```bash
kubectl rollout history deployment/energypredict-api-dev -n energypredict-dev
kubectl rollout undo deployment/energypredict-api-dev -n energypredict-dev
kubectl rollout status deployment/energypredict-api-dev -n energypredict-dev
```

## 9. Seguridad y secretos

1. Key Vault
- Secretos runtime en Key Vault.
- En Key Vault, nombres con `-` (no `_`).
- En AKS, consumo via Key Vault CSI + Workload Identity.

2. Git hygiene
- Fuera de git: `terraform.tfvars`, `*.tfstate`, `.terraform/`, `tfplan`, `.env`, `*.db`.

3. Operacion
- Si usas secretos hardcodeados localmente para practica, rotarlos al terminar.
- No copiar secretos reales a `.example` ni documentacion publica.

## 10. Checklist final de release tecnica

1. IaC
- Terraform modular por entorno con recursos core + data + frontend.

2. CI/CD
- Pipelines separados para infra, backend y frontend.

3. Kubernetes
- Overlays dev/prod + rolling update + health probes.

4. Seguridad
- Key Vault CSI + Workload Identity, sin `secret.yaml` con secretos reales.

5. Observabilidad
- Logs de trazabilidad request-level con `trace_id` y latencia.

## 11. Referencias
- `docs/14_SECURITY_HARDENING_PLAN.md`
- `docs/15_AKS_WORKLOAD_IDENTITY_KEYVAULT_CSI.md`
- `security-checklist.md`
