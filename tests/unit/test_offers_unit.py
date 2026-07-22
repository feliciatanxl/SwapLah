# pylint: disable=missing-module-docstring,missing-function-docstring,redefined-outer-name,duplicate-code
"""
Unit tests for POST /api/offers — cash and swap offer submission.
All DB calls are monkeypatched so no real database is needed.
"""
import pytest
from app import create_app
from app.routes import offers as offers_routes


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def login_as(client, user_id=1):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


# ---------------------------------------------------------------------------
# Helpers / stubs
# ---------------------------------------------------------------------------

def make_fake_get_listing_owner(seller_id):
    """Return a stub that always reports the given seller_id."""
    def _stub(_listing_id):
        return seller_id
    return _stub


def make_fake_get_active_listing_by_buyer(owned):
    """Return a stub: owned=True means the listing belongs to the buyer."""
    def _stub(listing_id, buyer_id):
        return {"id": listing_id, "seller_id": buyer_id} if owned else None
    return _stub


def fake_create_offer(listing_id, buyer_id, offer_type, proposed_price=None, swap_listing_id=None):
    return {
        "id": 99,
        "listing_id": listing_id,
        "buyer_id": buyer_id,
        "offer_type": offer_type,
        "proposed_price": proposed_price,
        "swap_listing_id": swap_listing_id,
        "status": "Pending",
        "created_at": "2026-06-09 10:00:00",
    }


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------

def test_submit_offer_not_logged_in(client):
    """Unauthenticated request must be rejected with 401."""
    response = client.post("/api/offers", json={
        "listingId": 1,
        "offerType": "cash",
        "proposedPrice": 10.0,
    })
    assert response.status_code == 401
    assert "error" in response.get_json()


# ===========================================================================
# CASH OFFER
# ===========================================================================

def test_cash_offer_success(client, monkeypatch):
    """AC1 / AC4 (cash): valid cash offer is recorded with status Pending."""
    login_as(client, user_id=2)
    monkeypatch.setattr(
        offers_routes, "get_listing_owner", make_fake_get_listing_owner(seller_id=1)
    )
    monkeypatch.setattr(offers_routes, "create_offer", fake_create_offer)

    response = client.post("/api/offers", json={
        "listingId": 5,
        "offerType": "cash",
        "proposedPrice": 20.0,
    })

    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Cash offer submitted successfully."
    assert data["offer"]["offerType"] == "cash"
    assert data["offer"]["status"] == "Pending"      # AC3 (cash)
    assert data["offer"]["proposedPrice"] == 20.0


def test_cash_offer_on_own_listing_rejected(client, monkeypatch):
    """AC2 (cash): buyer must not offer on their own listing."""
    login_as(client, user_id=1)
    monkeypatch.setattr(
        offers_routes, "get_listing_owner", make_fake_get_listing_owner(seller_id=1)
    )

    response = client.post("/api/offers", json={
        "listingId": 5,
        "offerType": "cash",
        "proposedPrice": 20.0,
    })

    assert response.status_code == 403
    assert "error" in response.get_json()


def test_cash_offer_missing_price_rejected(client, monkeypatch):
    """AC5 (cash): offer without proposedPrice must be rejected."""
    login_as(client, user_id=2)
    monkeypatch.setattr(
        offers_routes, "get_listing_owner", make_fake_get_listing_owner(seller_id=1)
    )

    response = client.post("/api/offers", json={
        "listingId": 5,
        "offerType": "cash",
    })

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_cash_offer_invalid_price_rejected(client, monkeypatch):
    """proposedPrice must be a non-negative number."""
    login_as(client, user_id=2)
    monkeypatch.setattr(
        offers_routes, "get_listing_owner", make_fake_get_listing_owner(seller_id=1)
    )

    response = client.post("/api/offers", json={
        "listingId": 5,
        "offerType": "cash",
        "proposedPrice": "not-a-number",
    })

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_cash_offer_returns_201_with_offer(client, monkeypatch):
    """AC4 (cash): POST /api/offers creates the offer and returns it."""
    login_as(client, user_id=2)
    monkeypatch.setattr(
        offers_routes, "get_listing_owner", make_fake_get_listing_owner(seller_id=1)
    )
    monkeypatch.setattr(offers_routes, "create_offer", fake_create_offer)

    response = client.post("/api/offers", json={
        "listingId": 5,
        "offerType": "cash",
        "proposedPrice": 15.0,
    })

    assert response.status_code == 201
    data = response.get_json()
    assert "offer" in data
    assert data["offer"]["id"] == 99


