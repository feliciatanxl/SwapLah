"""
Unit tests for:
  GET  /api/offers/received
  PATCH /api/offers/<id>/accept
  PATCH /api/offers/<id>/reject

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

FAKE_OFFERS = [
    {
        "id": 1, "listing_id": 10, "buyer_id": 2, "offer_type": "cash",
        "proposed_price": 40.0, "swap_listing_id": None, "status": "Pending",
        "created_at": "2026-06-09 10:00:00",
        "listing_title": "Test Item", "listing_category": "Electronics",
        "listing_price": "50.00", "seller_id": 1, "buyer_display_name": "BobBuyer",
        "swap_listing_title": None,
    },
    {
        "id": 2, "listing_id": 10, "buyer_id": 3, "offer_type": "swap",
        "proposed_price": None, "swap_listing_id": 5, "status": "Pending",
        "created_at": "2026-06-09 10:01:00",
        "listing_title": "Test Item", "listing_category": "Electronics",
        "listing_price": "50.00", "seller_id": 1, "buyer_display_name": "CarolBuyer",
        "swap_listing_title": "Swap Widget",
    },
]

FAKE_OFFER_PENDING = {
    "id": 1, "listing_id": 10, "buyer_id": 2, "offer_type": "cash",
    "proposed_price": 40.0, "swap_listing_id": None, "status": "Pending",
    "created_at": "2026-06-09 10:00:00",
}

FAKE_OFFER_REJECTED = {**FAKE_OFFER_PENDING, "status": "Rejected"}
FAKE_OFFER_ACCEPTED = {**FAKE_OFFER_PENDING, "status": "Accepted"}


# ===========================================================================
# GET /api/offers/received
# ===========================================================================

def test_unit_get_received_offers_success(client, monkeypatch):
    """AC1 (view): seller receives their offers list."""
    login_as(client, 1)
    monkeypatch.setattr(db_module, "get_offers_for_seller", lambda sid: FAKE_OFFERS)

    resp = client.get("/api/offers/received")

    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["offers"]) == 2
    assert data["offers"][0]["listingTitle"] == "Test Item"
    assert data["offers"][1]["swapListingTitle"] == "Swap Widget"


def test_unit_get_received_offers_unauthenticated(client):
    """AC2 (view): unauthenticated request is rejected."""
    resp = client.get("/api/offers/received")
    assert resp.status_code == 401


def test_unit_get_received_offers_empty(client, monkeypatch):
    """AC3 (view): empty list returned when seller has no offers."""
    login_as(client, 1)
    monkeypatch.setattr(db_module, "get_offers_for_seller", lambda sid: [])

    resp = client.get("/api/offers/received")

    assert resp.status_code == 200
    assert resp.get_json()["offers"] == []


# ===========================================================================
# PATCH /api/offers/<id>/accept
# ===========================================================================

def test_unit_accept_offer_success(client, monkeypatch):
    """AC1 (accept): seller accepts a pending offer."""
    login_as(client, 1)
    monkeypatch.setattr(db_module, "get_offer_by_id", lambda oid: FAKE_OFFER_PENDING)
    monkeypatch.setattr(db_module, "get_listing_owner", lambda lid: 1)
    monkeypatch.setattr(db_module, "accept_offer", lambda oid: FAKE_OFFER_ACCEPTED)

    resp = client.patch("/api/offers/1/accept")

    assert resp.status_code == 200
    assert resp.get_json()["offer"]["status"] == "Accepted"


def test_unit_accept_offer_non_owner_forbidden(client, monkeypatch):
    """AC2 (accept): non-owner gets 403."""
    login_as(client, 2)
    monkeypatch.setattr(db_module, "get_offer_by_id", lambda oid: FAKE_OFFER_PENDING)
    monkeypatch.setattr(db_module, "get_listing_owner", lambda lid: 1)

    resp = client.patch("/api/offers/1/accept")

    assert resp.status_code == 403


def test_unit_accept_offer_not_found(client, monkeypatch):
    """Accepting non-existent offer → 404."""
    login_as(client, 1)
    monkeypatch.setattr(db_module, "get_offer_by_id", lambda oid: None)

    resp = client.patch("/api/offers/999/accept")

    assert resp.status_code == 404


def test_unit_accept_offer_already_rejected(client, monkeypatch):
    """Cannot accept an already-rejected offer → 409."""
    login_as(client, 1)
    monkeypatch.setattr(db_module, "get_offer_by_id", lambda oid: FAKE_OFFER_REJECTED)
    monkeypatch.setattr(db_module, "get_listing_owner", lambda lid: 1)

    resp = client.patch("/api/offers/1/accept")

    assert resp.status_code == 409


def test_unit_accept_offer_unauthenticated(client):
    """Unauthenticated accept → 401."""
    resp = client.patch("/api/offers/1/accept")
    assert resp.status_code == 401


# ===========================================================================
# PATCH /api/offers/<id>/reject
# ===========================================================================

def test_unit_reject_offer_success(client, monkeypatch):
    """AC1 (reject): seller rejects a pending offer."""
    login_as(client, 1)
    monkeypatch.setattr(db_module, "get_offer_by_id", lambda oid: FAKE_OFFER_PENDING)
    monkeypatch.setattr(db_module, "get_listing_owner", lambda lid: 1)
    monkeypatch.setattr(db_module, "reject_offer", lambda oid: FAKE_OFFER_REJECTED)

    resp = client.patch("/api/offers/1/reject")

    assert resp.status_code == 200
    assert resp.get_json()["offer"]["status"] == "Rejected"


def test_unit_reject_offer_non_owner_forbidden(client, monkeypatch):
    """AC2 (reject): non-owner gets 403."""
    login_as(client, 2)
    monkeypatch.setattr(db_module, "get_offer_by_id", lambda oid: FAKE_OFFER_PENDING)
    monkeypatch.setattr(db_module, "get_listing_owner", lambda lid: 1)

    resp = client.patch("/api/offers/1/reject")

    assert resp.status_code == 403


def test_unit_reject_offer_not_found(client, monkeypatch):
    """Rejecting non-existent offer → 404."""
    login_as(client, 1)
    monkeypatch.setattr(db_module, "get_offer_by_id", lambda oid: None)

    resp = client.patch("/api/offers/999/reject")

    assert resp.status_code == 404


def test_unit_reject_offer_already_rejected(client, monkeypatch):
    """Cannot reject an already-rejected offer → 409."""
    login_as(client, 1)
    monkeypatch.setattr(db_module, "get_offer_by_id", lambda oid: FAKE_OFFER_REJECTED)
    monkeypatch.setattr(db_module, "get_listing_owner", lambda lid: 1)

    resp = client.patch("/api/offers/1/reject")

    assert resp.status_code == 409


def test_unit_reject_offer_unauthenticated(client):
    """Unauthenticated reject → 401."""
    resp = client.patch("/api/offers/1/reject")
    assert resp.status_code == 401


def test_unit_reject_does_not_touch_other_offers(client, monkeypatch):
    """AC3 (reject): reject_offer is called once with the correct offer id."""
    login_as(client, 1)
    monkeypatch.setattr(db_module, "get_offer_by_id", lambda oid: FAKE_OFFER_PENDING)
    monkeypatch.setattr(db_module, "get_listing_owner", lambda lid: 1)

    rejected_ids = []

    def fake_reject(oid):
        rejected_ids.append(oid)
        return FAKE_OFFER_REJECTED

    monkeypatch.setattr(db_module, "reject_offer", fake_reject)

    client.patch("/api/offers/1/reject")

    assert rejected_ids == [1]