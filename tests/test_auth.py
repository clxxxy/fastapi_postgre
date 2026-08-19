from fastapi.testclient import TestClient


def test_register_login_and_read_profile(client: TestClient) -> None:
    registration = client.post(
        "/auth/register",
        json={"name": "Ada Lovelace", "email": "ada@example.com", "password": "senha-segura"},
    )
    login = client.post(
        "/auth/login", data={"username": "ada@example.com", "password": "senha-segura"}
    )
    profile = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"}
    )

    assert registration.status_code == 201
    assert "password_hash" not in registration.json()
    assert login.status_code == 200
    assert profile.status_code == 200
    assert profile.json()["email"] == "ada@example.com"


def test_duplicate_email_and_invalid_credentials_are_rejected(client: TestClient) -> None:
    payload = {"name": "Grace Hopper", "email": "grace@example.com", "password": "senha-segura"}
    assert client.post("/auth/register", json=payload).status_code == 201

    duplicate = client.post("/auth/register", json=payload)
    login = client.post(
        "/auth/login", data={"username": payload["email"], "password": "senha-incorreta"}
    )

    assert duplicate.status_code == 409
    assert login.status_code == 401