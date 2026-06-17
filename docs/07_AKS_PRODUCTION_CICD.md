# 07 - AKS, Produccion y CI/CD

## Estado actual
Existe un flujo real CI/CD en Azure DevOps con pipelines separados para infraestructura, backend y frontend estatico.

## Despliegue backend (AKS)
- Imagen Docker inmutable por commit SHA.
- Namespaces: `energypredict-dev` y `energypredict-prod`.
- Recursos K8s: Deployment, Service, Ingress, ConfigMap, Secret, HPA.
- Secretos runtime: Key Vault CSI Driver + `SecretProviderClass` + Workload Identity.
- Probes:
  - Liveness: `/api/v1/health/live`
  - Readiness: `/api/v1/health/ready`
- Estrategia de rollout: `RollingUpdate`.

### Readiness y orden de arranque

Kubernetes no orquesta dependencias de negocio en orden estricto. La API puede arrancar antes de que exista un modelo production, pero no recibira trafico mientras `/api/v1/health/ready` responda `503`.

La readiness actual comprueba:

1. DB accesible con `SELECT 1`.
2. Metadata de modelo production disponible en el registry.

Si falla, devuelve un `reason` operativo:

- `database_unreachable`
- `no_production_model_registered`
- `registry_backend_unreachable`
- `registry_payload_invalid`
- `model_readiness_check_failed`

Esto permite distinguir un problema de inicializacion real de una dependencia todavia no disponible. Un fallo de readiness deja el pod en `Running` pero `NotReady`; no deberia provocar `CrashLoopBackOff`.

## Despliegue frontend (HTTPS)
- Frontend estatico: `frontend/simulator-portal`.
- Hosting: Azure Static Web App.
- HTTPS gestionado por Azure (certificado automatico).
- Configuracion por entorno inyectada en pipeline via `config.template.js`.

## Pipelines Azure DevOps

### 1) Infraestructura
- Archivo: `azure-pipelines-infra.yml`.
- Stages: `Terraform_Plan_Dev`, `Terraform_Apply_Dev`, `Terraform_Plan_Prod`, `Terraform_Apply_Prod`.
- Proposito: aprovisionar AKS, ACR, KV, Databricks, PostgreSQL, SWA, etc.

### 2) Aplicacion backend
- Archivo: `azure-pipelines-app.yml`.
- Stages:
  - `CI` (lint, tests, docker build)
  - `Deploy_Dev` (branch `dev`)
  - `Deploy_Prod` (branch `main`)
- Ajuste clave: aplica `CORS_ALLOWED_ORIGINS` por entorno durante deploy.
- Ajuste clave adicional: inyeccion en overlay de `clientId`, `tenantId` y `keyVaultName` para CSI/Workload Identity.

### 3) Frontend estatico
- Archivo: `azure-pipelines-frontend.yml`.
- Stages:
  - `Validate_Frontend`
  - `Deploy_Dev` (branch `dev`)
  - `Deploy_Prod` (branch `main`)
- El deployment token de SWA se obtiene en runtime con Azure CLI.

## Rollback

### Backend (AKS)
```bash
kubectl rollout undo deployment/energypredict-api-dev -n energypredict-dev
kubectl rollout undo deployment/energypredict-api-prod -n energypredict-prod
```

### Frontend (SWA)
- Re-ejecutar pipeline con commit anterior, o revertir commit y redeploy.

## Blue/Green o Rolling
- Estado actual: `RollingUpdate` (implementado).
- Blue/Green: defendible como extension usando dos deployments + cambio controlado de Service/Ingress.

## MVP implementado vs extension

### MVP implementado
- Infra/app/frontend desplegables con Azure DevOps.
- Separacion `dev` y `prod`.

### Extension productiva
- Aprobaciones obligatorias en prod para app y frontend.
- APIM delante de la API.
- WAF y politicas de seguridad avanzadas.
