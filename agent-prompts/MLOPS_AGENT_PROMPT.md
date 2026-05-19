# Prompt para agente MLOps

```txt
Actúa como un MLOps engineer senior. Sobre el proyecto EnergyPredict MLOps API ya creado, implementa la capa MLOps MVP.

Lee:
- docs/06_MLOPS_DATABRICKS_MLFLOW.md
- docs/03_DOMAIN_DATA_MODEL.md
- docs/04_API_SPECIFICATION.md

Implementa:
1. Dataset sintético si no existe.
2. Función build_features.
3. Entrenamiento con RandomForestClassifier.
4. Evaluación con accuracy, precision, recall, f1_score y roc_auc.
5. Guardado local del modelo con joblib.
6. Integración básica con MLflow si está disponible.
7. Entidades TrainingRun y ModelVersion si no existen.
8. Endpoint POST /models/train.
9. Endpoint GET /models/current.
10. Endpoint POST /models/{id}/promote.
11. Registro de model_version_id en cada predicción.
12. Tests mínimos de entrenamiento y permisos.

Criterio:
- Si MLflow no está corriendo, el sistema debe seguir funcionando con modo local.
- Mantén claro qué parte es demo local y qué parte se integraría con Databricks.
```
