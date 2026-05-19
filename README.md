# EnergyPredict MLOps API

Backend para mantenimiento predictivo industrial con FastAPI, MLOps y despliegue en Kubernetes (AKS-ready).

## Highlights
- FastAPI + OpenAPI.
- Auth JWT + RBAC por roles.
- Prediccion online (`/api/v1/predict`).
- Training endpoint (`/api/v1/models/train`).
- SQLAlchemy + SQLite (MVP), listo para PostgreSQL.
- Docker (imagen para AKS).
- Kubernetes manifests (`k8s/base`, `k8s/overlays`).
- Portal web estatico para simulador (`frontend/simulator-portal`).
- Registro de usuarios desde UI del portal (consume `POST /api/v1/auth/register`).
- Middleware de trazabilidad HTTP (`trace_id`, metodo, ruta, status, latencia, user, role).
- CI/CD en Azure DevOps:
  - `azure-pipelines-infra.yml`
  - `azure-pipelines-app.yml`
  - `azure-pipelines-frontend.yml`
- Variable Group `energypredict-shared` gestionable como codigo (`infra/terraform/devops`).
- Suite de tests automatizados.

## Visual Walkthrough
Estas capturas muestran el comportamiento real del proyecto en ejecucion.

### 1. Infrastructure Bootstrap
Primero se ve el pipeline de infraestructura completando el aprovisionamiento y dejando el estado listo para el resto del despliegue.

![Infra pipeline OK](docs/media/infra-pipeline-ok_censurada.jpg)

El backend de Terraform ya trabaja con backend remoto en Azure Storage para no depender del estado local.

![TFState storage resource](docs/media/storage-tfstate-resource_censurada.jpg)

Vista de todos los Resource Groups creados para separar el laboratorio por entorno y por componente.

![All resource groups](docs/media/all-resource-groups_censurada.jpg)

### 2. Provisioned Platform
Detalle de los recursos principales del entorno de produccion una vez aplicado el stack de plataforma.

![EnergyPredict prod resources](docs/media/energypredict-resources-prod_censurada.jpg)

Detalle de los recursos de AKS y su soporte operativo en Azure.

![AKS resources](docs/media/aks-resources_censurada.jpg)

Si la extension de datos esta activa, se observa el workspace de Databricks del entorno de produccion.

![Databricks prod resources](docs/media/databricks-prod-resources_censurada.jpg)

### 3. Product UI
Portal del simulador predictivo en Azure Static Web Apps (sin datos cargados en esta vista inicial).

![Predictive simulator portal (UI)](docs/media/predictive-simulator-ui-no-data_censurada.jpg)

### 4. API Health and Runtime Status
Verificacion de health checks del backend (`live` / `ready`) y estado operativo correcto.

![API health status OK](docs/media/health-status-ok_censurada.jpg)

### 5. Azure DevOps CI/CD Overview
Vista general de ejecucion de pipelines para infra, backend y frontend.

![Pipelines running](docs/media/pipelines-running_censurada.jpg)

Pipeline de backend (app) con fases de validacion y despliegue.

![Backend pipeline overview](docs/media/general-pipeline-app_censurada.jpg)

Validacion de seguridad de dependencias en CI (dependency audit).

![Dependency audit in app pipeline](docs/media/dependency-audit-pipeline-app_censurada.jpg)

Pipeline de frontend (vista general de despliegue).

![Frontend pipeline overview](docs/media/general-front-deploy-pipeline_censurada.jpg)

Pipeline de frontend (detalle del job de deploy).

![Frontend deploy details](docs/media/details-front-deploy-pipeline_censurada.jpg)

### 6. AKS and Kubernetes Operations
Estado del deployment y replicas en AKS.

![Deployment status](docs/media/status-deploy_censurada.jpg)

Relacion entre Service, Endpoints y Pods en namespace de aplicacion.

![Service, endpoints and pods](docs/media/svc-endpoints-pods_censurada.jpg)

Detalle de un pod para diagnostico operativo.

![Describe pod output](docs/media/describe-pod_censurada.jpg)

Eventos del pod para troubleshooting (scheduling, mounts, pulls, etc.).

![Pod events](docs/media/pod-events_censurada.jpg)

Metricas de escalado y consumo (`HPA` / `kubectl top`).

![HPA and top metrics](docs/media/hpa-top_censurada.jpg)

### 7. Data Layer
Estado de Azure Database for PostgreSQL en portal Azure.

![Azure Database for PostgreSQL dashboard](docs/media/azure-database-for-postgres-sql-dashboard_censurada.jpg)

## AKS-First Quickstart
```powershell
cd infra/terraform/envs/dev
Copy-Item terraform.tfvars.example terraform.tfvars
terraform init
terraform plan -out tfplan
terraform apply tfplan
```

Backend and frontend deployment are managed through Azure DevOps pipelines (`infra`, `app`, `frontend`).

El pipeline de app prepara host publico del API en Ingress y el pipeline de frontend puede consumir ese host para publicar `config.js` con `API_BASE_URL` por entorno.

## Quick cleanup (cost control)
Para destruir los entornos desplegados y evitar costes fuera de horario:
```powershell
.\scripts\destroy_all.ps1
```

## CI/CD without tfvars in repo
Para ejecutar Terraform desde Azure DevOps sin subir `terraform.tfvars`, genera:
- `TFVARS_DEV_B64`
- `TFVARS_PROD_B64`

Comando:
```powershell
.\scripts\generate_tfvars_b64.ps1
```

## API Base Path
- `/api/v1`

## Key Endpoints
- `GET /health/live`
- `GET /health/ready`
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `POST /predict`
- `GET /models/current`
- `POST /models/train`

## Documentation
- `docs/02_ARCHITECTURE.md`
- `docs/05_SECURITY_AUTH_ENCRYPTION.md`
- `docs/06_MLOPS_DATABRICKS_MLFLOW.md`
- `docs/07_AKS_PRODUCTION_CICD.md`
- `docs/09_FRONTEND_STATIC_SIMULATOR.md`
- `docs/14_SECURITY_HARDENING_PLAN.md`
- `docs/15_AKS_WORKLOAD_IDENTITY_KEYVAULT_CSI.md`
- `RUNBOOK_E2E_AZURE_DEVOPS.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`

## Delivery Scope
### MVP implemented
API, auth, prediction, training flow, persistence, tests, containerization and AKS-ready artifacts.

### Production extension
Advanced security hardening, full observability, and managed enterprise integrations.





