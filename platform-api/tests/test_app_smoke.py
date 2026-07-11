from fastapi.testclient import TestClient

from app.main import app


def test_platform_api_imports_and_health_endpoint_works() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["app"] == "k8s-platform-api"
    assert "version" in payload
