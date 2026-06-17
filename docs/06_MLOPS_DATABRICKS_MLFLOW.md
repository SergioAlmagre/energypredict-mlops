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
- Baseline estadistico de features guardado con cada modelo entrenado.
- Drift monitoring mediante Kubernetes CronJob y endpoint operativo.
- Prediccion automatica mediante Event Hub + data-processor.
- Observabilidad Prometheus/Grafana para API, predicciones, alertas y drift.

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
MLFLOW_SYNC_PRODUCTION_ALIAS=false
MLFLOW_PRODUCTION_ALIAS=champion
```

`MLFLOW_REGISTERED_MODEL_NAME` tiene prioridad. Si no se informa, la aplicacion compone el nombre con `MLFLOW_UC_CATALOG`, `MLFLOW_UC_SCHEMA` y `MLFLOW_MODEL_NAME`.

Requisitos en Databricks:

1. Unity Catalog habilitado en el workspace.
2. Catalog y schema creados antes del entrenamiento.
3. La identidad usada por el Job debe tener permisos `USE CATALOG`, `USE SCHEMA` y `CREATE MODEL`.
4. `DATABRICKS_HOST` y `DATABRICKS_TOKEN` deben estar disponibles en runtime desde Key Vault/Secrets.

Si `MLFLOW_SYNC_PRODUCTION_ALIAS=true`, la promocion de un modelo a production intenta mover el alias `champion` del modelo de Unity Catalog a la version registrada correspondiente. Esta sincronizacion es opcional porque requiere permisos reales sobre el registry de Databricks; si esta desactivada, el registry operativo sigue funcionando.

## Por que Blob y Unity Catalog conviven

No son duplicados:

- Unity Catalog es el registro gobernado: lineage, auditoria, permisos y discovery del modelo.
- Blob Storage es el cache operativo que la API en AKS puede leer de forma directa para inferencia online.

Con este diseno, Databricks conserva la trazabilidad MLOps y AKS mantiene un runtime de inferencia sencillo, desacoplado y rapido de arrancar.

## Data drift y retraining trigger

La primera implementacion productiva usa un patron batch:

```text
Predicciones/Sensor events persistidos
  -> CronJob energypredict-drift-monitor
  -> compara ventana reciente contra baseline del modelo production
  -> calcula PSI por feature
  -> guarda drift report
  -> si max_feature_psi >= threshold, dispara training job
```

Implementacion:

- `app/ml/drift.py`: baseline, calculo de PSI y decision.
- `app/jobs/drift_monitor.py`: runner ejecutado por Kubernetes CronJob.
- `POST /api/v1/models/drift/evaluate`: evaluacion bajo demanda.
- `GET /api/v1/models/drift/reports`: historico de reportes.
- `k8s/base/drift-monitor-cronjob.yaml`: ejecucion periodica en AKS.

Variables:

```text
DRIFT_MONITOR_WINDOW_HOURS=24
DRIFT_MONITOR_MIN_SAMPLES=30
DRIFT_PSI_WARNING_THRESHOLD=0.10
DRIFT_PSI_RETRAIN_THRESHOLD=0.25
DRIFT_RETRAINING_ENABLED=false
DRIFT_RETRAINING_DATASET_URI=azureblob://processed/latest/sensor_data.csv
DRIFT_ALERT_WEBHOOK_URL=
```

Decision de diseno:

- El endpoint `/predict` no calcula drift para no aumentar latencia ni mezclar serving online con analitica batch.
- El CronJob usa las inferencias persistidas y puede disparar el reentreno si `DRIFT_RETRAINING_ENABLED=true`.
- Si `DRIFT_ALERT_WEBHOOK_URL` esta configurado, los reportes `warning` y `retrain_required` envian una alerta HTTP.
- Cada training nuevo genera una version nueva, registra metricas en MLflow y registra el modelo en Unity Catalog.
- La promocion automatica solo ocurre si `f1_score >= AUTO_PROMOTE_MIN_F1_SCORE`; si no, el modelo queda como `candidate` y el champion anterior sigue en production.
- La promocion/rollback sigue apoyandose en el registry: el modelo production actual se puede cambiar a una version anterior mediante `POST /models/{model_id}/promote`.
- Si esta habilitado el alias sync, esa promocion tambien mueve el alias `champion` en Unity Catalog.

En una evolucion Databricks-first, este mismo contrato se puede mover a Lakehouse Monitoring/Data Profiling sobre tablas Delta de inferencia. La logica de decision seguiria siendo la misma: baseline, metricas, alerta, retraining workflow y promocion controlada.

## Prediccion automatica

El endpoint `POST /predict` sigue existiendo para pruebas, Swagger y simulaciones manuales, pero el flujo productivo no depende de una llamada humana:

```text
Databricks / IoT / generador sintetico
  -> Event Hub
  -> energypredict-data-processor
  -> ingest_telemetry_event()
  -> predict_failure_risk()
  -> SensorEvent + Alert + metricas Prometheus
  -> frontend consulta /stream/latest y /alerts
```

Configuracion:

```text
STREAM_INGESTION_ENABLED=true
API_SIMULATION_WORKER_ENABLED=false
EVENTHUB_NAME=<event-hub-name>
EVENTHUB_FQ_NAMESPACE=<namespace>.servicebus.windows.net
EVENTHUB_CONSUMER_GROUP=energypredict-consumer
```

`STREAM_INGESTION_ENABLED` controla el `data-processor`. `API_SIMULATION_WORKER_ENABLED` queda separado y debe reservarse para demo local; en cloud debe estar desactivado para no duplicar consumidores dentro de la API.

## Prometheus y Grafana

La API expone metricas reales en:

```text
GET /metrics
```

Metricas principales:

```text
energypredict_http_requests_total
energypredict_http_request_duration_seconds
energypredict_predictions_total
energypredict_active_alerts
energypredict_drift_reports_total
energypredict_drift_max_feature_psi
energypredict_drift_global_psi
energypredict_training_jobs_triggered_total
```

Manifests incluidos:

- `k8s/base/servicemonitor.yaml`
- `k8s/base/prometheus-rules.yaml`
- `k8s/base/grafana-dashboard.yaml`

Prerequisito:

- El cluster debe tener Prometheus Operator, normalmente instalado mediante `kube-prometheus-stack`.
- El chart de Grafana debe tener habilitado el sidecar de dashboards que descubre ConfigMaps con `grafana_dashboard: "1"`.

Dashboard incluido:

- API request rate.
- API p95 latency.
- Predicciones por riesgo y origen.
- Alertas activas.
- Drift PSI.
- Training jobs disparados por drift.

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
