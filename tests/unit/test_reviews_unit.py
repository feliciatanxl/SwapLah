"""Unit tests for user review retrieval routes."""

import app.db as db_module
import app as app_module


def _client(monkeypatch, reviews=None, user_exists=True):
    """Create a test client with review DB helpers monkeypatched."""
    monkeypatch.setattr(
        db_module,
        "get_user_by_id",
        lambda user_id: {"id": user_id} if user_exists else None,
    )
    monkeypatch.setattr(db_module, "get_reviews_for_user", lambda _user_id: reviews or [])
    monkeypatch.setattr(app_module, "init_db", lambda: None)

    flask_app = app_module.create_app()
    flask_app.config["TESTING"] = True
    return flask_app.test_client()


def test_get_user_reviews_returns_reviews(monkeypatch):
    """Existing users receive their review list."""
    reviews = [{"id": 1, "rating": 5, "comment": "Reliable campus seller."}]
    client = _client(monkeypatch, reviews=reviews)

    response = client.get("/api/users/1/reviews")

    assert response.status_code == 200
    assert response.get_json() == {"reviews": reviews}


def test_get_user_reviews_returns_empty_list(monkeypatch):
    """Existing users with no reviews receive an empty review list."""
    client = _client(monkeypatch)

    response = client.get("/api/users/1/reviews")

    assert response.status_code == 200
    assert response.get_json() == {"reviews": []}


def test_get_user_reviews_returns_404_for_missing_user(monkeypatch):
    """Unknown users receive a JSON 404 response."""
    client = _client(monkeypatch, user_exists=False)

    response = client.get("/api/users/999/reviews")

    assert response.status_code == 404
    assert response.get_json() == {"error": "User not found."}


def test_get_user_reviews_rejects_invalid_user_id(monkeypatch):
    """Non-integer user IDs do not match the route."""
    client = _client(monkeypatch)

    response = client.get("/api/users/not-a-number/reviews")

    assert response.status_code == 404
