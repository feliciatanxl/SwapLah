"""Unit tests for review submission and retrieval routes."""

# pylint: disable=redefined-outer-name

import pytest

import app as app_module
import app.db as db_module
from app import create_app


@pytest.fixture()
def client():
    """Create a Flask test client."""
    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client


def _login(client, user_id):
    """Set the logged-in user for a review request."""
    with client.session_transaction() as session:
        session["user_id"] = user_id


def _stub_completed_offer(monkeypatch, buyer_id=22, seller_id=11):
    """Stub one accepted offer and its listing owner."""
    monkeypatch.setattr(
        db_module,
        "get_offer_by_id",
        lambda offer_id: {
            "id": offer_id,
            "listing_id": 7,
            "buyer_id": buyer_id,
            "status": "Accepted",
        },
    )
    monkeypatch.setattr(db_module, "get_listing_owner", lambda listing_id: seller_id)
    monkeypatch.setattr(
        db_module,
        "get_user_rating_stats",
        lambda user_id: {"average_rating": 5.0, "review_count": 1},
    )


def _capture_created_review(monkeypatch):
    """Capture create_review arguments and return a representative review."""
    captured = {}

    def fake_create_review(**kwargs):
        captured.update(kwargs)
        return {"id": 1, **kwargs}

    monkeypatch.setattr(db_module, "create_review", fake_create_review)
    return captured


def test_seller_can_review_buyer_after_accepted_offer(client, monkeypatch):
    """An accepted offer's seller can review that offer's buyer."""
    _stub_completed_offer(monkeypatch)
    captured = _capture_created_review(monkeypatch)
    _login(client, 11)

    response = client.post("/api/reviews", json={"offer_id": 3, "rating": 5})

    assert response.status_code == 201
    assert captured == {
        "reviewer_id": 11,
        "reviewed_user_id": 22,
        "rating": 5,
        "comment": "",
    }


def test_buyer_can_still_review_seller(client, monkeypatch):
    """The existing buyer-to-seller review path remains available."""
    _stub_completed_offer(monkeypatch)
    captured = _capture_created_review(monkeypatch)
    _login(client, 22)

    response = client.post(
        "/api/reviews",
        json={"offer_id": 3, "reviewee_id": 11, "rating": 4, "comment": "Helpful"},
    )

    assert response.status_code == 201
    assert captured["reviewer_id"] == 22
    assert captured["reviewed_user_id"] == 11
    assert captured["comment"] == "Helpful"


@pytest.mark.parametrize("rating", [None, 0, 6, 2.5, True])
def test_review_rejects_invalid_rating(client, rating):
    """Ratings are required whole numbers from one to five."""
    _login(client, 11)

    response = client.post("/api/reviews", json={"offer_id": 3, "rating": rating})

    assert response.status_code == 400


def test_non_participant_cannot_review(client, monkeypatch):
    """Users outside the accepted transaction cannot review either party."""
    _stub_completed_offer(monkeypatch)
    _login(client, 99)

    response = client.post("/api/reviews", json={"offer_id": 3, "rating": 5})

    assert response.status_code == 403


def test_pending_offer_cannot_be_reviewed(client, monkeypatch):
    """A pending offer is not a completed transaction."""
    monkeypatch.setattr(
        db_module,
        "get_offer_by_id",
        lambda offer_id: {
            "id": offer_id,
            "listing_id": 7,
            "buyer_id": 22,
            "status": "Pending",
        },
    )
    _login(client, 11)

    response = client.post("/api/reviews", json={"offer_id": 3, "rating": 5})

    assert response.status_code == 400


def test_review_requires_login(client):
    """An unauthenticated request is rejected before validation runs."""
    response = client.post("/api/reviews", json={"offer_id": 3, "rating": 5})

    assert response.status_code == 401


def test_review_rejects_missing_offer(client, monkeypatch):
    """A review for an offer ID that does not exist is rejected."""
    monkeypatch.setattr(db_module, "get_offer_by_id", lambda offer_id: None)
    _login(client, 11)

    response = client.post("/api/reviews", json={"offer_id": 999, "rating": 5})

    assert response.status_code == 404


def test_review_rejects_reviewee_not_matching_counterparty(client, monkeypatch):
    """An explicit reviewee_id that is not the transaction counterparty is rejected."""
    _stub_completed_offer(monkeypatch)
    _login(client, 11)

    response = client.post(
        "/api/reviews", json={"offer_id": 3, "reviewee_id": 999, "rating": 5}
    )

    assert response.status_code == 400


def _reviews_client(monkeypatch, reviews=None, user_exists=True):
    """Create a test client with review retrieval DB helpers monkeypatched."""
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
    client = _reviews_client(monkeypatch, reviews=reviews)

    response = client.get("/api/users/1/reviews")

    assert response.status_code == 200
    assert response.get_json() == {"reviews": reviews}


def test_get_user_reviews_returns_empty_list(monkeypatch):
    """Existing users with no reviews receive an empty review list."""
    client = _reviews_client(monkeypatch)

    response = client.get("/api/users/1/reviews")

    assert response.status_code == 200
    assert response.get_json() == {"reviews": []}


def test_get_user_reviews_returns_404_for_missing_user(monkeypatch):
    """Unknown users receive a JSON 404 response."""
    client = _reviews_client(monkeypatch, user_exists=False)

    response = client.get("/api/users/999/reviews")

    assert response.status_code == 404
    assert response.get_json() == {"error": "User not found."}


def test_get_user_reviews_rejects_invalid_user_id(monkeypatch):
    """Non-integer user IDs do not match the route."""
    client = _reviews_client(monkeypatch)

    response = client.get("/api/users/not-a-number/reviews")

    assert response.status_code == 404
