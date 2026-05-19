import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.db import models  # noqa: F401
from app.core.auth_protection import login_failure_guard
from app.core.rate_limit import rate_limiter
from app.db.session import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    from app.main import app

    # Ensure the SQLite test database schema exists for every client instance.
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    rate_limiter._hits.clear()
    login_failure_guard._attempts.clear()


def _token_for(client: TestClient, email: str, role: str) -> str:
    password = "StrongPassword123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": password, "role": role})
    resp = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    return resp.json()["access_token"]


@pytest.fixture
def consumer_headers(client):
    token = _token_for(client, "consumer@example.com", "consumer")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def ml_engineer_headers(client):
    token = _token_for(client, "ml_engineer@example.com", "ml_engineer")
    return {"Authorization": f"Bearer {token}"}
