# Quality Report

## Estado

Vertical slice backend implementado y verificable:

- API funcional con auth JWT, RBAC, health, predict y modelos.
- Persistencia SQLite para usuarios, predicciones y version de modelo.
- Training local y registro de metricas/artefactos en flujo MLOps MVP.
- Artefactos de entrega presentes para Docker, AKS y CI/CD.

## Riesgos y mitigaciones

- Riesgo medio: `jwt_secret_key` tiene default inseguro (`change-me`).
  - Mitigacion: exigir secreto por entorno y rotacion.
- Riesgo medio: sin rate limiting ni lockout de login.
  - Mitigacion: APIM/Ingress + politica anti-bruteforce.
- Riesgo medio: conectores enterprise en modo simulado (Databricks/Snowflake/MLflow local).
  - Mitigacion: activar integraciones reales por fase 3.

## Evidencia de calidad

- Tests de auth, roles, health, predict, validacion y pipeline ML en `tests/**`.
- Endpoints sensibles (`/predict`, `/models/train`, `/models/current`, `/auth/me`) protegidos por autenticacion/autorizacion.
- Contratos principales cubiertos con `pytest` como gate de regresion.
