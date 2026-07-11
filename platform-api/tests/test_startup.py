from app.main import app


def test_platform_api_app_imports() -> None:
    assert app.title == "K8s Platform API"
    assert app.version == "0.2.0"


def test_platform_api_has_expected_routers() -> None:
    routes = {getattr(route, "path", "") for route in app.routes}

    assert "/health/" in routes
    assert any(path.startswith("/api/v1/workflows") for path in routes)
    assert any(path.startswith("/api/v1/jobs") for path in routes)
