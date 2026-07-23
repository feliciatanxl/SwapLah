"""
Unit tests for:
  GET /api/transactions

All DB calls are monkeypatched — no real database needed.
"""
import pytest
from app import create_app
from app.routes import history as history_routes
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

FAKE_BUYER_TRANSACTIONS = [
    {
        "id": 1, "transaction_type": "cash", "amount": 55.0,
        "created_at": "2026-05-08 10:00:00",
        "listing_title": "Logitech MX Master 3", "listing_category": "Electronics",
        "counterparty_display_name": "Aisyah R.",
    },
    {
        "id": 2, "transaction_type": "swap", "amount": None,
        "created_at": "2026-05-02 09:00:00",
        "listing_title": "Physics Lab Goggles", "listing_category": "Lab Equipment",
        "counterparty_display_name": "Hafiz M.",
    },
]

FAKE_SELLER_TRANSACTIONS = [
    {
        "id": 3, "transaction_type": "cash", "amount": 20.0,
        "created_at": "2026-05-12 14:00:00",
        "listing_title": "Intro to Algorithms 3E", "listing_category": "Textbooks",
        "counterparty_display_name": "Wei Ming",
    },
]

FAKE_RESOLVED_OFFERS = [
    {
        "id": 4, "listing_id": 12, "buyer_id": 2, "offer_type": "cash",
        "proposed_price": 30.0, "swap_listing_id": None, "status": "Accepted",
        "created_at": "2026-05-13 15:00:00",
        "listing_title": "Calculator", "listing_category": "Electronics",
        "listing_price": "35.00", "buyer_display_name": "Buyer One",
        "seller_display_name": "Seller One", "swap_listing_title": None,
    },
    {
        "id": 5, "listing_id": 13, "buyer_id": 3, "offer_type": "swap",
        "proposed_price": None, "swap_listing_id": 9, "status": "Rejected",
        "created_at": "2026-05-14 16:00:00",
        "listing_title": "Lab Coat", "listing_category": "Clothing",
        "listing_price": "18.00", "buyer_display_name": "Buyer Two",
        "seller_display_name": "Seller Two", "swap_listing_title": "Notebook",
    },
]


# ===========================================================================
# GET /api/transactions
# ===========================================================================

def test_unit_get_buyer_history_success(client, monkeypatch):
    """AC1 (buyer): logged-in buyer sees their past transactions."""
    login_as(client, 1)
    monkeypatch.setattr(
        db_module, "get_transactions_for_user",
        lambda user_id, role: FAKE_BUYER_TRANSACTIONS,
    )

    resp = client.get("/api/transactions?role=buyer")

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["role"] == "buyer"
    assert len(data["transactions"]) == 2
    assert data["transactions"][0]["listingTitle"] == "Logitech MX Master 3"
    assert data["transactions"][0]["counterpartyDisplayName"] == "Aisyah R."


def test_unit_get_seller_history_success(client, monkeypatch):
    """AC1 (seller): logged-in seller sees their past transactions."""
    login_as(client, 1)
    monkeypatch.setattr(
        db_module, "get_transactions_for_user",
        lambda user_id, role: FAKE_SELLER_TRANSACTIONS,
    )

    resp = client.get("/api/transactions?role=seller")

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["role"] == "seller"
    assert len(data["transactions"]) == 1
    assert data["transactions"][0]["counterpartyDisplayName"] == "Wei Ming"


def test_unit_get_history_defaults_to_buyer(client, monkeypatch):
    """No role query param defaults to 'buyer'."""
    login_as(client, 1)
    monkeypatch.setattr(
        db_module, "get_transactions_for_user",
        lambda user_id, role: FAKE_BUYER_TRANSACTIONS,
    )

    resp = client.get("/api/transactions")

    assert resp.status_code == 200
    assert resp.get_json()["role"] == "buyer"


def test_unit_get_history_empty_state(client, monkeypatch):
    """AC3: no completed transactions returns an empty list, not an error."""
    login_as(client, 1)
    monkeypatch.setattr(db_module, "get_transactions_for_user", lambda user_id, role: [])

    resp = client.get("/api/transactions?role=buyer")

    assert resp.status_code == 200
    assert resp.get_json()["transactions"] == []


def test_unit_get_history_unauthenticated(client):
    """AC2: unauthenticated request is rejected with 401."""
    resp = client.get("/api/transactions?role=buyer")
    assert resp.status_code == 401


def test_unit_get_history_invalid_role(client):
    """An invalid role value is rejected with 400."""
    login_as(client, 1)
    resp = client.get("/api/transactions?role=admin")
    assert resp.status_code == 400


def test_unit_get_resolved_offer_outcomes_success(client, monkeypatch):
    """Logged-in users can see accepted and rejected offer outcomes involving them."""
    login_as(client, 1)
    monkeypatch.setattr(db_module, "get_resolved_offers_for_user", lambda user_id: FAKE_RESOLVED_OFFERS)

    resp = client.get("/api/transactions/offers")

    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["offers"]) == 2
    assert data["offers"][0]["status"] == "Accepted"
    assert data["offers"][1]["status"] == "Rejected"
    assert data["offers"][1]["swapListingTitle"] == "Notebook"


def test_unit_get_resolved_offer_outcomes_admin_sees_all(client, monkeypatch):
    """Active admins can see all accepted and rejected offer outcomes."""
    login_as(client, 1)
    with client.session_transaction() as sess:
        sess["role"] = "admin"

    monkeypatch.setattr(
        db_module,
        "get_user_by_id",
        lambda uid: {"id": uid, "role": "admin", "status": "Active"},
    )
    monkeypatch.setattr(db_module, "get_all_resolved_offers", lambda: FAKE_RESOLVED_OFFERS)
    monkeypatch.setattr(
        db_module,
        "get_resolved_offers_for_user",
        lambda user_id: pytest.fail("admin should not use user-scoped resolved offers"),
    )

    resp = client.get("/api/transactions/offers")

    assert resp.status_code == 200
    assert len(resp.get_json()["offers"]) == 2


def test_unit_get_resolved_offer_outcomes_unauthenticated(client):
    """Logged-out users cannot see resolved offer outcomes."""
    resp = client.get("/api/transactions/offers")
    assert resp.status_code == 401
