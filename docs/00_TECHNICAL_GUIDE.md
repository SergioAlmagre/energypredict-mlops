# Technical Guide

Documento extendido para el equipo técnico con arquitectura, operación y evolución del sistema.

## 1. Estado actual
- API FastAPI funcional.
- JWT + roles.
- Persistencia SQLite.
- Entrenamiento e inferencia base.
- Tests automatizados.
- Artefactos Docker/K8s/CI-CD.

## 2. Arquitectura
Ver `docs/02_ARCHITECTURE.md` y `docs/diagrams/architecture.mmd`.

## 3. Operación
- E2E Azure/AKS/DevOps: sección `Full operational runbook (integrated)` en `README.md`.

## 4. Seguridad
Ver `docs/05_SECURITY_AUTH_ENCRYPTION.md`.

## 5. MLOps
Ver `docs/06_MLOPS_DATABRICKS_MLFLOW.md`.

## 6. CI/CD
Ver `docs/07_AKS_PRODUCTION_CICD.md`.

## 7. Roadmap recomendado
1. PostgreSQL + migraciones.
2. MLflow remoto gestionado.
3. APIM policies y observabilidad completa.
4. Pruebas de carga y SLOs.


