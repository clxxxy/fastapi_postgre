from fastapi.testclient import TestClient


def authenticated_headers(client: TestClient, email: str) -> dict[str, str]:
    password = "senha-segura"
    client.post(
        "/auth/register",
        json={"name": "Test User", "email": email, "password": password},
    )
    login = client.post("/auth/login", data={"username": email, "password": password})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_task_write_lifecycle(client: TestClient) -> None:
    headers = authenticated_headers(client, "owner@example.com")

    created = client.post(
        "/tasks",
        headers=headers,
        json={"title": "Preparar apresentacao", "description": "Demonstrar o fluxo completo"},
    )
    task_id = created.json()["id"]
    updated = client.patch(
        f"/tasks/{task_id}",
        headers=headers,
        json={"title": "Apresentar projeto", "is_completed": True},
    )
    listed = client.get("/tasks?completed=true", headers=headers)
    deleted = client.delete(f"/tasks/{task_id}", headers=headers)
    missing = client.get(f"/tasks/{task_id}", headers=headers)

    assert created.status_code == 201
    assert updated.status_code == 200
    assert updated.json()["is_completed"] is True
    assert [task["id"] for task in listed.json()] == [task_id]
    assert deleted.status_code == 204
    assert missing.status_code == 404


def test_tasks_require_authentication(client: TestClient) -> None:
    assert client.get("/tasks").status_code == 401
    assert client.post("/tasks", json={"title": "Privada"}).status_code == 401


def test_user_cannot_read_update_or_delete_another_users_task(client: TestClient) -> None:
    owner_headers = authenticated_headers(client, "first@example.com")
    other_headers = authenticated_headers(client, "second@example.com")
    task = client.post("/tasks", headers=owner_headers, json={"title": "Somente minha"})
    task_id = task.json()["id"]

    assert client.get(f"/tasks/{task_id}", headers=other_headers).status_code == 404
    assert (
        client.patch(
            f"/tasks/{task_id}", headers=other_headers, json={"is_completed": True}
        ).status_code
        == 404
    )
    assert client.delete(f"/tasks/{task_id}", headers=other_headers).status_code == 404