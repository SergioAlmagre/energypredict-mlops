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

## 1.1 Orden recomendado entre pipelines
Orden operativo recomendado:
1. `azure-pipelines-infra.yml`
2. `azure-pipelines-app.yml`
3. `azure-pipelines-frontend.yml`

Importante:
- Aunque `app` y `frontend` tengan trigger por commit en `dev/main`, Azure DevOps no garantiza ejecucion secuencial estricta entre pipelines distintos.
- Para reducir errores de orden, el pipeline de frontend valida que el deployment backend en AKS este `available` antes de publicar.
- Si no esta listo, frontend falla con mensaje explicito: ejecutar primero pipeline `app`.

Practica recomendada para entrevistas/demos:
1. Ejecutar `infra`.
2. Ejecutar `app` y verificar rollout.
3. Ejecutar `frontend`.

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

3. Terraform remote state (recomendado)
- `TF_STATE_RESOURCE_GROUP`
- `TF_STATE_LOCATION`
- `TF_STATE_STORAGE_ACCOUNT`
- `TF_STATE_CONTAINER`
- `TF_STATE_KEY_DEV`
- `TF_STATE_KEY_PROD`

4. Terraform tfvars via Library (opcional, secretos base64)
- `TFVARS_DEV_B64`
- `TFVARS_PROD_B64`

Generacion automatica de esos valores:
```powershell
.\scripts\generate_tfvars_b64.ps1
```

Pasos en Azure DevOps:
1. Ir a `Pipelines > Library > Variable groups > energypredict-shared`.
2. Crear/actualizar:
- `TFVARS_DEV_B64` (marcar como secret).
- `TFVARS_PROD_B64` (marcar como secret).
3. Guardar y relanzar pipeline `azure-pipelines-infra.yml`.

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

El pipeline de infraestructura:
1. Crea/verifica el backend remoto en Azure Storage (state bootstrap).
2. Ejecuta `terraform init -reconfigure` con backend `azurerm`.
3. Si existen `TFVARS_DEV_B64`/`TFVARS_PROD_B64`, reconstruye `terraform.tfvars` en el agente.

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

Script unificado (recomendado para apagar al final del dia):
```powershell
.\scripts\destroy_all.ps1
```

Comportamiento por defecto:
- Intenta `terraform destroy` en `prod` y `dev` usando backend remoto.
- Intenta borrar y purgar secretos conocidos de Key Vault (`DATABASE-URL`, `JWT-SECRET-KEY`, `FERNET-KEY`, Snowflake y Databricks).
- Si algun destroy falla, ejecuta automaticamente borrado de Resource Groups (`az group delete`) para evitar coste residual.
- Borra tambien el Resource Group de `tfstate` (wipe total).
- Solo borra Resource Groups explicitos del proyecto: `rg-energypredict-prod`, `rg-energypredict-dev` y `rg-energypredict-tfstate`.
- No borra otros recursos de la suscripcion.
- `NetworkWatcherRG` solo se borra si se usa `-DeleteNetworkWatcherRG`.

Limitacion importante:
- Si Key Vault tiene purge protection activa, Azure puede impedir el purge inmediato aunque el script lo solicite.
- En ese caso el recurso queda protegido hasta que venza la retencion configurada por Azure.

Configuracion recomendada:
- `dev`: `key_vault_purge_protection_enabled = false`
- `prod`: `key_vault_purge_protection_enabled = true`

Nota:
- Azure Key Vault mantiene soft-delete obligatorio; no se puede desactivar por completo.
- Con purge protection desactivada, el script puede purgar secretos/vaults cuando los permisos lo permitan.

Workaround de laboratorio:
- Si un Key Vault de dev anterior queda bloqueado por purge protection, cambiar `key_vault_name` en `infra/terraform/envs/dev/terraform.tfvars`.
- Ejemplo: `kv-energypredict-dev-01` -> `kv-energypredict-dev-02`.
- Despues regenerar `TFVARS_DEV_B64` con `.\scripts\generate_tfvars_b64.ps1` y actualizar el Variable Group `energypredict-shared`.
- Si ocurre lo mismo en prod durante la practica, aplicar la misma idea: `kv-energypredict-prod-01` -> `kv-energypredict-prod-02`.
- Despues regenerar `TFVARS_PROD_B64` y actualizar `KEY_VAULT_NAME_PROD` en Library.

