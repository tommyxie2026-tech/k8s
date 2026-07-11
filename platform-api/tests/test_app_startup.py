from fastapi.testclient import TestClient

from app.main import app


def test_app_imports_and_health_endpoint_responds() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
