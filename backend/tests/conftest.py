import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app import models  # noqa: F401  (registers tables)
from app.database import get_session
from app.main import app


@pytest.fixture
def client():
    # Fresh in-memory database for every test, so tests never affect each other
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def make_user(client, email="alice@example.com", name="Alice", password="password123"):
    """Sign up + log in; return auth headers for that user."""
    r = client.post("/auth/signup", json={"email": email, "name": name, "password": password})
    assert r.status_code == 201, r.text
    r = client.post("/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
