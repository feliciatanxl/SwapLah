"""
Unit tests for:
  POST /api/reviews

All DB calls are monkeypatched — no real database needed.
"""
import pytest

from app import create_app
from app.routes import reviews as reviews_routes


@pytest.fixture
def client():
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def login_as(client, user_id):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


FAKE_ACCEPTED_OFFER = {
    "id": 1,
    "listing_id": 10,
    "buyer_id": 2,
    "offer_type": "cash",
    "proposed_price": 20.0,
    "swap_listing_id": None,
    "status": "Accepted",
    "created_at": "2026-06-09 10:00:00",
}

FAKE_PENDING_OFFER = {**FAKE_ACCEPTED_OFFER, "status": "Pending"}
FAKE_REJECTED_OFFER = {**FAKE_ACCEPTED_OFFER, "status": "Rejected"}

FAKE_CREATED_REVIEW = {
    "id": 99,
    "reviewer_id": 2,
    "reviewed_user_id": 1,
    "rating": 5,
    "comment": "Prompt payment, smooth handover.",
    "created_at": "2026-06-09 10:05:00",
}

FAKE_STATS = {"average_rating": 5.0, "review_count": 1}


# ===========================================================================
# AC1: valid rating (+ optional comment) is saved for the seller
# ===========================================================================

def test_submit_review_success_with_comment(client, monkeypatch):
    """A buyer submits a rating and comment for an accepted offer -> 201."""
    login_as(client, 2)
    monkeypatch.setattr(reviews_routes.db_module, "get_offer_by_id", lambda oid: FAKE_ACCEPTED_OFFER)
    monkeypatch.setattr(reviews_routes.db_module, "get_listing_owner", lambda lid: 1)
    monkeypatch.setattr(reviews_routes.db_module, "create_review", lambda **kw: FAKE_CREATED_REVIEW)
    monkeypatch.setattr(reviews_routes.db_module, "get_user_rating_stats", lambda uid: FAKE_STATS)

    resp = client.post(
        "/api/reviews",
        json={"offer_id": 1, "rating": 5, "comment": "Prompt payment, smooth handover."},
    )

    assert resp.status_code == 201
    data = resp.get_json()
    assert data["review"]["rating"] == 5
    assert data["average_rating"] == 5.0
    assert data["review_count"] == 1


def test_submit_review_success_without_comment(client, monkeypatch):
    """Comment is optional."""
    login_as(client, 2)
    monkeypatch.setattr(reviews_routes.db_module, "get_offer_by_id", lambda oid: FAKE_ACCEPTED_OFFER)
    monkeypatch.setattr(reviews_routes.db_module, "get_listing_owner", lambda lid: 1)
    monkeypatch.setattr(reviews_routes.db_module, "get_user_rating_stats", lambda uid: FAKE_STATS)

    captured = {}

    def fake_create_review(**kwargs):
        captured.update(kwargs)
        return {**FAKE_CREATED_REVIEW, "comment": ""}

    monkeypatch.setattr(reviews_routes.db_module, "create_review", fake_create_review)

    resp = client.post("/api/reviews", json={"offer_id": 1, "rating": 4})

    assert resp.status_code == 201
    assert captured["comment"] == ""
    assert captured["reviewer_id"] == 2
    assert captured["reviewed_user_id"] == 1


# ===========================================================================
# AC2: transaction is not completed
# ===========================================================================

def test_submit_review_rejects_missing_offer(client, monkeypatch):
    """A non-existent offer_id -> 404."""
    login_as(client, 2)
    monkeypatch.setattr(reviews_routes.db_module, "get_offer_by_id", lambda oid: None)

    resp = client.post("/api/reviews", json={"offer_id": 999, "rating": 5})

    assert resp.status_code == 404
    assert "error" in resp.get_json()


def test_submit_review_rejects_pending_offer(client, monkeypatch):
    """A Pending offer is not yet a completed transaction -> 400."""
    login_as(client, 2)
    monkeypatch.setattr(reviews_routes.db_module, "get_offer_by_id", lambda oid: FAKE_PENDING_OFFER)

    resp = client.post("/api/reviews", json={"offer_id": 1, "rating": 5})

    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_submit_review_rejects_rejected_offer(client, monkeypatch):
    """A Rejected offer is not a completed transaction -> 400."""
    login_as(client, 2)
    monkeypatch.setattr(reviews_routes.db_module, "get_offer_by_id", lambda oid: FAKE_REJECTED_OFFER)

    resp = client.post("/api/reviews", json={"offer_id": 1, "rating": 5})

    assert resp.status_code == 400


# ===========================================================================
# AC3: review is linked to the seller of the transaction
# ===========================================================================

