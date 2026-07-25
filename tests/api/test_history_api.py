"""
API integration tests for GET /api/transactions.

Uses a real temporary SQLite database seeded with users, listings, and
offers, exercising the actual accept_offer() -> transaction path so the
history page's transaction list (and its offer_id, used by the review
modal) is returned correctly.
"""
# pylint: disable=redefined-outer-name

import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a Flask test client backed by an isolated temporary SQLite database."""
    test_db = tmp_path / "test_history.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client, test_db


def create_user(test_db, student_id, display_name):
    """Insert a user and return the generated ID."""
    conn = sqlite3.connect(test_db)
    cursor = conn.execute(
        """
        INSERT INTO users (student_id, first_name, last_name, display_name,
                           email, contact_number, password_hash, role, status)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (student_id, display_name, "Test", display_name,
         f"{student_id.lower()}@mymail.nyp.edu.sg", "91234567",
         generate_password_hash("Password1"), "user", "Active"),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def create_listing(test_db, seller_id, title):
    """Insert a listing for a seller and return the generated ID."""
    conn = sqlite3.connect(test_db)
    now = "2026-07-01 10:00:00"
    cursor = conn.execute(
        """
        INSERT INTO listings (seller_id, title, description, price, category,
                              item_condition, image_url, listing_date, last_modified_timestamp)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (seller_id, title, "A nice item", "20.00", "Textbooks",
         "Good", '["https://example.com/img.jpg"]', now, now),
    )
    conn.commit()
    listing_id = cursor.lastrowid
    conn.close()
    return listing_id


def seed_completed_deal(test_db):
    """Seed a seller, buyer, listing, and an accepted offer. Returns ids."""
    seller_id = create_user(test_db, "S4000001", "HistorySeller")
    buyer_id = create_user(test_db, "S4000002", "HistoryBuyer")
    listing_id = create_listing(test_db, seller_id, "History Test Item")

    conn = sqlite3.connect(test_db)
    conn.execute(
        """
        INSERT INTO offers (listing_id, buyer_id, offer_type, proposed_price,
                            swap_listing_id, status, created_at)
        VALUES (?, ?, 'cash', 20.0, NULL, 'Pending', '2026-07-01 10:00:00')
        """,
        (listing_id, buyer_id),
    )
    offer_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()[0]
    conn.commit()
    conn.close()

    db_module.accept_offer(offer_id)
    return seller_id, buyer_id, offer_id


def login_as(test_client, user_id):
    """Set the logged-in user on the test client session."""
    with test_client.session_transaction() as sess:
        sess["user_id"] = user_id


def test_transactions_require_login(client):
    """An unauthenticated request is rejected with 401."""
    test_client, _test_db = client

    resp = test_client.get("/api/transactions?role=seller")

    assert resp.status_code == 401


def test_seller_transactions_include_offer_id(client):
    """The seller's completed sale is listed with the offer_id used for reviews."""
    test_client, test_db = client
    seller_id, _buyer_id, offer_id = seed_completed_deal(test_db)
    login_as(test_client, seller_id)

    resp = test_client.get("/api/transactions?role=seller")

    assert resp.status_code == 200
    transactions = resp.get_json()["transactions"]
    assert len(transactions) == 1
    assert transactions[0]["listingTitle"] == "History Test Item"
    assert transactions[0]["counterpartyDisplayName"] == "HistoryBuyer"
    assert transactions[0]["offerId"] == offer_id


def test_buyer_transactions_listed_for_buyer_role(client):
    """The buyer sees the same completed deal under the buyer role."""
    test_client, test_db = client
    _seller_id, buyer_id, offer_id = seed_completed_deal(test_db)
    login_as(test_client, buyer_id)

    resp = test_client.get("/api/transactions?role=buyer")

    assert resp.status_code == 200
    transactions = resp.get_json()["transactions"]
    assert len(transactions) == 1
    assert transactions[0]["offerId"] == offer_id
    assert transactions[0]["counterpartyDisplayName"] == "HistorySeller"


def test_seller_has_no_buyer_transactions(client):
    """A seller who never bought anything has an empty buyer transaction list."""
    test_client, test_db = client
    seller_id, _buyer_id, _offer_id = seed_completed_deal(test_db)
    login_as(test_client, seller_id)

    resp = test_client.get("/api/transactions?role=buyer")

    assert resp.status_code == 200
    assert resp.get_json()["transactions"] == []


def test_invalid_role_is_rejected(client):
    """An unknown role value is rejected with 400."""
    test_client, test_db = client
    seller_id, _buyer_id, _offer_id = seed_completed_deal(test_db)
    login_as(test_client, seller_id)

    resp = test_client.get("/api/transactions?role=admin")

    assert resp.status_code == 400
