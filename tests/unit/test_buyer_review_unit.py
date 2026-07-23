"""
Unit tests for:
  POST /api/transactions/<id>/buyer-review

All DB calls are monkeypatched — no real database needed. Mirrors
test_seller_review_unit.py but for the buyer reviewing the seller.
"""
import pytest

from app import create_app
import app.db as db_module


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def login_as(client, user_id):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

FAKE_TRANSACTION = {
    "id": 1,
    "offer_id": 10,
    "listing_id": 20,
    "seller_id": 1,
    "buyer_id": 2,
    "transaction_type": "cash",
    "amount": 25.0,
    "swap_listing_id": None,
    "created_at": "2026-06-09 10:00:00",
}

FAKE_CREATED_REVIEW = {
    "id": 99,
    "transaction_id": 1,
    "reviewer_id": 2,
    "reviewed_user_id": 1,
    "rating": 5,
    "comment": "Item exactly as described.",
    "created_at": "2026-06-09 10:05:00",
}


# ===========================================================================
# AC1: valid rating (+ optional comment) is saved for the seller
# ===========================================================================

def test_buyer_review_success_with_comment(client, monkeypatch):
    """AC1: buyer submits a rating and comment -> 201 with the created review."""
    login_as(client, 2)
    monkeypatch.setattr(db_module, "get_transaction_by_id", lambda tid: FAKE_TRANSACTION)
    monkeypatch.setattr(db_module, "create_review", lambda **kw: FAKE_CREATED_REVIEW)

    resp = client.post(
        "/api/transactions/1/buyer-review",
        json={"rating": 5, "comment": "Item exactly as described."},
    )

    assert resp.status_code == 201
    data = resp.get_json()
    assert data["review"]["rating"] == 5
    assert data["review"]["comment"] == "Item exactly as described."
    assert data["review"]["reviewedUserId"] == 1
    assert data["review"]["reviewerId"] == 2
    assert data["review"]["transactionId"] == 1


def test_buyer_review_success_without_comment(client, monkeypatch):
    """AC1: comment is optional."""
    login_as(client, 2)
    monkeypatch.setattr(db_module, "get_transaction_by_id", lambda tid: FAKE_TRANSACTION)

    captured = {}

    def fake_create_review(**kwargs):
        captured.update(kwargs)
        return {**FAKE_CREATED_REVIEW, "comment": ""}

    monkeypatch.setattr(db_module, "create_review", fake_create_review)

    resp = client.post("/api/transactions/1/buyer-review", json={"rating": 4})

    assert resp.status_code == 201
    assert captured["comment"] == ""
    assert captured["rating"] == 4
    assert captured["transaction_id"] == 1
    assert captured["reviewer_id"] == FAKE_TRANSACTION["buyer_id"]
    assert captured["reviewed_user_id"] == FAKE_TRANSACTION["seller_id"]


# ===========================================================================
# AC2: transaction is not completed (does not exist)
# ===========================================================================

def test_buyer_review_transaction_not_found(client, monkeypatch):
    """AC2: no matching transaction -> 404."""
    login_as(client, 2)
    monkeypatch.setattr(db_module, "get_transaction_by_id", lambda tid: None)

    resp = client.post("/api/transactions/999/buyer-review", json={"rating": 5})

    assert resp.status_code == 404
    assert "error" in resp.get_json()


# ===========================================================================
# AC3: review is linked to the transaction and seller profile (payload shape)
# ===========================================================================

def test_buyer_review_links_transaction_and_seller(client, monkeypatch):
    """AC3: create_review() is called with the transaction id and seller id."""
    login_as(client, 2)
    monkeypatch.setattr(db_module, "get_transaction_by_id", lambda tid: FAKE_TRANSACTION)

    captured = {}

    def fake_create_review(**kwargs):
        captured.update(kwargs)
        return FAKE_CREATED_REVIEW

    monkeypatch.setattr(db_module, "create_review", fake_create_review)

    client.post("/api/transactions/1/buyer-review", json={"rating": 5})

    assert captured["transaction_id"] == 1
    assert captured["reviewed_user_id"] == FAKE_TRANSACTION["seller_id"]


# ===========================================================================
# AC4: rating outside 1-5, or non-integer, is rejected
# ===========================================================================

@pytest.mark.parametrize("bad_rating", [0, 6, -1, 4.5, "five", True, None])
def test_buyer_review_rejects_invalid_rating(client, monkeypatch, bad_rating):
    """AC4: invalid ratings never reach create_review()."""
    login_as(client, 2)
    monkeypatch.setattr(db_module, "get_transaction_by_id", lambda tid: FAKE_TRANSACTION)

    def fail_if_called(**_kwargs):
        raise AssertionError("create_review() must not be called for an invalid rating")

    monkeypatch.setattr(db_module, "create_review", fail_if_called)

    resp = client.post("/api/transactions/1/buyer-review", json={"rating": bad_rating})

    assert resp.status_code == 400


def test_buyer_review_rejects_missing_body(client, monkeypatch):
    """AC4: a request with no JSON body at all is rejected, not a 500."""
    login_as(client, 2)
    monkeypatch.setattr(db_module, "get_transaction_by_id", lambda tid: FAKE_TRANSACTION)

    resp = client.post("/api/transactions/1/buyer-review")

    assert resp.status_code == 400


# ===========================================================================
# AC5: buyer was not involved in the completed transaction
# ===========================================================================

def test_buyer_review_rejects_seller_of_same_transaction(client, monkeypatch):
    """AC5: the seller of this transaction is not its buyer -> 403."""
    login_as(client, 1)  # seller_id in FAKE_TRANSACTION
    monkeypatch.setattr(db_module, "get_transaction_by_id", lambda tid: FAKE_TRANSACTION)

    resp = client.post("/api/transactions/1/buyer-review", json={"rating": 5})

    assert resp.status_code == 403
    assert "error" in resp.get_json()


def test_buyer_review_rejects_unrelated_user(client, monkeypatch):
    """AC5: a user unrelated to the transaction -> 403."""
    login_as(client, 999)
    monkeypatch.setattr(db_module, "get_transaction_by_id", lambda tid: FAKE_TRANSACTION)

    resp = client.post("/api/transactions/1/buyer-review", json={"rating": 5})

    assert resp.status_code == 403


def test_buyer_review_rejects_unauthenticated(client, monkeypatch):
    """Unauthenticated request -> 401, before any DB lookup."""
    monkeypatch.setattr(
        db_module,
        "get_transaction_by_id",
        lambda tid: (_ for _ in ()).throw(AssertionError("should not be called")),
    )

    resp = client.post("/api/transactions/1/buyer-review", json={"rating": 5})

    assert resp.status_code == 401
