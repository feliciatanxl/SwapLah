"""API tests for application health."""

import pytest

import app.db as db_module
from app import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Create a Flask test client with an isolated health-check database."""
    test_db = tmp_path / "test_health.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client


def test_health_endpoint_returns_ok(client):
    """GET /api/health returns a simple healthy status."""
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
