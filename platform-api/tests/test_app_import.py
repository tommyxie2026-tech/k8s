"""Application import smoke tests.

These tests provide the minimum safety net for structural refactoring. They do
not execute infrastructure commands or require access to a Kubernetes cluster.
"""


def test_fastapi_application_imports() -> None:
    from app.main import app

    assert app.title == "K8s Platform API"
    assert app.version


def test_health_route_is_registered() -> None:
    from app.main import app

    paths = {route.path for route in app.routes}
    assert "/health" in paths
