# 03 - Modelo de dominio y datos

## Objetivo

Definir entidades, relaciones y campos necesarios para explicar:

- Auth
- Roles
- Ingesta
- Inferencia
- AuditorÃ­a
- MLOps
- Feedback
- Model registry

## Entidades principales

```mermaid
erDiagram
    USER ||--o{ PREDICTION : creates
    USER ||--o{ TRAINING_RUN : launches
    ASSET ||--o{ SENSOR_EVENT : emits
    ASSET ||--o{ PREDICTION : has
    MODEL_VERSION ||--o{ PREDICTION : used_by
    MODEL_VERSION ||--o{ TRAINING_RUN : produced_by
    PREDICTION ||--o| PREDICTION_FEEDBACK : receives

    USER {
        uuid id
        string email
        string hashed_password
        string role
        bool is_active
        datetime created_at
        datetime updated_at
    }

    ASSET {
        uuid id
        string asset_code
        string asset_type
        string plant
        string location
        string criticality
        datetime created_at
    }

    SENSOR_EVENT {
        uuid id
        uuid asset_id
        float temperature
        float pressure
        float vibration
        float flow_rate
        float energy_consumption
        float operating_hours
        datetime event_timestamp
        datetime received_at
    }

    MODEL_VERSION {
        uuid id
        string name
        string version
        string stage
        string algorithm
        string artifact_uri
        float accuracy
        float precision
        float recall
        float f1_score
        float roc_auc
        datetime created_at
        datetime promoted_at
    }

    TRAINING_RUN {
        uuid id
        uuid user_id
        uuid model_version_id
        string status
        string dataset_uri
        string mlflow_run_id
        json parameters
        json metrics
        datetime started_at
        datetime finished_at
        string error_message
    }

    PREDICTION {
        uuid id
        uuid user_id
        uuid asset_id
        uuid model_version_id
        json input_payload
        json feature_payload
        string risk_level
        float failure_probability
        string recommendation
        datetime created_at
    }

    PREDICTION_FEEDBACK {
        uuid id
        uuid prediction_id
        bool real_failure
        string corrected_risk_level
        string comment
        datetime created_at
    }
```

## Tabla `users`

| Campo | Tipo | Requerido | DescripciÃ³n |
|---|---|---:|---|
| `id` | UUID | sÃ­ | Identificador interno |
| `email` | string unique | sÃ­ | Login del usuario |
| `hashed_password` | string | sÃ­ | Password con hash, nunca texto plano |
| `role` | enum/string | sÃ­ | `admin`, `ml_engineer`, `analyst`, `consumer` |
| `is_active` | bool | sÃ­ | Permite desactivar usuarios |
| `created_at` | datetime | sÃ­ | Fecha creaciÃ³n |
| `updated_at` | datetime | sÃ­ | Fecha actualizaciÃ³n |

Notas:

- No almacenar passwords en claro.
- Para demo se puede crear un usuario admin por seed.

## Tabla `assets`

Representa el activo industrial.

| Campo | Tipo | Ejemplo |
|---|---|---|
| `id` | UUID | `...` |
| `asset_code` | string unique | `PUMP-001` |
| `asset_type` | string | `pump` |
| `plant` | string | `refinery_a` |
| `location` | string | `unit_3` |
| `criticality` | enum | `low`, `medium`, `high` |
| `created_at` | datetime | `2026-05-16T10:00:00Z` |

## Tabla `sensor_events`

Guarda eventos de sensores crudos.

| Campo | Tipo | DescripciÃ³n |
|---|---|---|
| `id` | UUID | Evento |
| `asset_id` | FK | Activo |
| `temperature` | float | Temperatura |
| `pressure` | float | PresiÃ³n |
| `vibration` | float | VibraciÃ³n |
| `flow_rate` | float | Caudal |
| `energy_consumption` | float | Consumo |
| `operating_hours` | float | Horas de operaciÃ³n |
| `event_timestamp` | datetime | Momento de mediciÃ³n |
| `received_at` | datetime | Momento de recepciÃ³n por API |

Validaciones recomendadas:

- `temperature`: -50 a 250
- `pressure`: 0 a 500
- `vibration`: 0 a 50
- `flow_rate`: >= 0
- `energy_consumption`: >= 0
- `operating_hours`: >= 0

## Tabla `model_versions`

Representa una versiÃ³n de modelo.

| Campo | Tipo | DescripciÃ³n |
|---|---|---|
| `id` | UUID | ID interno |
| `name` | string | `asset_failure_classifier` |
| `version` | string | `1.0.0` |
| `stage` | enum | `staging`, `production`, `archived` |
| `algorithm` | string | `RandomForestClassifier` |
| `artifact_uri` | string | ruta local, MLflow URI o Databricks UC |
| `accuracy` | float | mÃ©trica |
| `precision` | float | mÃ©trica |
| `recall` | float | mÃ©trica |
| `f1_score` | float | mÃ©trica |
| `roc_auc` | float | mÃ©trica |
| `created_at` | datetime | creaciÃ³n |
| `promoted_at` | datetime nullable | promociÃ³n a prod |

