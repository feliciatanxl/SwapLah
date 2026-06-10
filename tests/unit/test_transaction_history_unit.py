"""
Unit tests for GET /api/transactions

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

FAKE_TRANSACTIONS = [
    {
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
    },
    {
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
    },
]


# ===========================================================================
# GET /api/transactions
# ===========================================================================

def test_get_transactions_unauthenticated(client):
    """AC2: unauthenticated request is blocked with 401."""
    resp = client.get("/api/transactions")
    assert resp.status_code == 401


def test_get_transactions_success(client, monkeypatch):
    """AC1: logged-in user receives their transaction list."""
    login_as(client, 1)
    monkeypatch.setattr(db_module, "get_transactions_for_user", lambda uid: FAKE_TRANSACTIONS)

    resp = client.get("/api/transactions")

    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["transactions"]) == 2


def test_get_transactions_empty(client, monkeypatch):
    """AC3: user with no transactions receives an empty list."""
    login_as(client, 1)
    monkeypatch.setattr(db_module, "get_transactions_for_user", lambda uid: [])

    resp = client.get("/api/transactions")

    assert resp.status_code == 200
    assert resp.get_json()["transactions"] == []


def test_get_transactions_buyer_role_set(client, monkeypatch):
    """AC1: transaction where user is the buyer has role='buyer'."""
    login_as(client, 2)  # buyer_id in FAKE_TRANSACTIONS[0] is 2
    monkeypatch.setattr(db_module, "get_transactions_for_user", lambda uid: [FAKE_TRANSACTIONS[0]])

    resp = client.get("/api/transactions")
    txn = resp.get_json()["transactions"][0]

    assert txn["role"] == "buyer"
    assert txn["listingTitle"] == "Calculus Textbook"
    assert txn["buyerDisplayName"] == "Alice"


def test_get_transactions_seller_role_set(client, monkeypatch):
    """AC1: transaction where user is the seller has role='seller'."""
    login_as(client, 1)  # seller_id in FAKE_TRANSACTIONS[0] is 1
    monkeypatch.setattr(db_module, "get_transactions_for_user", lambda uid: [FAKE_TRANSACTIONS[0]])

    resp = client.get("/api/transactions")
    txn = resp.get_json()["transactions"][0]

    assert txn["role"] == "seller"


def test_get_transactions_fields_present(client, monkeypatch):
    """Response contains all expected fields."""
    login_as(client, 1)
    monkeypatch.setattr(db_module, "get_transactions_for_user", lambda uid: [FAKE_TRANSACTIONS[0]])

    resp = client.get("/api/transactions")
    txn = resp.get_json()["transactions"][0]

    for field in [
        "transactionId", "transactionDate", "offerId", "offerType",
        "proposedPrice", "listingId", "listingTitle", "listingCategory",
        "buyerId", "buyerDisplayName", "sellerId", "sellerDisplayName", "role",
    ]:
        assert field in txn, f"Missing field: {field}"


def test_get_transactions_swap_offer(client, monkeypatch):
    """Swap transactions include swapListingTitle."""
    login_as(client, 1)
    monkeypatch.setattr(db_module, "get_transactions_for_user", lambda uid: [FAKE_TRANSACTIONS[1]])

    resp = client.get("/api/transactions")
    txn = resp.get_json()["transactions"][0]

    assert txn["offerType"] == "swap"
    assert txn["swapListingTitle"] == "Physics Notes"


def test_get_transactions_called_with_user_id(client, monkeypatch):
    """DB function is called with the correct logged-in user id."""
    login_as(client, 42)
    called_with = []

    def fake_get(uid):
        called_with.append(uid)
        return []

    monkeypatch.setattr(db_module, "get_transactions_for_user", fake_get)
    client.get("/api/transactions")

    assert called_with == [42]