# ===========================================================================
# SWAP OFFER
# ===========================================================================

def test_swap_offer_success(client, monkeypatch):
    """AC1 (swap): valid swap offer using buyer's own active listing is recorded."""
    login_as(client, user_id=2)
    monkeypatch.setattr(
        offers_routes, "get_listing_owner", make_fake_get_listing_owner(seller_id=1)
    )
    monkeypatch.setattr(
        offers_routes,
        "get_active_listing_by_buyer",
        make_fake_get_active_listing_by_buyer(owned=True),
    )
    monkeypatch.setattr(offers_routes, "create_offer", fake_create_offer)

    response = client.post("/api/offers", json={
        "listingId": 5,
        "offerType": "swap",
        "swapListingId": 10,
    })

    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Swap offer submitted successfully."
    assert data["offer"]["offerType"] == "swap"
    assert data["offer"]["swapListingId"] == 10


def test_swap_offer_item_not_owned_by_buyer(client, monkeypatch):
    """AC2 / AC3 (swap): swap item must exist in buyer's own active listings."""
    login_as(client, user_id=2)
    monkeypatch.setattr(
        offers_routes, "get_listing_owner", make_fake_get_listing_owner(seller_id=1)
    )
    monkeypatch.setattr(
        offers_routes,
        "get_active_listing_by_buyer",
        make_fake_get_active_listing_by_buyer(owned=False),
    )

    response = client.post("/api/offers", json={
        "listingId": 5,
        "offerType": "swap",
        "swapListingId": 99,
    })

    assert response.status_code == 403
    assert "error" in response.get_json()


def test_swap_offer_on_own_listing_rejected(client, monkeypatch):
    """AC4 (swap): buyer must not swap-offer on their own listing."""
    login_as(client, user_id=1)
    monkeypatch.setattr(
        offers_routes, "get_listing_owner", make_fake_get_listing_owner(seller_id=1)
    )

    response = client.post("/api/offers", json={
        "listingId": 5,
        "offerType": "swap",
        "swapListingId": 10,
    })

    assert response.status_code == 403
    assert "error" in response.get_json()


def test_swap_offer_missing_swap_listing_id(client, monkeypatch):
    """AC2 (swap): swapListingId is required."""
    login_as(client, user_id=2)
    monkeypatch.setattr(
        offers_routes, "get_listing_owner", make_fake_get_listing_owner(seller_id=1)
    )

    response = client.post("/api/offers", json={
        "listingId": 5,
        "offerType": "swap",
    })

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_swap_offer_returns_201_with_offer(client, monkeypatch):
    """AC5 (swap): POST /api/offers creates the swap offer and returns it."""
    login_as(client, user_id=2)
    monkeypatch.setattr(
        offers_routes, "get_listing_owner", make_fake_get_listing_owner(seller_id=1)
    )
    monkeypatch.setattr(
        offers_routes,
        "get_active_listing_by_buyer",
        make_fake_get_active_listing_by_buyer(owned=True),
    )
    monkeypatch.setattr(offers_routes, "create_offer", fake_create_offer)

    response = client.post("/api/offers", json={
        "listingId": 5,
        "offerType": "swap",
        "swapListingId": 10,
    })

    assert response.status_code == 201
    data = response.get_json()
    assert "offer" in data
    assert data["offer"]["id"] == 99


# ---------------------------------------------------------------------------
# General validation
# ---------------------------------------------------------------------------

def test_invalid_offer_type(client, monkeypatch):
    """Unknown offerType must be rejected with 400."""
    login_as(client, user_id=2)
    monkeypatch.setattr(
        offers_routes, "get_listing_owner", make_fake_get_listing_owner(seller_id=1)
    )

    response = client.post("/api/offers", json={
        "listingId": 5,
        "offerType": "barter",
    })

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_missing_listing_id(client):
    """listingId is required."""
    login_as(client, user_id=2)

    response = client.post("/api/offers", json={
        "offerType": "cash",
        "proposedPrice": 10.0,
    })

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_listing_not_found(client, monkeypatch):
    """Non-existent listing must return 404."""
    login_as(client, user_id=2)
    monkeypatch.setattr(offers_routes, "get_listing_owner", lambda lid: None)

    response = client.post("/api/offers", json={
        "listingId": 999,
        "offerType": "cash",
        "proposedPrice": 10.0,
    })

    assert response.status_code == 404
    assert "error" in response.get_json()