Error comun:
- Si el pipeline sigue mostrando `kv-energypredict-dev-01`, Azure DevOps esta usando un `TFVARS_DEV_B64` antiguo.
- Regenerar `TFVARS_DEV_B64` y actualizar tambien `KEY_VAULT_NAME_DEV` en Library.

Permisos necesarios del Service Principal:
- Para crear `azurerm_role_assignment`, la Service Connection necesita permisos de asignacion de roles.
- En una suscripcion de practica, usar `Owner`.
- Alternativa mas limitada: `Contributor` + `User Access Administrator`.

Comando orientativo:
```powershell
az role assignment create `
  --assignee-object-id "<service-principal-object-id>" `
  --assignee-principal-type ServicePrincipal `
  --role "User Access Administrator" `
  --scope "/subscriptions/<subscription-id>"
```

Nota de ejecucion:
- Si estas en la raiz del repo: `.\scripts\destroy_all.ps1`
- Si ya estas dentro de la carpeta `scripts`: `.\destroy_all.ps1`

Si tu backend remoto usa nombres distintos:
```powershell
.\scripts\destroy_all.ps1 `
  -TfStateResourceGroup "<rg-tfstate>" `
  -TfStateStorageAccount "<storage-account-tfstate>" `
  -TfStateContainer "<container-tfstate>" `
  -TfStateKeyDev "<dev-key>" `
  -TfStateKeyProd "<prod-key>"
```

Incluir tambien stack DevOps:
```powershell
.\scripts\destroy_all.ps1 -IncludeDevOps
```

Modo emergencia (ademas borra RGs por `az group delete`):
```powershell
.\scripts\destroy_all.ps1 -EmergencyDeleteResourceGroups
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
- Ejecuta `scripts/prepare_public_api_endpoint.sh <env>` para:
- instalar/asegurar ingress-nginx con LoadBalancer,
- obtener IP publica del controlador,
- configurar host publico dinamico (`nip.io`) en el Ingress.
- `kubectl set image` por SHA (`Build.SourceVersion`).
- `kubectl set env` para `CORS_ALLOWED_ORIGINS`.
- `kubectl rollout status`.

3. Endpoint online generado automaticamente
- Dev: `http://api-dev.<public-ip-dashed>.nip.io/api/v1`
- Prod: `http://api.<public-ip-dashed>.nip.io/api/v1`
- El pipeline imprime la URL final como `Public API endpoint`.

## 7. Despliegue frontend HTTPS

Pipeline: `azure-pipelines-frontend.yml`

1. Valida archivos del portal.
2. Genera `config.js` desde `config.template.js` con URL API por entorno.
- Si existe Ingress en AKS, el pipeline toma host real desde cluster y construye URL automaticamente.
3. Obtiene token SWA con `az staticwebapp secrets list`.
4. Publica contenido estatico con `AzureStaticWebApp@0`.

Nota de navegador:
- SWA se sirve por HTTPS.
- Si `FRONTEND_API_SCHEME_*` es `http`, el navegador puede bloquear llamadas por mixed content.
- Para uso plenamente online desde SWA, configurar HTTPS tambien en API (TLS del Ingress + certificado valido).

## 8. Validacion operativa

## 8.1 AKS
```bash
az aks get-credentials -g <RG> -n <AKS_NAME> --overwrite-existing
kubectl get nodes
kubectl get ns
kubectl get pods
kubectl get pods -n energypredict-dev
kubectl get pods -n energypredict-prod
kubectl get pods -A
```

Nota:
- `kubectl get pods` sin `-n` consulta `default`.
- La app esta desplegada en `energypredict-dev` o `energypredict-prod`.

## 8.2 Estado de deployment, replicas y rollout
```bash
kubectl -n energypredict-prod get deploy,rs,pods
kubectl -n energypredict-prod rollout status deploy/energypredict-api-prod
kubectl -n energypredict-prod rollout history deploy/energypredict-api-prod
```

## 8.3 Service, Ingress y DNS
```bash
kubectl -n energypredict-prod get svc,ingress
kubectl -n energypredict-prod describe ingress energypredict-api-prod
nslookup <host-del-ingress>
```

