
"""API tests use a temporary SQLite database."""

import pytest
from fastapi.testclient import TestClient
import main


@pytest.fixture(autouse=True)
def use_temporary_database(tmp_path, monkeypatch):
    test_db = tmp_path / "tasks.db"
    monkeypatch.setattr(main, "DB_PATH", test_db)


def test_create_and_get_task():
    with TestClient(main.app) as client:
        response = client.post(
            "/tasks",
            json={"title": "  Prepare resume  ", "description": " SDE role "},
        )
        assert response.status_code == 201

        task = response.json()
        assert task["title"] == "Prepare resume"
        assert task["description"] == "SDE role"
        assert task["completed"] is False

        fetched = client.get(f"/tasks/{task['id']}")
        assert fetched.status_code == 200
        assert fetched.json() == task


def test_validation_rejects_blank_title():
    with TestClient(main.app) as client:
        response = client.post("/tasks", json={"title": "   "})
        assert response.status_code == 422


def test_update_and_filter_tasks():
    with TestClient(main.app) as client:
        task = client.post(
            "/tasks", json={"title": "Study DSA"}
        ).json()

        updated = client.patch(
            f"/tasks/{task['id']}", json={"completed": True}
        )
        assert updated.status_code == 200
        assert updated.json()["completed"] is True

        assert len(
            client.get("/tasks", params={"completed": True}).json()
        ) == 1

        assert client.get(
            "/tasks", params={"completed": False}
        ).json() == []


def test_missing_task_returns_404():
    with TestClient(main.app) as client:
        assert client.get("/tasks/999").status_code == 404
        assert client.patch(
            "/tasks/999", json={"completed": True}
        ).status_code == 404
        assert client.delete("/tasks/999").status_code == 404


def test_delete_task():
    with TestClient(main.app) as client:
        task = client.post(
            "/tasks", json={"title": "Delete me"}
        ).json()

        response = client.delete(f"/tasks/{task['id']}")
        assert response.status_code == 204
        assert client.get(f"/tasks/{task['id']}").status_code == 404
