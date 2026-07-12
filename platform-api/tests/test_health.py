from fastapi.testclient import TestClient


def test_health_endpoint_returns_application_status(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["app"]
    assert payload["version"]
