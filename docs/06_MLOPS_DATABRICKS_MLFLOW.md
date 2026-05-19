# 06 - MLOps, Databricks y MLflow

## Estado actual
- Utilidades ML base en `app/ml`.
- Flujo MLOps descrito, sin integración real en ejecución aún.

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

## MVP implementado vs extensión

### MVP implementado
- Diseño de proceso MLOps.
- Módulos base para features/métricas.

### Extensión productiva
- Endpoint `/models/train` conectado a Job Databricks.
- Persistencia de `run_id`, métricas y modelo promovido.
- Monitoreo de drift y calidad en producción.
