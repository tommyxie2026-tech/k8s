from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """Provide an isolated FastAPI test client for API tests."""
    with TestClient(app) as test_client:
        yield test_client
