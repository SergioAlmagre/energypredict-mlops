# 04 - EspecificaciÃ³n de API

## Convenciones

Base path:

```txt
/api/v1
```

Formato:

- JSON.
- Fechas en ISO-8601.
- Auth vÃ­a `Authorization: Bearer <token>`.
- Errores con estructura consistente.

## Estructura estÃ¡ndar de error

```json
{
  "detail": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or expired token",
    "request_id": "req_123"
  }
}
```

## Roles

| Rol | Capacidades |
|---|---|
| `consumer` | Consumir predicciones |
| `analyst` | Ver predicciones y feedback |
| `ml_engineer` | Entrenar modelos y ver mÃ©tricas |
| `admin` | Todo, incluyendo promociÃ³n de modelos |

## Health

### `GET /health/live`

Uso: liveness probe.

Respuesta:

```json
{
  "status": "ok",
  "service": "energypredict-api"
}
```

### `GET /health/ready`

Uso: readiness probe.

Debe comprobar:

- conexiÃ³n DB
- modelo cargado o registry accesible
- configuraciÃ³n bÃ¡sica

Respuesta:

```json
{
  "status": "ready",
  "database": "ok",
  "model": "ok"
}
```

## Auth

### `POST /auth/register`

Roles permitidos:

- pÃºblico para demo
- en producciÃ³n deberÃ­a estar restringido o gestionado por IAM

Request:

```json
{
  "email": "analyst@example.com",
  "password": "StrongPassword123!",
  "role": "analyst"
}
```

Respuesta:

```json
{
  "id": "11111111-1111-1111-1111-111111111111",
  "email": "analyst@example.com",
  "role": "analyst",
  "is_active": true
}
```

Validaciones:

- email vÃ¡lido
- password mÃ­nimo 8-12 caracteres
- role vÃ¡lido
- email Ãºnico

### `POST /auth/login`

Request OAuth2 password flow o JSON.

RecomendaciÃ³n demo simple: usar OAuth2PasswordRequestForm para integrarse bien con Swagger.

Respuesta:

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### `GET /auth/me`

Auth: cualquier usuario autenticado.

Respuesta:

```json
{
  "id": "11111111-1111-1111-1111-111111111111",
  "email": "analyst@example.com",
  "role": "analyst"
}
```

## Assets

### `POST /assets`

Roles: `analyst`, `ml_engineer`, `admin`

Request:

```json
{
  "asset_code": "PUMP-001",
  "asset_type": "pump",
  "plant": "refinery_a",
  "location": "unit_3",
  "criticality": "high"
}
```

Respuesta:

```json
{
  "id": "22222222-2222-2222-2222-222222222222",
  "asset_code": "PUMP-001",
  "asset_type": "pump",
  "plant": "refinery_a",
  "location": "unit_3",
  "criticality": "high",
  "created_at": "2026-05-16T10:00:00Z"
}
```

### `GET /assets`

Roles: `analyst`, `ml_engineer`, `admin`

Query params:

- `asset_type`
- `plant`
- `criticality`
- `limit`
- `offset`

## Ingestion

### `POST /ingestion/sensor-events`

Roles: `analyst`, `ml_engineer`, `admin`

Request:

```json
{
  "asset_code": "PUMP-001",
  "temperature": 91.5,
  "pressure": 7.8,
  "vibration": 0.82,
  "flow_rate": 120.4,
  "energy_consumption": 430.2,
  "operating_hours": 5020,
  "event_timestamp": "2026-05-16T09:30:00Z"
}
```

Respuesta:

```json
{
  "id": "33333333-3333-3333-3333-333333333333",
  "asset_code": "PUMP-001",
  "received_at": "2026-05-16T09:31:00Z"
}
```

### `POST /ingestion/batch`

Roles: `ml_engineer`, `admin`

Uso:

- demo: cargar CSV local
- producciÃ³n: registrar batch a procesar en Databricks

Request:

```json
{
  "source_type": "csv",
  "source_uri": "data/synthetic_sensor_data.csv",
  "description": "Initial training dataset"
}
```

Respuesta:

```json
{
  "dataset_id": "dataset_001",
  "status": "registered",
  "source_type": "csv"
}
```

## Predictions

### `POST /predict`

Roles: `consumer`, `analyst`, `ml_engineer`, `admin`

Request:

```json
{
  "asset_code": "PUMP-001",
  "temperature": 91.5,
  "pressure": 7.8,
  "vibration": 0.82,
  "flow_rate": 120.4,
  "energy_consumption": 430.2,
  "operating_hours": 5020
}
```

Respuesta:

```json
{
  "prediction_id": "44444444-4444-4444-4444-444444444444",
  "asset_code": "PUMP-001",
  "risk_level": "high",
  "failure_probability": 0.87,
  "recommendation": "Inspect asset within 24 hours and review vibration trend.",
  "model_name": "asset_failure_classifier",
  "model_version": "1.0.0",
  "created_at": "2026-05-16T10:05:00Z"
}
```

LÃ³gica de riesgo:

```txt
probability < 0.35 => low
0.35 <= probability < 0.70 => medium
probability >= 0.70 => high
```

