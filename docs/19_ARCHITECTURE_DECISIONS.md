# 19 - Architecture Decisions

Este documento resume las decisiones principales del proyecto, las alternativas consideradas y el motivo por el que se eligio cada camino.

## Principio general

EnergyPredict prioriza una arquitectura cloud-ready, explicable y operable:

- AKS para runtime de aplicacion, inferencia y Jobs.
- Databricks para lakehouse, MLflow, Unity Catalog y gobierno del modelo.
- Event Hub para telemetria streaming.
- Azure Blob Storage para cache operativo de artifacts.
- Azure DevOps y Terraform para delivery e infraestructura.

La meta no es usar todas las herramientas posibles, sino asignar responsabilidades claras y reducir duplicidad.

## Decision 1 - FastAPI para la API

### Elegido

FastAPI.

### Alternativas

- Flask.
- Django REST Framework.
- Azure Functions.

### Por que FastAPI

- Pydantic valida payloads de inferencia y entrenamiento.
- OpenAPI/Swagger sale automaticamente.
- Buen rendimiento para APIs REST.
- Modelo de dependencias sencillo para auth, DB sessions y RBAC.
- Encaja bien con contenedores y AKS.

### Por que no Flask

Flask es valido, pero requeriria montar mas piezas manualmente: validacion, OpenAPI, dependency injection y tipado de schemas.

### Por que no Django

Django aporta mucho si el dominio principal es CRUD/admin complejo. Aqui el foco es inferencia, MLOps, streaming y runtime ligero.

### Por que no Azure Functions

Functions simplifica serverless, pero limita el control del runtime, probes, workers, deployment K8s y librerias ML pesadas. AKS da mas control para una plataforma MLOps.

## Decision 2 - AKS como runtime principal

### Elegido

AKS con Deployments, Jobs, CronJobs, probes y HPA.

### Alternativas

- App Service.
- Container Apps.
- Azure ML endpoints.
- Databricks Model Serving.

### Por que AKS

- Control del runtime de API, data processor, training jobs y drift monitor.
- Kustomize permite overlays dev/prod.
- Probes y rollout strategy son explicitos.
- Encaja con CI/CD de Azure DevOps y ACR.

### Por que no App Service

App Service simplifica hosting, pero no cubre tan bien Jobs, CronJobs, ServiceMonitor, workers y patrones K8s.

### Por que no Container Apps

Container Apps seria una opcion razonable para simplificar operaciones, pero el proyecto quiere demostrar AKS, Kustomize, probes, HPA, Workload Identity y observabilidad K8s.

### Por que no solo Databricks Serving

Databricks Serving puede servir modelos, pero la API hace mas que inferencia: auth, RBAC, rate limiting, streaming, alertas, explicaciones y contratos de plataforma.

## Decision 3 - Event Hub + data-processor para prediccion automatica

### Elegido

Event Hub como bus de telemetria y `data-processor` como consumidor.

### Alternativas

- Llamadas manuales a `/predict`.
- Thread interno en FastAPI.
- Kafka gestionado.
- Polling directo a una base de datos.

### Por que Event Hub

- Es nativo de Azure para streaming.
- Desacopla productores de consumidores.
- Permite que Databricks, simuladores o IoT publiquen eventos sin conocer la API.
- El data processor convierte telemetria en `SensorEvent`, `Alert` y metricas.

### Por que no llamadas manuales

`/predict` queda como contrato de API y fallback, pero no debe ser el flujo productivo. La prediccion automatica necesita telemetria variable que llegue sola.

### Por que no thread interno en FastAPI

El thread interno sirve para demo, pero en cloud puede duplicar responsabilidad del API y mezclar serving con ingestion. Por eso `API_SIMULATION_WORKER_ENABLED=false` en runtime cloud.

### Por que no Kafka

Kafka es potente, pero Event Hub reduce friccion en Azure y cubre el caso de telemetria industrial sin operar otro cluster.

## Decision 4 - Databricks MLflow y Unity Catalog como registry

### Elegido

Databricks MLflow Tracking + Unity Catalog Model Registry.

### Alternativas

- MLflow server propio en AKS.
- Azure ML Registry.
- Registry local en Blob como unica fuente.
- Kubeflow Model Registry.

### Por que Databricks

- El lakehouse y los datasets viven cerca de Databricks.
- Unity Catalog aporta permisos, lineage, auditoria y modelo de nombres `catalog.schema.model`.
- MLflow esta integrado de forma natural.
- Evita operar un MLflow server propio.

### Por que no MLflow en AKS

Operar MLflow propio implica backend store, artifact store, upgrades, auth, backups y HA. Databricks ya proporciona esa capa gestionada.

