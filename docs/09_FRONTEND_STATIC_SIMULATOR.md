# 09 - Frontend estatico HTTPS (Simulator Portal)

## Objetivo
Exponer una interfaz profesional para demos tecnicas sin depender de un frontend complejo ni de datos reales productivos.

## Ubicacion
- `frontend/simulator-portal`

## Stack
- HTML + CSS + JavaScript modular (sin framework)
- Azure Static Web App para hosting HTTPS

## Flujos funcionales
1. Configurar URL base de API (`/api/v1`).
2. Login contra `POST /auth/login`.
3. Ver perfil con `GET /auth/me`.
4. Ejecutar health checks:
- `GET /health/live`
- `GET /health/ready`
5. Ejecutar prediccion con `POST /predict`.
6. Consultar estado de integraciones con `GET /models/integrations/status` (roles `ml_engineer`/`admin`).

## Configuracion por entorno
- Archivo plantilla: `config.template.js`.
- Archivo runtime: `config.js`.
- El pipeline inyecta:
  - `FRONTEND_DEV_API_BASE_URL`
  - `FRONTEND_PROD_API_BASE_URL`

## CORS
Backend debe permitir origen del portal en cada entorno:
- `CORS_ALLOWED_ORIGINS_DEV`
- `CORS_ALLOWED_ORIGINS_PROD`

## Dependencia de seguridad backend
- El backend en AKS usa Workload Identity + Key Vault CSI para leer secretos en runtime.

## Deploy
Pipeline dedicado:
- `azure-pipelines-frontend.yml`

Stages:
1. `Validate_Frontend`
2. `Deploy_Dev`
3. `Deploy_Prod`

## Seguridad
- HTTPS lo gestiona Azure Static Web App.
- Sin secretos en frontend.
- Token JWT almacenado localmente solo para demo; para productivo real, migrar a flujo seguro con refresh/short-session.
