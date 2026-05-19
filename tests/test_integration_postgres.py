import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from app.db import models  # noqa: F401
from app.db.models import Prediction, User
from app.db.session import Base, get_db

POSTGRES_TEST_URL = os.getenv(
    "POSTGRES_TEST_DATABASE_URL",
    "postgresql+psycopg2://energypredict:energypredict@localhost:5432/energypredict",
)


def _postgres_engine_or_skip():
    try:
        engine = create_engine(POSTGRES_TEST_URL, future=True)
    except ModuleNotFoundError:
        pytest.skip("psycopg2 not installed. Install requirements to run PostgreSQL integration tests.")
    try:
        with engine.connect() as conn:
            conn.execute(User.__table__.select().limit(1))
    except OperationalError:
        pytest.skip("PostgreSQL not available. Start docker compose for integration tests.")
    return engine


@pytest.fixture
def pg_client():
    engine = _postgres_engine_or_skip()
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    from app.main import app

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, TestingSessionLocal
    app.dependency_overrides.clear()


@pytest.mark.integration
def test_postgres_register_persists_user(pg_client):
    client, SessionLocal = pg_client

    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "pg_user@example.com", "password": "StrongPassword123!", "role": "consumer"},
    )
    assert resp.status_code == 201

    with SessionLocal() as db:
        saved = db.query(User).filter(User.email == "pg_user@example.com").first()
        assert saved is not None


@pytest.mark.integration
def test_postgres_predict_persists_prediction(pg_client):
    client, SessionLocal = pg_client

    client.post(
        "/api/v1/auth/register",
        json={"email": "pg_predict@example.com", "password": "StrongPassword123!", "role": "consumer"},
    )
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "pg_predict@example.com", "password": "StrongPassword123!"},
    )
    token = login.json()["access_token"]

    payload = {
        "asset_code": "PUMP-001",
        "temperature": 91.5,
        "pressure": 7.8,
        "vibration": 0.82,
        "flow_rate": 120.4,
        "energy_consumption": 430.2,
        "operating_hours": 5020,
    }
    resp = client.post("/api/v1/predict", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    with SessionLocal() as db:
        count = db.query(Prediction).count()
        assert count == 1
