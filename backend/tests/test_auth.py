from tests.conftest import make_user


def test_signup_and_me(client):
    headers = make_user(client)
    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == "alice@example.com"
    assert "hashed_password" not in r.json()  # never leak the hash


def test_duplicate_email_rejected(client):
    make_user(client)
    r = client.post("/auth/signup", json={"email": "ALICE@example.com", "name": "A2",
                                          "password": "password123"})
    assert r.status_code == 409  # emails are case-insensitive


def test_wrong_password(client):
    make_user(client)
    r = client.post("/auth/login", data={"username": "alice@example.com", "password": "wrongpass1"})
    assert r.status_code == 401


def test_short_password_rejected(client):
    r = client.post("/auth/signup", json={"email": "b@example.com", "name": "B", "password": "short"})
    assert r.status_code == 422


def test_protected_route_requires_token(client):
    assert client.get("/boards").status_code == 401
    assert client.get("/boards", headers={"Authorization": "Bearer garbage"}).status_code == 401
