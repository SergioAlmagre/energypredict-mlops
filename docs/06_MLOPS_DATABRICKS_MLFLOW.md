# 06 - MLOps, Databricks y MLflow

## Estado actual
- Utilidades ML base en `app/ml`.
- Entrenamiento local para desarrollo y Kubernetes Jobs para cloud.
- Tracking en Databricks MLflow mediante `MLFLOW_TRACKING_URI=databricks`.
- Registro formal del modelo en Databricks Unity Catalog con `MLFLOW_REGISTRY_URI=databricks-uc`.
- Cache operativo de artifacts y `registry.json` en Azure Blob Storage.

## Flujo MLOps objetivo
1. Ingesta de datos de sensores/históricos.
2. Feature engineering (PySpark en Databricks para volumen alto).
3. Entrenamiento batch.
4. Registro de runs y métricas en Databricks MLflow.
5. Registro del modelo entrenado en Unity Catalog Model Registry.
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
- Databricks MLflow para tracking y Unity Catalog como registry gobernado.
- Registro del estimador sklearn con `mlflow.sklearn.log_model(..., registered_model_name=...)`.
- Readiness de API validando DB y metadata de modelo production.

### Extension productiva
- Databricks provider en Terraform para declarar experiments, jobs y esquemas Unity Catalog.
- Monitoreo de drift y calidad en produccion.
- Promotion flow formal entre dev/staging/prod con aprobaciones.

## Registro en Databricks Unity Catalog

El entrenamiento cloud se ejecuta como Kubernetes Job en AKS, pero el sistema de gobierno del modelo vive en Databricks:

1. El Job carga datos, entrena el modelo sklearn y calcula metricas.
2. El artifact `.pkl` se publica en Azure Blob Storage para que AKS pueda consumirlo de forma simple y estable.
3. El mismo entrenamiento abre un run de MLflow en Databricks.
4. El modelo se registra como entidad gobernada en Unity Catalog usando un nombre de tres niveles:

```text
<catalog>.<schema>.<model>
```

Ejemplo:

```text
energypredict.mlops.asset_failure_classifier
```

Variables relevantes:

```text
MLFLOW_TRACKING_URI=databricks
MLFLOW_REGISTRY_URI=databricks-uc
MLFLOW_EXPERIMENT_NAME=energypredict-training
MLFLOW_MODEL_NAME=asset_failure_classifier
MLFLOW_REGISTER_MODEL=true
MLFLOW_UC_CATALOG=energypredict
MLFLOW_UC_SCHEMA=mlops
MLFLOW_REGISTERED_MODEL_NAME=energypredict.mlops.asset_failure_classifier
```

`MLFLOW_REGISTERED_MODEL_NAME` tiene prioridad. Si no se informa, la aplicacion compone el nombre con `MLFLOW_UC_CATALOG`, `MLFLOW_UC_SCHEMA` y `MLFLOW_MODEL_NAME`.

Requisitos en Databricks:

1. Unity Catalog habilitado en el workspace.
2. Catalog y schema creados antes del entrenamiento.
3. La identidad usada por el Job debe tener permisos `USE CATALOG`, `USE SCHEMA` y `CREATE MODEL`.
4. `DATABRICKS_HOST` y `DATABRICKS_TOKEN` deben estar disponibles en runtime desde Key Vault/Secrets.

## Por que Blob y Unity Catalog conviven

No son duplicados:

- Unity Catalog es el registro gobernado: lineage, auditoria, permisos y discovery del modelo.
- Blob Storage es el cache operativo que la API en AKS puede leer de forma directa para inferencia online.

Con este diseno, Databricks conserva la trazabilidad MLOps y AKS mantiene un runtime de inferencia sencillo, desacoplado y rapido de arrancar.

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