### `POST /predict/batch`

Roles: `analyst`, `ml_engineer`, `admin`

Request:

```json
{
  "items": [
    {
      "asset_code": "PUMP-001",
      "temperature": 91.5,
      "pressure": 7.8,
      "vibration": 0.82,
      "flow_rate": 120.4,
      "energy_consumption": 430.2,
      "operating_hours": 5020
    }
  ]
}
```

Respuesta:

```json
{
  "count": 1,
  "predictions": [
    {
      "prediction_id": "44444444-4444-4444-4444-444444444444",
      "risk_level": "high",
      "failure_probability": 0.87
    }
  ]
}
```

### `GET /predictions`

Roles: `analyst`, `ml_engineer`, `admin`

Query params:

- `asset_code`
- `risk_level`
- `model_version`
- `from_date`
- `to_date`
- `limit`
- `offset`

Respuesta:

```json
{
  "items": [],
  "total": 0,
  "limit": 50,
  "offset": 0
}
```

### `GET /predictions/{prediction_id}`

Roles: `analyst`, `ml_engineer`, `admin`

Respuesta incluye:

- input
- output
- modelo
- usuario
- feedback si existe

## Feedback

### `POST /predictions/{prediction_id}/feedback`

Roles: `analyst`, `ml_engineer`, `admin`

Request:

```json
{
  "real_failure": true,
  "corrected_risk_level": "high",
  "comment": "Asset failed two days after prediction."
}
```

Respuesta:

```json
{
  "feedback_id": "55555555-5555-5555-5555-555555555555",
  "prediction_id": "44444444-4444-4444-4444-444444444444",
  "status": "created"
}
```

Notas:

> Este endpoint cierra el loop MLOps: las predicciones se contrastan con resultado real y se usan para reentrenar.

## Models

### `GET /models`

Roles: `analyst`, `ml_engineer`, `admin`

Respuesta:

```json
{
  "items": [
    {
      "id": "66666666-6666-6666-6666-666666666666",
      "name": "asset_failure_classifier",
      "version": "1.0.0",
      "stage": "production",
      "algorithm": "RandomForestClassifier",
      "accuracy": 0.91,
      "precision": 0.88,
      "recall": 0.84,
      "f1_score": 0.86,
      "roc_auc": 0.93,
      "created_at": "2026-05-16T10:00:00Z"
    }
  ]
}
```

### `GET /models/current`

Roles: cualquier usuario autenticado.

Respuesta:

```json
{
  "name": "asset_failure_classifier",
  "version": "1.0.0",
  "stage": "production",
  "artifact_uri": "models/asset_failure_classifier_1.0.0.pkl"
}
```

### `POST /models/train`

Roles: `ml_engineer`, `admin`

Request:

```json
{
  "dataset_uri": "data/synthetic_sensor_data.csv",
  "algorithm": "RandomForestClassifier",
  "parameters": {
    "n_estimators": 100,
    "max_depth": 6,
    "random_state": 42
  },
  "register_model": true
}
```

Respuesta sÃ­ncrona para demo:

```json
{
  "run_id": "77777777-7777-7777-7777-777777777777",
  "status": "completed",
  "model_version": "1.0.1",
  "metrics": {
    "accuracy": 0.91,
    "precision": 0.88,
    "recall": 0.84,
    "f1_score": 0.86,
    "roc_auc": 0.93
  }
}
```

Respuesta asÃ­ncrona productiva:

```json
{
  "run_id": "77777777-7777-7777-7777-777777777777",
  "status": "pending",
  "message": "Training job submitted to Databricks"
}
```

### `GET /models/runs`

Roles: `ml_engineer`, `admin`

Lista ejecuciones.

### `GET /models/runs/{run_id}`

Roles: `ml_engineer`, `admin`

Detalle de ejecuciÃ³n.

### `POST /models/{model_id}/promote`

Roles: `admin`

Request:

```json
{
  "target_stage": "production",
  "reason": "Model has better recall and passed validation threshold."
}
```

Respuesta:

```json
{
  "model_id": "66666666-6666-6666-6666-666666666666",
  "stage": "production",
  "promoted_at": "2026-05-16T11:00:00Z"
}
```

Regla:

- Archivar modelo production anterior.
- Promocionar nuevo.
- Guardar evento/auditorÃ­a.

### `POST /models/{model_id}/archive`

Roles: `admin`

Archiva versiÃ³n.

## MÃ©tricas opcionales

### `GET /metrics`

Para Prometheus.

Ejemplos:

```txt
http_requests_total
prediction_requests_total
prediction_latency_seconds
model_version_info
```

## CÃ³digos HTTP esperados

| CÃ³digo | Caso |
|---|---|
| 200 | OK |
| 201 | Creado |
| 202 | Job aceptado |
| 400 | Payload invÃ¡lido o regla de negocio |
| 401 | No autenticado |
| 403 | Sin rol necesario |
| 404 | Recurso no encontrado |
| 409 | Conflicto, por ejemplo email duplicado |
| 422 | ValidaciÃ³n Pydantic |
| 500 | Error interno |
| 503 | Dependencia no lista |