def test_submit_review_links_to_listing_seller(client, monkeypatch):
    """create_review() is called with the listing's actual seller as reviewed_user_id."""
    login_as(client, 2)
    monkeypatch.setattr(reviews_routes.db_module, "get_offer_by_id", lambda oid: FAKE_ACCEPTED_OFFER)
    monkeypatch.setattr(reviews_routes.db_module, "get_listing_owner", lambda lid: 1)
    monkeypatch.setattr(reviews_routes.db_module, "get_user_rating_stats", lambda uid: FAKE_STATS)

    captured = {}

    def fake_create_review(**kwargs):
        captured.update(kwargs)
        return FAKE_CREATED_REVIEW

    monkeypatch.setattr(reviews_routes.db_module, "create_review", fake_create_review)

    client.post("/api/reviews", json={"offer_id": 1, "rating": 5})

    assert captured["reviewed_user_id"] == 1


def test_submit_review_rejects_mismatched_reviewee_id(client, monkeypatch):
    """A reviewee_id that does not match the listing's seller -> 400."""
    login_as(client, 2)
    monkeypatch.setattr(reviews_routes.db_module, "get_offer_by_id", lambda oid: FAKE_ACCEPTED_OFFER)
    monkeypatch.setattr(reviews_routes.db_module, "get_listing_owner", lambda lid: 1)

    resp = client.post("/api/reviews", json={"offer_id": 1, "rating": 5, "reviewee_id": 999})

    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_submit_review_accepts_matching_reviewee_id(client, monkeypatch):
    """An explicit reviewee_id that matches the listing's seller is accepted."""
    login_as(client, 2)
    monkeypatch.setattr(reviews_routes.db_module, "get_offer_by_id", lambda oid: FAKE_ACCEPTED_OFFER)
    monkeypatch.setattr(reviews_routes.db_module, "get_listing_owner", lambda lid: 1)
    monkeypatch.setattr(reviews_routes.db_module, "create_review", lambda **kw: FAKE_CREATED_REVIEW)
    monkeypatch.setattr(reviews_routes.db_module, "get_user_rating_stats", lambda uid: FAKE_STATS)

    resp = client.post("/api/reviews", json={"offer_id": 1, "rating": 5, "reviewee_id": 1})

    assert resp.status_code == 201


def test_submit_review_rejects_when_listing_not_found(client, monkeypatch):
    """A listing that no longer exists (owner lookup returns None) -> 404."""
    login_as(client, 2)
    monkeypatch.setattr(reviews_routes.db_module, "get_offer_by_id", lambda oid: FAKE_ACCEPTED_OFFER)
    monkeypatch.setattr(reviews_routes.db_module, "get_listing_owner", lambda lid: None)

    resp = client.post("/api/reviews", json={"offer_id": 1, "rating": 5})

    assert resp.status_code == 404


# ===========================================================================
# AC4: rating outside 1-5, or non-integer, is rejected
# ===========================================================================

@pytest.mark.parametrize("bad_rating", [0, 6, -1, 4.5, "five", True, None])
def test_submit_review_rejects_invalid_rating(client, monkeypatch, bad_rating):
    """Invalid ratings never reach create_review()."""
    login_as(client, 2)

    def fail_if_called(oid):
        raise AssertionError("get_offer_by_id() must not be called for an invalid rating")

    monkeypatch.setattr(reviews_routes.db_module, "get_offer_by_id", fail_if_called)

    resp = client.post("/api/reviews", json={"offer_id": 1, "rating": bad_rating})

    assert resp.status_code == 400


def test_submit_review_rejects_missing_body(client):
    """A request with no JSON body at all is rejected, not a 500."""
    login_as(client, 2)

    resp = client.post("/api/reviews")

    assert resp.status_code == 400


# ===========================================================================
# AC5: only the buyer of the completed offer may submit the review
# ===========================================================================

def test_submit_review_rejects_seller_of_same_offer(client, monkeypatch):
    """The seller is not the buyer of this offer -> 403."""
    login_as(client, 1)  # seller_id, not buyer_id (2) of FAKE_ACCEPTED_OFFER
    monkeypatch.setattr(reviews_routes.db_module, "get_offer_by_id", lambda oid: FAKE_ACCEPTED_OFFER)

    resp = client.post("/api/reviews", json={"offer_id": 1, "rating": 5})

    assert resp.status_code == 403
    assert "error" in resp.get_json()


def test_submit_review_rejects_unrelated_user(client, monkeypatch):
    """A user unrelated to the offer -> 403."""
    login_as(client, 999)
    monkeypatch.setattr(reviews_routes.db_module, "get_offer_by_id", lambda oid: FAKE_ACCEPTED_OFFER)

    resp = client.post("/api/reviews", json={"offer_id": 1, "rating": 5})

    assert resp.status_code == 403


def test_submit_review_rejects_unauthenticated(client):
    """Unauthenticated request -> 401, before any DB lookup."""
    resp = client.post("/api/reviews", json={"offer_id": 1, "rating": 5})

    assert resp.status_code == 401
