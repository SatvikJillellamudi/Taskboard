import os

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app import models  # noqa: F401  (registers tables)
from app.config import normalize_db_url
from app.database import enforce_sqlite_foreign_keys, get_session
from app.main import app


@pytest.fixture
def client():
    # Fresh database for every test, so tests never affect each other.
    # Default: in-memory SQLite. Set TEST_DATABASE_URL to run the same tests against Postgres.
    pg_url = os.getenv("TEST_DATABASE_URL")
    if pg_url:
        engine = create_engine(normalize_db_url(pg_url))
        SQLModel.metadata.drop_all(engine)
    else:
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                               poolclass=StaticPool)
        enforce_sqlite_foreign_keys(engine)
    SQLModel.metadata.create_all(engine)

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    engine.dispose()


def make_user(client, email="alice@example.com", name="Alice", password="password123"):
    """Sign up + log in; return auth headers for that user."""
    r = client.post("/auth/signup", json={"email": email, "name": name, "password": password})
    assert r.status_code == 201, r.text
    r = client.post("/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
