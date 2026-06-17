# 06 - MLOps, Databricks y MLflow

## Estado actual
- Utilidades ML base en `app/ml`.
- Entrenamiento local para desarrollo y Kubernetes Jobs para cloud.
- Tracking en Databricks MLflow mediante `MLFLOW_TRACKING_URI=databricks`.
- Registry gestionado preparado para Unity Catalog con `MLFLOW_REGISTRY_URI=databricks-uc`.
- Cache operativo de artifacts y `registry.json` en Azure Blob Storage.

## Flujo MLOps objetivo
1. Ingesta de datos de sensores/históricos.
2. Feature engineering (PySpark en Databricks para volumen alto).
3. Entrenamiento batch.
4. Registro de runs y métricas en MLflow.
5. Registro/promoción de modelo.
6. Serving online por API.
7. Feedback loop para reentrenos.

## Roles de cada tecnología
- MLflow: trazabilidad de experimentos y registry.
- Databricks: compute distribuido y orquestación de training.
- Snowflake: fuente de histórico corporativo.
- FastAPI: serving y orquestación, no training pesado.

## Implementado vs extension

### Implementado
- Endpoint `/models/train` con modo local y modo cloud `k8s_job`.
- Registro de training runs, metricas y modelo promovido.
- Artifacts `.pkl` publicados en Blob Storage cuando `MODEL_ARTIFACT_BACKEND=blob`.
- Registry operativo en Blob cuando `MODEL_REGISTRY_BACKEND=blob`.
- Databricks MLflow para tracking y Unity Catalog como registry gestionado.
- Readiness de API validando DB y metadata de modelo production.

### Extension productiva
- Databricks provider en Terraform para declarar experiments, jobs y esquemas Unity Catalog.
- Monitoreo de drift y calidad en produccion.
- Promotion flow formal entre dev/staging/prod con aprobaciones.

## Streaming Databricks -> Event Hub (implemented contract)
Archivo base del generador:
- `notebooks/databricks/synthetic_stream_generator.py`

Contrato de evento generado:
1. `asset_code`
2. `temperature`
3. `pressure`
4. `vibration`
5. `flow_rate`
6. `energy_consumption`
7. `operating_hours`

Metadatos opcionales recomendados:
1. `event_id`
2. `event_ts`
3. `source`
4. `anomaly`

Objetivo operativo:
1. Databricks emite eventos continuamente.
2. Event Hub los entrega al backend.
3. El worker de API persiste `SensorEvent` y activa alertas.
