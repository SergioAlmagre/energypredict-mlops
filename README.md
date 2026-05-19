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
- Middleware de trazabilidad HTTP (`trace_id`, metodo, ruta, status, latencia, user, role).
- CI/CD en Azure DevOps:
  - `azure-pipelines-infra.yml`
  - `azure-pipelines-app.yml`
  - `azure-pipelines-frontend.yml`
- Variable Group `energypredict-shared` gestionable como codigo (`infra/terraform/devops`).
- Suite de tests automatizados.

## AKS-First Quickstart
```powershell
cd infra/terraform/envs/dev
Copy-Item terraform.tfvars.example terraform.tfvars
terraform init
terraform plan -out tfplan
terraform apply tfplan
```

Backend and frontend deployment are managed through Azure DevOps pipelines (`infra`, `app`, `frontend`).

## API Base Path
- ` /api/v1`

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





