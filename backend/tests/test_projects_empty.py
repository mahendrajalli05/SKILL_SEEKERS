from __future__ import annotations


def test_projects_list_is_empty_without_seed_data(client) -> None:
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0


def test_missing_project_returns_structured_404(client) -> None:
    response = client.get("/api/v1/projects/1")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "not_found"
    assert "fraud" not in body["error"]["message"].lower()