## 8.4 Health API
```bash
kubectl port-forward svc/energypredict-api-dev 8080:80 -n energypredict-dev
curl http://localhost:8080/api/v1/health/live
curl http://localhost:8080/api/v1/health/ready

kubectl port-forward svc/energypredict-api-prod 8081:80 -n energypredict-prod
curl http://localhost:8081/api/v1/health/live
curl http://localhost:8081/api/v1/health/ready
```

## 8.5 HPA y capacidad de cluster
```bash
kubectl -n energypredict-prod get hpa
kubectl top nodes
kubectl -n energypredict-prod top pods
```

## 8.6 Eventos y diagnostico rapido de fallos
```bash
kubectl -n energypredict-prod get events --sort-by=.metadata.creationTimestamp | tail -n 40
kubectl -n energypredict-prod describe deploy energypredict-api-prod
kubectl -n energypredict-prod describe pod <pod-name>
kubectl -n energypredict-prod logs <pod-name> --tail=200
kubectl -n energypredict-prod logs <pod-name> --previous --tail=200
```

Checks de error comunes:
```bash
kubectl -n energypredict-prod get pods
kubectl -n energypredict-prod describe pod <pod-name> | grep -E "FailedMount|ErrImagePull|ImagePullBackOff|FailedScheduling"
```

## 8.7 Verificacion de imagen desplegada y variable CORS
```bash
kubectl -n energypredict-prod get deploy energypredict-api-prod -o jsonpath="{.spec.template.spec.containers[0].image}"
kubectl -n energypredict-prod get deploy energypredict-api-prod -o jsonpath="{.spec.template.spec.containers[0].env}"
```

## 8.8 Portal frontend
- Abrir URL HTTPS de SWA.
- Confirmar login.
- Ejecutar prediccion desde UI.
- Revisar salida JSON.

## 8.8.1 Registro de usuario desde la UI
El portal incluye formulario de registro (email, password, role) en el bloque de autenticacion.

Flujo:
1. Abrir el portal HTTPS de SWA.
2. Completar formulario `Create User`.
3. Pulsar `Create user`.
4. Verificar mensaje de exito en UI.
5. Iniciar sesion con ese usuario desde el mismo portal.

Validacion API equivalente:
```bash
curl -X POST "<API_BASE_URL>/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"demo.user@energypredict.local","password":"DemoPass!123","role":"operator"}'
```

Nota:
- La API no renderiza HTML propio; el consumo visual se hace desde SWA.
- Si se prueba directo en navegador, abrir docs OpenAPI (`/docs`) o endpoints JSON.

## 8.8.2 Verificacion de conectividad online (SWA -> API)
1. En DevTools del navegador (tab `Network`), confirmar peticiones a `<API_BASE_URL>`.
2. Confirmar que no hay bloqueos CORS ni mixed-content.
3. Si SWA (HTTPS) llama a API en HTTP, el navegador puede bloquear la llamada.
4. Solucion recomendada para entorno profesional: exponer API con HTTPS valido en Ingress.

## 8.9 CSI + Workload Identity (dev)
```bash
kubectl apply -k k8s/overlays/dev
kubectl get sa -n energypredict-dev
kubectl get secretproviderclass -n energypredict-dev
kubectl get pods -n energypredict-dev
kubectl get secret energypredict-secrets -n energypredict-dev
kubectl describe pod -n energypredict-dev <pod-name>
```

## 8.10 CSI + Workload Identity (prod)
```bash
kubectl get sa -n energypredict-prod
kubectl get secretproviderclass -n energypredict-prod
kubectl get secret energypredict-secrets -n energypredict-prod
kubectl describe pod -n energypredict-prod <pod-name>
```

## 8.11 CI/CD en Azure DevOps
1. Verificar estado exitoso de:
- `azure-pipelines-infra.yml`
- `azure-pipelines-app.yml`
- `azure-pipelines-frontend.yml`

## 8.12 Trazabilidad HTTP (middleware)
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

## 8.13 Rollback
```bash
kubectl rollout history deployment/energypredict-api-dev -n energypredict-dev
kubectl rollout undo deployment/energypredict-api-dev -n energypredict-dev
kubectl rollout status deployment/energypredict-api-dev -n energypredict-dev

kubectl rollout history deployment/energypredict-api-prod -n energypredict-prod
kubectl rollout undo deployment/energypredict-api-prod -n energypredict-prod
kubectl rollout status deployment/energypredict-api-prod -n energypredict-prod
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
