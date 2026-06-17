# 13 - Multi-Agent Delivery Strategy

## Objetivo
Coordinar integracion incremental por fases, con ownership claro y contratos compartidos, evitando bloqueos entre agentes.

## Ownership por carpetas
- `app/**`: implementacion API/servicios (fuera del alcance QA+Docs en esta iteracion).
- `k8s/**` y `.github/workflows/**`: plataforma y delivery (fuera del alcance QA+Docs en esta iteracion).
- `tests/**`: ownership QA para contratos minimos y regresion critica.
- `docs/**`, `README.md`, `quality-report.md`, `security-checklist.md`: ownership Docs+QA para narrativa, trazabilidad y evidencia.

## Contratos compartidos (fuente de verdad)
1. API base: prefijo `/api/v1`.
2. Salud: `GET /health/live` -> `{"status":"ok"}`, `GET /health/ready` -> `{"status":"ready","database":"ok","model":"ok"}`.
3. Auth: `POST /auth/register`, `POST /auth/login` (OAuth2 password form), `GET /auth/me`.
4. Prediccion: `POST /predict` autenticado, respuesta con `prediction_id`, `risk_level`, `failure_probability`, `model_version`.
5. Modelos: `GET /models/current` autenticado, `POST /models/train` restringido a `ml_engineer|admin`.
6. Integraciones MLOps:
   - MLflow: fallback local para desarrollo y Databricks MLflow en cloud.
   - Databricks: launcher configurable para Kubernetes Jobs o Databricks Jobs API.
   - Snowflake/datasets: CSV local para desarrollo y lectura cloud configurable.

## Orden de integracion por fases
1. Fase 0 - Contrato y baseline
   - Confirmar esquema de endpoints, roles y payloads.
   - Congelar contratos en tests de humo.
2. Fase 1 - Vertical slice operativo (estado actual)
   - FastAPI + JWT + RBAC + persistencia SQLite.
   - `/health`, `/auth`, `/predict`, `/models/current`, `/models/train`.
   - Dockerfile, manifests AKS base/overlays, workflows CI/CD presentes.
3. Fase 2 - Hardening de seguridad y operacion
   - Secretos por entorno, rate limiting, auditoria extendida, observabilidad.
   - Gates de calidad mas estrictos en CI.
4. Fase 3 - Integraciones productivas
   - Validar conectores reales con credenciales cloud y datos representativos.
   - Declarar objetos Databricks con Terraform si se exige IaC completo dentro del workspace.
   - Promotion flow dev->prod con evidencia y rollback probado.

## Checklist de integracion por fase
### Fase 0
- Contratos API acordados y documentados.
- Tests criticos de auth/roles/predict definidos.
### Fase 1
- Endpoints core funcionales y protegidos.
- Persistencia minima de usuarios/predicciones activa.
- `pytest -q` en verde.
### Fase 2
- Secretos no hardcodeados en runtime productivo.
- Controles anti-abuso en login y endpoints sensibles.
- Checklist OWASP API revisada.
### Fase 3
- Conectores MLOps reales validados extremo a extremo.
- Evidencia de despliegue en dev y promocion a prod.
- Runbooks actualizados con procedimiento de rollback.

## Definition of Done (DoD)
- Funcional: contrato del endpoint cumplido y cubierto por test.
- Seguridad: autenticacion/autorizacion aplicada segun rol.
- Calidad: `python -m pytest -q` en verde sin romper tests existentes.
- Documentacion: README y docs sin contradiccion con estado real, diferenciando fallback local de runtime cloud.
- Operacion: pasos de ejecucion local y despliegue documentados.
