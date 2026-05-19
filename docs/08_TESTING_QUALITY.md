# 08 - Testing y calidad

## Objetivo

Definir una estrategia realista de testing para explicar calidad sin invertir demasiado tiempo.

## PirÃ¡mide de testing

```txt
Muchos tests unitarios
Algunos tests de integraciÃ³n
Pocos tests end-to-end
```

## Herramientas

- pytest
- httpx / FastAPI TestClient
- ruff para lint
- coverage opcional
- pytest-cov opcional

## Tests P0

### Auth

1. Registrar usuario.
2. Login correcto.
3. Login incorrecto.
4. Acceso a endpoint protegido sin token devuelve 401.
5. Acceso con rol insuficiente devuelve 403.

### Predict

1. `/predict` con payload vÃ¡lido devuelve:
   - `prediction_id`
   - `risk_level`
   - `failure_probability`
   - `model_version`

2. `/predict` con payload invÃ¡lido devuelve 422.

3. PredicciÃ³n queda registrada en DB.

### Models

1. `/models/current` devuelve modelo actual.
2. `/models/train` requiere rol `ml_engineer` o `admin`.
3. Usuario `consumer` no puede entrenar.

### Health

1. `/health/live` responde 200.
2. `/health/ready` responde 200 si DB/modelo estÃ¡n listos.

## Estructura de tests

```txt
tests/
â”œâ”€â”€ conftest.py
â”œâ”€â”€ test_auth.py
â”œâ”€â”€ test_predictions.py
â”œâ”€â”€ test_models.py
â”œâ”€â”€ test_health.py
â””â”€â”€ test_permissions.py
```

## Fixtures recomendadas

```python
@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth_headers(client):
    # register/login user and return Authorization header
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers(client):
    return {"Authorization": f"Bearer {admin_token}"}
```

## Test de endpoint protegido

```python
def test_predict_requires_auth(client):
    response = client.post("/api/v1/predict", json={})
    assert response.status_code == 401
```

## Test de predicciÃ³n

```python
def test_predict_success(client, auth_headers):
    payload = {
        "asset_code": "PUMP-001",
        "temperature": 91.5,
        "pressure": 7.8,
        "vibration": 0.82,
        "flow_rate": 120.4,
        "energy_consumption": 430.2,
        "operating_hours": 5020
    }

    response = client.post(
        "/api/v1/predict",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "prediction_id" in data
    assert data["risk_level"] in ["low", "medium", "high"]
    assert 0 <= data["failure_probability"] <= 1
```

## Test de autorizaciÃ³n

```python
def test_consumer_cannot_train_model(client, consumer_headers):
    response = client.post(
        "/api/v1/models/train",
        json={"dataset_uri": "data/synthetic_sensor_data.csv"},
        headers=consumer_headers
    )
    assert response.status_code == 403
```

## Calidad de cÃ³digo

### Lint

```bash
ruff check app tests
```

### Formato

```bash
ruff format app tests
```

### Tests

```bash
pytest -q
```

### Coverage opcional

```bash
pytest --cov=app --cov-report=term-missing
```

## QuÃ© explicar en evaluacion

> He priorizado tests de seguridad, permisos e inferencia porque son los puntos crÃ­ticos. El pipeline ejecuta los tests antes de construir y desplegar la imagen, evitando que cÃ³digo roto llegue a AKS.

## Definition of Done

Una historia se considera terminada si:

- endpoint implementado
- validaciÃ³n Pydantic
- auth/roles aplicados
- persistencia si aplica
- test mÃ­nimo
- documentaciÃ³n OpenAPI clara
- sin secrets hardcodeados
- logs coherentes

## Testing en CI/CD

En PR:

```txt
install -> lint -> tests -> docker build
```

En merge a dev:

```txt
tests -> build image -> push ACR -> deploy dev
```

En main/prod:

```txt
tests -> build/promote image -> approval -> deploy prod
```

## Tests que NO son prioritarios para MVP

- carga/rendimiento
- caos
- seguridad avanzada
- contrato OpenAPI automatizado
- mutation testing
- e2e contra AKS real

## Tests Ãºtiles si sobra tiempo

- test de ML `build_features`
- test de `risk_level_from_probability`
- test de registry/promociÃ³n
- test de validaciÃ³n de dataset
- test de `SnowflakeClient` mockeado
- test de `DatabricksClient` mockeado


