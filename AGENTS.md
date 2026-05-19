# AGENTS.md

Instrucciones para agentes de IA que trabajen en este repositorio.

## Objetivo del proyecto

Construir **EnergyPredict MLOps API**, una API profesional con FastAPI para mantenimiento predictivo industrial, enfocada a evaluacion técnica. El objetivo no es crear el sistema más grande posible, sino una solución **robusta**, **bien estructurada** y **alineada con producción**.

## Restricción principal

El usuario tiene tiempo limitado. Priorizar siempre:

1. Código funcional.
2. Arquitectura limpia.
3. Seguridad básica real.
4. README y operacion técnica.
5. Tests mínimos.
6. Docker y Kubernetes.
7. CI/CD documentado.

No sobreingenierizar.

## Stack objetivo

- Python 3.11+
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic opcional
- SQLite para demo rápida
- PostgreSQL como alternativa productiva
- scikit-learn
- pandas
- MLflow
- pytest
- Docker
- Kubernetes/AKS
- GitHub Actions o Azure DevOps

## Principios de diseño

### 1. Separación de capas

No meter lógica compleja en los routers.

Capas esperadas:

- `api/`: endpoints FastAPI.
- `schemas/`: modelos Pydantic.
- `db/`: SQLAlchemy y repositorios.
- `services/`: lógica de negocio, si se crea.
- `ml/`: entrenamiento, inferencia, features y registry.
- `integrations/`: Snowflake, Databricks, MLflow.
- `core/`: configuración, seguridad, logging, errores.

### 2. Seguridad desde el inicio

Todo endpoint sensible debe usar JWT.

Roles mínimos:

- `admin`
- `ml_engineer`
- `analyst`
- `consumer`

Reglas:

- `/predict`: `consumer`, `analyst`, `ml_engineer`, `admin`
- `/models/train`: `ml_engineer`, `admin`
- `/models/promote`: `admin`
- `/predictions`: `analyst`, `ml_engineer`, `admin`
- `/feedback`: `analyst`, `ml_engineer`, `admin`

### 3. Configuración por entorno

Usar variables de entorno con `.env`.

Nunca hardcodear:

- passwords
- JWT secret
- Fernet key
- database URL
- Snowflake credentials
- Databricks token
- MLflow URI

### 4. MLOps robusta

Cada predicción debe registrar:

- input recibido
- output del modelo
- versión del modelo
- usuario
- timestamp
- probabilidad
- identificador de predicción

Cada entrenamiento debe registrar:

- dataset usado
- algoritmo
- parámetros
- métricas
- artifact path
- estado del modelo

### 5. AKS robusta

Crear manifests mínimos:

- Namespace dev/prod
- Deployment
- Service
- Ingress
- ConfigMap
- Secret
- HPA opcional
- probes: liveness/readiness

### 6. Testing mínimo obligatorio

Tests esperados:

- login correcto
- login incorrecto
- endpoint protegido sin token
- endpoint protegido con token
- `/predict` devuelve estructura válida
- usuario sin rol no puede entrenar
- healthcheck responde OK

## Criterios de aceptación MVP

El MVP se considera terminado cuando:

- `uvicorn app.main:app --reload` arranca.
- `/docs` muestra endpoints.
- Se puede crear/login usuario.
- Se puede obtener token.
- Se puede llamar `/predict` con token.
- `/predict` guarda una predicción.
- Existe endpoint `/models/current`.
- Existe endpoint `/models/train`, aunque sea entrenamiento sencillo.
- Existen tests básicos.
- Existe Dockerfile.
- Existe `Dockerfile`.
- Existen manifests Kubernetes.
- Existe pipeline CI/CD, aunque no se ejecute realmente.
- README explica cómo explicar el proyecto.

## Estilo de código

- Python claro y mantenible.
- Type hints.
- Nombres descriptivos.
- Evitar funciones gigantes.
- Usar dependencias de FastAPI para auth y roles.
- Validar todo con Pydantic.
- Devolver errores HTTP coherentes.
- Logs estructurados cuando sea posible.

## No hacer salvo que sobre tiempo

- Frontend.
- Autenticación con proveedor externo real.
- Compleja arquitectura de microservicios.
- Entrenamientos largos.
- GPU.
- Streaming real.
- Spark real si no es imprescindible.
- Terraform completo.

## Comandos esperados

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest
docker build -t energypredict-api:local .
docker compose up --build
kubectl apply -k k8s/overlays/dev
```

## Mensaje para agentes

Antes de generar código, leer:

1. `docs/00_PROJECT_CONTEXT_FOR_AI_AGENTS.md`
2. `docs/01_SCOPE_AND_ROADMAP.md`
3. `docs/03_DOMAIN_DATA_MODEL.md`
4. `docs/04_API_SPECIFICATION.md`
5. `docs/09_OPERATIONAL_GUIDE.md`

Trabajar por incrementos pequeños. Después de cada bloque, dejar el proyecto ejecutable.