### Por que no Azure ML Registry

Azure ML Registry es valido, pero el proyecto ya usa Databricks para lakehouse/MLflow. Meter otro registry dividiria gobierno y lineage.

### Por que no solo Blob

Blob es cache operativo para artifacts consumidos por AKS. No sustituye un registry gobernado con lineage, permisos y discovery.

## Decision 5 - Azure Blob como cache operativo de modelos

### Elegido

Blob Storage para artifacts `.pkl`, registry operativo y datasets procesados.

### Alternativas

- Descargar siempre desde Unity Catalog.
- Guardar artifacts dentro de la imagen Docker.
- Montar disco persistente en AKS.

### Por que Blob

- AKS puede consumir artifacts de forma sencilla.
- Permite desacoplar serving de Databricks en runtime.
- Evita reconstruir imagen por cada modelo.
- Encaja con Workload Identity y containers separados.

### Por que no meter el modelo en la imagen

Acopla release de aplicacion y version de modelo. Cada modelo exigiria build/deploy de imagen.

### Por que no disco persistente

Introduce estado en Kubernetes y complica replicas, rollback y recuperacion.

## Decision 6 - Drift monitoring batch con PSI

### Elegido

CronJob que calcula PSI sobre ventana reciente y compara contra baseline de training.

### Alternativas

- Calcular drift dentro de `/predict`.
- Usar solo Databricks Lakehouse Monitoring.
- No automatizar drift y revisarlo manualmente.

### Por que batch

- No penaliza latencia de inferencia.
- Permite ventanas temporales estables.
- Se puede auditar con drift reports.
- Puede disparar retraining sin bloquear el serving.

### Por que PSI

- Es interpretable.
- Es comun en scoring y risk.
- Funciona bien como primera senal de cambio distribucional.

### Por que no calcularlo en `/predict`

El endpoint online debe ser rapido y estable. Drift es analitica batch, no parte del hot path.

### Por que no solo Lakehouse Monitoring

Lakehouse Monitoring es una evolucion natural cuando inference tables Delta esten consolidadas. El PSI propio deja el contrato implementado sin depender de una feature externa para la demo.

## Decision 7 - Prometheus/Grafana para observabilidad

### Elegido

`/metrics` con `prometheus_client`, ServiceMonitor, PrometheusRule y dashboard Grafana.

### Alternativas

- Solo logs.
- Azure Monitor exclusivamente.
- Datadog/New Relic.

### Por que Prometheus/Grafana

- Patron estandar en Kubernetes.
- ServiceMonitor encaja con Prometheus Operator.
- Permite dashboard versionado como ConfigMap.
- Cubre API latency, error rate, predicciones, alertas y drift.

### Por que no solo logs

Los logs sirven para debugging, pero no para SLOs, alertas o tendencias numericas.

### Por que no solo Azure Monitor

Azure Monitor es valido para plataforma Azure, pero Prometheus/Grafana es mas portable y natural para metricas de app en Kubernetes.

## Decision 8 - No Kubeflow en esta fase

Ver detalle completo en `private-defense/KUBEFLOW_DECISION_RECORD.md`.

Resumen:

- Kubeflow seria excesivo para un training batch lineal.
- Duplicaria metadata/gobierno con Databricks Unity Catalog.
- Aumentaria coste operativo en AKS.
- Se reevalua si aparecen DAGs ML complejos, Katib, multi-model serving o plataforma ML multi-equipo.

## Decision 9 - Terraform + Azure DevOps

### Elegido

Terraform para infraestructura y Azure DevOps para CI/CD.

### Alternativas

- Bicep.
- Pulumi.
- GitHub Actions.
- Despliegues manuales.

### Por que Terraform

- Multi-stack dev/prod/devops.
- State remoto.
- Plan/apply auditable.
- Facil de explicar y revisar.

### Por que Azure DevOps

- Encaja con ecosistema enterprise Microsoft.
- Variable groups y service connections.
- Separacion de pipelines infra/app/frontend.

### Por que no despliegue manual

No es reproducible, no deja evidencia y aumenta riesgo operativo.

## Como responder en entrevista

Formato recomendado:

```text
Elegi X porque resuelve A y B con bajo coste operativo.
Considere Y y Z.
No use Y porque duplicaba responsabilidades / aumentaba operacion / no encajaba con el alcance.
Si el proyecto creciera hacia condicion C, reabriria la decision.
```

Ejemplo:

> "No elegi Kubeflow porque ya tengo Databricks como plano de gobierno MLOps y AKS como runtime. Meter Kubeflow ahora duplicaria metadata y control plane. Si necesitara DAGs complejos, Katib o KServe multi-model, lo reabriria."