Reglas:

- Solo debe haber un modelo `production` por nombre.
- No se promociona un modelo si no supera umbral mÃ­nimo.
- El modelo usado en predicciÃ³n siempre se guarda.

## Tabla `training_runs`

Representa una ejecuciÃ³n de entrenamiento.

| Campo | Tipo | DescripciÃ³n |
|---|---|---|
| `id` | UUID | ID interno |
| `user_id` | FK | Usuario que lanza |
| `model_version_id` | FK nullable | Modelo generado |
| `status` | enum | `pending`, `running`, `completed`, `failed` |
| `dataset_uri` | string | CSV, Snowflake query, Delta table |
| `mlflow_run_id` | string nullable | ID de MLflow |
| `parameters` | JSON | hiperparÃ¡metros |
| `metrics` | JSON | mÃ©tricas |
| `started_at` | datetime | inicio |
| `finished_at` | datetime nullable | fin |
| `error_message` | string nullable | error |

## Tabla `predictions`

Guarda trazabilidad de inferencias.

| Campo | Tipo | DescripciÃ³n |
|---|---|---|
| `id` | UUID | ID predicciÃ³n |
| `user_id` | FK | QuiÃ©n pidiÃ³ |
| `asset_id` | FK nullable | Activo |
| `model_version_id` | FK | Modelo usado |
| `input_payload` | JSON | Payload original |
| `feature_payload` | JSON | Features calculadas |
| `risk_level` | enum | `low`, `medium`, `high` |
| `failure_probability` | float | 0 a 1 |
| `recommendation` | string | recomendaciÃ³n |
| `created_at` | datetime | fecha |

Frase de operacion:

> Cada predicciÃ³n guarda la versiÃ³n exacta del modelo, el input y el output. Esto permite auditorÃ­a, trazabilidad, anÃ¡lisis de drift y rollback.

## Tabla `prediction_feedback`

| Campo | Tipo | DescripciÃ³n |
|---|---|---|
| `id` | UUID | ID feedback |
| `prediction_id` | FK | PredicciÃ³n evaluada |
| `real_failure` | bool | Si ocurriÃ³ fallo real |
| `corrected_risk_level` | enum nullable | CorrecciÃ³n humana |
| `comment` | text | ObservaciÃ³n |
| `created_at` | datetime | fecha |

Uso MLOps:

- Evaluar calidad real.
- Crear dataset de reentrenamiento.
- Medir drift.
- Mejorar modelo.

## Schemas Pydantic principales

### `SensorEventCreate`

```python
class SensorEventCreate(BaseModel):
    asset_code: str
    temperature: float = Field(..., ge=-50, le=250)
    pressure: float = Field(..., ge=0, le=500)
    vibration: float = Field(..., ge=0, le=50)
    flow_rate: float = Field(..., ge=0)
    energy_consumption: float = Field(..., ge=0)
    operating_hours: float = Field(..., ge=0)
    event_timestamp: datetime
```

### `PredictionRequest`

```python
class PredictionRequest(BaseModel):
    asset_code: str
    temperature: float
    pressure: float
    vibration: float
    flow_rate: float
    energy_consumption: float
    operating_hours: float
```

### `PredictionResponse`

```python
class PredictionResponse(BaseModel):
    prediction_id: UUID
    asset_code: str
    risk_level: Literal["low", "medium", "high"]
    failure_probability: float
    recommendation: str
    model_name: str
    model_version: str
    created_at: datetime
```

### `ModelVersionResponse`

```python
class ModelVersionResponse(BaseModel):
    id: UUID
    name: str
    version: str
    stage: Literal["staging", "production", "archived"]
    algorithm: str
    accuracy: float | None
    precision: float | None
    recall: float | None
    f1_score: float | None
    roc_auc: float | None
    created_at: datetime
```

## Dataset sintÃ©tico recomendado

Columnas CSV:

```csv
asset_code,asset_type,plant,temperature,pressure,vibration,flow_rate,energy_consumption,operating_hours,failure_next_7_days
PUMP-001,pump,refinery_a,91.2,7.8,0.82,120.3,430.1,5020,1
PUMP-002,pump,refinery_a,67.5,5.1,0.23,151.0,390.5,2201,0
```

Target:

- `failure_next_7_days`: 0/1

Regla sintÃ©tica posible:

```txt
Mayor riesgo si:
temperature > 85
pressure > 7
vibration > 0.7
operating_hours > 4000
energy_consumption alto
```

## Feature engineering mÃ­nimo

Features:

- `temperature`
- `pressure`
- `vibration`
- `flow_rate`
- `energy_consumption`
- `operating_hours`
- `temp_pressure_ratio`
- `vibration_per_hour`
- `energy_per_flow`

No complicar mÃ¡s.

## Ãndices recomendados

Para producciÃ³n:

- `users.email`
- `assets.asset_code`
- `sensor_events.asset_id`
- `sensor_events.event_timestamp`
- `predictions.created_at`
- `predictions.model_version_id`
- `model_versions.name_stage`
- `training_runs.status`


