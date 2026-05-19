# 01 - Alcance, roadmap y plan de ejecución

## Objetivo del documento

Definir qué se construye, qué se deja preparado/documentado y cómo priorizar para terminar algo robusta en tiempo limitado.

## Matriz de prioridades

| Prioridad | Elemento | Motivo |
|---|---|---|
| P0 | FastAPI con auth JWT | Es el núcleo de la apificación segura |
| P0 | Endpoint `/predict` | Demuestra inferencia ML apificada |
| P0 | Modelo ML simple | Permite hablar de ML sin atascarse |
| P0 | Registro de predicciones | Permite hablar de auditoría y trazabilidad |
| P0 | Dockerfile | Base para producción y AKS |
| P0 | Kubernetes manifests | Permite explicar AKS |
| P0 | README y guía de operacion | Clave para evaluacion |
| P1 | `/models/train` | Demuestra entrenamiento apificado |
| P1 | MLflow básico | Demuestra MLOps real |
| P1 | CI/CD YAML | Permite explicar pipelines |
| P1 | Roles | Demuestra autorización |
| P1 | Tests | Demuestra calidad |
| P2 | Databricks adapter | Demuestra integración enterprise |
| P2 | Snowflake adapter | Demuestra integración de datos |
| P2 | API Management docs | Demuestra producción/gobierno |
| P3 | RAG/embeddings | Extra para IA generativa |

## MVP funcional

El MVP debe permitir una demo de 5 minutos:

1. Abrir `/docs`.
2. Crear usuario.
3. Login.
4. Copiar token.
5. Llamar `/predict`.
6. Ver respuesta con riesgo y versión del modelo.
7. Consultar histórico de predicciones.
8. Lanzar `/models/train` o simular training run.
9. Mostrar Dockerfile.
10. Mostrar manifests AKS.
11. Mostrar pipeline CI/CD.
12. Explicar dev/prod.

## Plan de 3 días

### Día 1 - API y seguridad

Objetivo: tener una API viva, segura y con inferencia básica.

Tareas:

- Crear repo y estructura.
- Crear `app/main.py`.
- Configuración con Pydantic Settings.
- Base de datos SQLite.
- Modelos SQLAlchemy.
- Registro/login.
- JWT.
- Roles.
- Endpoint `/health/live`.
- Endpoint `/health/ready`.
- Endpoint `/predict`.
- Modelo fake o modelo scikit-learn simple.
- Tests mínimos de auth y predict.

Resultado del día:

> Puedo arrancar la API, autenticarme y pedir una predicción.

### Día 2 - MLOps y datos

Objetivo: tener ciclo de entrenamiento, versionado básico y trazabilidad.

Tareas:

- Crear dataset sintético.
- Entrenar RandomForest/LogisticRegression.
- Guardar modelo local.
- Crear `ModelVersion`.
- Crear `TrainingRun`.
- Registrar métricas.
- Integración básica con MLflow.
- Endpoint `/models/train`.
- Endpoint `/models/current`.
- Endpoint `/models/{id}/promote`.
- Endpoint `/predictions/{id}/feedback`.
- Adaptadores stub para Snowflake y Databricks.
- Tests de roles y modelos.

Resultado del día:

> Puedo explicar que la API no solo predice, sino que participa en el ciclo MLOps.

### Día 3 - Producción, AKS, CI/CD y operacion

Objetivo: tener material profesional para explicar producción.

Tareas:

- Dockerfile.
- docker-compose.
- k8s/base:
  - deployment
  - service
  - ingress
  - configmap
  - secret
- k8s/overlays/dev.
- k8s/overlays/prod.
- GitHub Actions:
  - CI
  - deploy dev
  - deploy prod
- README final.
- Guía de operacion.
- Preguntas y respuestas.
- Diagramas Mermaid.

Resultado del día:

> Puedo explicar cómo llevaría esta API a producción en AKS con CI/CD, APIM, DNS, secrets, monitoring y separación dev/prod.

## Qué dejar simulado sin miedo

Para una evaluacion técnica, es válido si está bien justificado:

| Elemento | Implementación demo | operacion productiva |
|---|---|---|
| Snowflake | CSV local o SQLite | Python Connector/Spark Connector |
| Databricks | clase stub | Databricks Jobs API |
| MLflow Registry | local file store | Databricks MLflow + Unity Catalog |
| Secrets | `.env` y Kubernetes Secret | Azure Key Vault CSI |
| AKS | manifests sin clúster real | despliegue real con ACR + AKS |
| APIM | documentación | import OpenAPI + policies |
| DNS | ingress host ficticio | Azure DNS/Public DNS |
| PySpark | notebook o pseudocódigo | Databricks cluster/serverless |

## Métricas de éxito

El proyecto es exitoso si puedes responder claramente:

- ¿Cómo se autentican los usuarios?
- ¿Cómo se autorizan acciones por rol?
- ¿Qué está cifrado?
- ¿Qué endpoints tiene la API?
- ¿Cómo se entrena el modelo?
- ¿Cómo se versiona el modelo?
- ¿Cómo sabes qué modelo hizo cada predicción?
- ¿Cómo se despliega en AKS?
- ¿Qué diferencia hay entre dev y prod?
- ¿Qué hace el pipeline CI/CD?
- ¿Dónde viven los secretos?
- ¿Cómo se integra Snowflake?
- ¿Cómo se integra Databricks?
- ¿Qué harías para producción real?



