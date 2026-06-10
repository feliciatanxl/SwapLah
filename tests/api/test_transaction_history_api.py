"""
API tests for GET /api/transactions

All DB calls are monkeypatched — no real database needed.
"""
import pytest
import app.db as db_module
from app import create_app


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

FAKE_TXN_CASH = {
    "transaction_id": 1,
    "transaction_date": "2026-06-01 10:00:00",
    "offer_id": 10,
    "offer_type": "cash",
    "proposed_price": 50.0,
    "swap_listing_id": None,
    "swap_listing_title": None,
    "listing_id": 5,
    "listing_title": "Calculus Textbook",
    "listing_category": "Textbooks",
    "listing_price": "55.00",
    "buyer_id": 2,
    "buyer_display_name": "Alice",
    "seller_id": 1,
    "seller_display_name": "Bob",
}

FAKE_TXN_SWAP = {
    "transaction_id": 2,
    "transaction_date": "2026-06-02 11:00:00",
    "offer_id": 11,
    "offer_type": "swap",
    "proposed_price": None,
    "swap_listing_id": 7,
    "swap_listing_title": "Physics Notes",
    "listing_id": 6,
    "listing_title": "Lab Coat",
    "listing_category": "Lab Equipment",
    "listing_price": "20.00",
    "buyer_id": 1,
    "buyer_display_name": "Bob",
    "seller_id": 3,
    "seller_display_name": "Carol",
}


# ===========================================================================
# Positive tests
# ===========================================================================

def test_api_get_transactions_returns_200(client, monkeypatch):
    """AC1: authenticated request returns 200 with transactions key."""
    login_as(client, 1)
    monkeypatch.setattr(db_module, "get_transactions_for_user", lambda uid: [FAKE_TXN_CASH])

    resp = client.get("/api/transactions")

    assert resp.status_code == 200
    assert "transactions" in resp.get_json()


def test_api_get_transactions_multiple_records(client, monkeypatch):
    """AC1: returns all transactions for the user."""
    login_as(client, 1)
    monkeypatch.setattr(
        db_module, "get_transactions_for_user",
        lambda uid: [FAKE_TXN_CASH, FAKE_TXN_SWAP]
    )

    resp = client.get("/api/transactions")
    data = resp.get_json()

    assert len(data["transactions"]) == 2


def test_api_get_transactions_empty_list(client, monkeypatch):
    """AC3: user with no transactions gets 200 with empty list."""
    login_as(client, 1)
    monkeypatch.setattr(db_module, "get_transactions_for_user", lambda uid: [])

    resp = client.get("/api/transactions")

    assert resp.status_code == 200
    assert resp.get_json()["transactions"] == []


def test_api_get_transactions_cash_fields(client, monkeypatch):
    """Cash transaction has correct fields and proposedPrice."""
    login_as(client, 2)
    monkeypatch.setattr(db_module, "get_transactions_for_user", lambda uid: [FAKE_TXN_CASH])

    txn = client.get("/api/transactions").get_json()["transactions"][0]

    assert txn["offerType"] == "cash"
    assert txn["proposedPrice"] == 50.0
    assert txn["listingTitle"] == "Calculus Textbook"
    assert txn["role"] == "buyer"


def test_api_get_transactions_swap_fields(client, monkeypatch):
    """Swap transaction has swapListingTitle populated."""
    login_as(client, 1)
    monkeypatch.setattr(db_module, "get_transactions_for_user", lambda uid: [FAKE_TXN_SWAP])

    txn = client.get("/api/transactions").get_json()["transactions"][0]

    assert txn["offerType"] == "swap"
    assert txn["swapListingTitle"] == "Physics Notes"
    assert txn["role"] == "buyer"


# ===========================================================================
# Negative tests
# ===========================================================================

def test_api_get_transactions_unauthenticated(client):
    """AC2: unauthenticated request returns 401."""
    resp = client.get("/api/transactions")
    assert resp.status_code == 401


def test_api_get_transactions_401_has_error_message(client):
    """AC2: 401 response includes an error message."""
    resp = client.get("/api/transactions")
    data = resp.get_json()
    assert "error" in data