"""
API integration tests for POST /api/offers.
Uses a real temporary SQLite database with seeded users and listings.
"""
import sqlite3
import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "test_offers.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client, test_db


def seed_db(test_db):
    """Insert two users and two listings for testing."""
    conn = sqlite3.connect(test_db)

    # user 1 = seller
    conn.execute(
        """
        INSERT INTO users (student_id, first_name, last_name, display_name,
                           email, contact_number, password_hash, role, status)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        ("S11111111", "Alice", "Seller", "AliceSeller",
         "alice@mymail.nyp.edu.sg", "91111111",
         generate_password_hash("Password1"), "user", "Active"),
    )
    # user 2 = buyer
    conn.execute(
        """
        INSERT INTO users (student_id, first_name, last_name, display_name,
                           email, contact_number, password_hash, role, status)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        ("S22222222", "Bob", "Buyer", "BobBuyer",
         "bob@mymail.nyp.edu.sg", "92222222",
         generate_password_hash("Password2"), "user", "Active"),
    )

    now = "2026-06-09 10:00:00"
    # listing 1 owned by seller (id=1)
    conn.execute(
        """
        INSERT INTO listings (seller_id, title, description, price, category,
                              item_condition, image_url, listing_date, last_modified_timestamp)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (1, "Seller Item", "A nice item", "50.00", "Electronics",
         "Good", '["https://example.com/img.jpg"]', now, now),
    )
    # listing 2 owned by buyer (id=2) — used as swap item
    conn.execute(
        """
        INSERT INTO listings (seller_id, title, description, price, category,
                              item_condition, image_url, listing_date, last_modified_timestamp)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (2, "Buyer Swap Item", "My swap item", "30.00", "Books",
         "Fair", '["https://example.com/swap.jpg"]', now, now),
    )
    conn.commit()
    conn.close()


def login_as_buyer(test_client, test_db):
    """Authenticate the test client as user id=2 (buyer)."""
    with test_client.session_transaction() as sess:
        sess["user_id"] = 2


def login_as_seller(test_client, test_db):
    """Authenticate the test client as user id=1 (seller)."""
    with test_client.session_transaction() as sess:
        sess["user_id"] = 1


# ===========================================================================
# CASH OFFER — Positive cases
# ===========================================================================

def test_api_cash_offer_success(client):
    """AC1 / AC4 (cash): buyer submits a valid cash offer — 201 returned."""
    test_client, test_db = client
    seed_db(test_db)
    login_as_buyer(test_client, test_db)

    response = test_client.post("/api/offers", json={
        "listingId": 1,
        "offerType": "cash",
        "proposedPrice": 45.0,
    })

    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Cash offer submitted successfully."
    assert data["offer"]["offerType"] == "cash"
    assert data["offer"]["proposedPrice"] == 45.0
    assert data["offer"]["status"] == "Pending"       # AC3 (cash)
    assert data["offer"]["listingId"] == 1
    assert data["offer"]["buyerId"] == 2


def test_api_cash_offer_status_is_pending(client):
    """AC3 (cash): offer status is set to Pending upon creation."""
    test_client, test_db = client
    seed_db(test_db)
    login_as_buyer(test_client, test_db)

    response = test_client.post("/api/offers", json={
        "listingId": 1,
        "offerType": "cash",
        "proposedPrice": 10.0,
    })

    assert response.status_code == 201
    assert response.get_json()["offer"]["status"] == "Pending"


# ===========================================================================
# CASH OFFER — Negative cases
# ===========================================================================

def test_api_cash_offer_on_own_listing(client):
    """AC2 (cash): seller cannot submit a cash offer on their own listing."""
    test_client, test_db = client
    seed_db(test_db)
    login_as_seller(test_client, test_db)

    response = test_client.post("/api/offers", json={
        "listingId": 1,
        "offerType": "cash",
        "proposedPrice": 40.0,
    })

    assert response.status_code == 403
    assert "error" in response.get_json()


def test_api_cash_offer_missing_price(client):
    """AC5 (cash): offer without proposedPrice is rejected."""
    test_client, test_db = client
    seed_db(test_db)
    login_as_buyer(test_client, test_db)

    response = test_client.post("/api/offers", json={
        "listingId": 1,
        "offerType": "cash",
    })

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_api_cash_offer_unauthenticated(client):
    """Unauthenticated request must be rejected with 401."""
    test_client, test_db = client
    seed_db(test_db)

    response = test_client.post("/api/offers", json={
        "listingId": 1,
        "offerType": "cash",
        "proposedPrice": 10.0,
    })

    assert response.status_code == 401
    assert "error" in response.get_json()


# ===========================================================================
# SWAP OFFER — Positive cases
# ===========================================================================

def test_api_swap_offer_success(client):
    """AC1 / AC5 (swap): buyer submits a swap offer using their own active listing."""
    test_client, test_db = client
    seed_db(test_db)
    login_as_buyer(test_client, test_db)

    response = test_client.post("/api/offers", json={
        "listingId": 1,
        "offerType": "swap",
        "swapListingId": 2,   # listing 2 belongs to buyer
    })

    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Swap offer submitted successfully."
    assert data["offer"]["offerType"] == "swap"
    assert data["offer"]["swapListingId"] == 2
    assert data["offer"]["buyerId"] == 2


# ===========================================================================
# SWAP OFFER — Negative cases
# ===========================================================================

def test_api_swap_offer_item_not_owned_by_buyer(client):
    """AC2 / AC3 (swap): swap item must be in buyer's active listings."""
    test_client, test_db = client
    seed_db(test_db)
    login_as_buyer(test_client, test_db)

    # listing 1 belongs to seller, not the buyer
    response = test_client.post("/api/offers", json={
        "listingId": 1,
        "offerType": "swap",
        "swapListingId": 1,
    })

    assert response.status_code == 403
    assert "error" in response.get_json()


def test_api_swap_offer_on_own_listing(client):
    """AC4 (swap): buyer must not swap-offer on their own listing."""
    test_client, test_db = client
    seed_db(test_db)
    login_as_buyer(test_client, test_db)

    # buyer tries to offer on listing 2 which they own
    response = test_client.post("/api/offers", json={
        "listingId": 2,
        "offerType": "swap",
        "swapListingId": 2,
    })

    assert response.status_code == 403
    assert "error" in response.get_json()


def test_api_swap_offer_missing_swap_listing_id(client):
    """AC2 (swap): swapListingId is required."""
    test_client, test_db = client
    seed_db(test_db)
    login_as_buyer(test_client, test_db)

    response = test_client.post("/api/offers", json={
        "listingId": 1,
        "offerType": "swap",
    })

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_api_swap_offer_unauthenticated(client):
    """Unauthenticated swap request must be rejected with 401."""
    test_client, test_db = client
    seed_db(test_db)

    response = test_client.post("/api/offers", json={
        "listingId": 1,
        "offerType": "swap",
        "swapListingId": 2,
    })

    assert response.status_code == 401
    assert "error" in response.get_json()
