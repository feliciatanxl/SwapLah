"""
API integration tests for GET /api/transactions.

Uses a real temporary SQLite database with seeded users, listings, and
transactions, exercising the actual SQL in get_transactions_for_user().
"""
import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "test_history.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client, test_db


def _create_user(conn, student_id, display_name):
    conn.execute(
        """
        INSERT INTO users (student_id, first_name, last_name, display_name,
                           email, contact_number, password_hash, role, status)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (student_id, display_name, "Test", display_name,
         f"{student_id.lower()}@mymail.nyp.edu.sg", "91234567",
         generate_password_hash("Password1"), "user", "Active"),
    )
    return conn.execute(
        "SELECT id FROM users WHERE student_id = ?", (student_id,)
    ).fetchone()["id"]


def _create_listing(conn, seller_id, title):
    now = "2026-06-09 10:00:00"
    conn.execute(
        """
        INSERT INTO listings (seller_id, title, description, price, category,
                              item_condition, image_url, listing_date, last_modified_timestamp)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (seller_id, title, "A nice item", "20.00", "Textbooks",
         "Good", '["https://example.com/img.jpg"]', now, now),
    )
    return conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]


def _create_offer_and_accept(test_db, seller_id, buyer_id, listing_id, price):
    """Seed a pending offer and accept it via the real accept_offer() path."""
    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        INSERT INTO offers (listing_id, buyer_id, offer_type, proposed_price,
                            swap_listing_id, status, created_at)
        VALUES (?, ?, 'cash', ?, NULL, 'Pending', '2026-06-10 10:00:00')
        """,
        (listing_id, buyer_id, price),
    )
    offer_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    conn.commit()
    conn.close()

    db_module.accept_offer(offer_id)


def _create_rejected_offer(test_db, seller_id, buyer_id, listing_id, price):
    """Seed a rejected cash offer for resolved-offer history."""
    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        INSERT INTO offers (listing_id, buyer_id, offer_type, proposed_price,
                            swap_listing_id, status, created_at)
        VALUES (?, ?, 'cash', ?, NULL, 'Rejected', '2026-06-11 10:00:00')
        """,
        (listing_id, buyer_id, price),
    )
    conn.commit()
    conn.close()


def seed_completed_deal(test_db, seller_name="Seller1", buyer_name="Buyer1", price=25.0):
    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    seller_id = _create_user(conn, "S1000001", seller_name)
    buyer_id = _create_user(conn, "S1000002", buyer_name)
    listing_id = _create_listing(conn, seller_id, "Intro to Algorithms 3E")
    conn.commit()
    conn.close()

    _create_offer_and_accept(test_db, seller_id, buyer_id, listing_id, price)
    return seller_id, buyer_id


def login_as(test_client, user_id):
    with test_client.session_transaction() as sess:
        sess["user_id"] = user_id


# ===========================================================================
# GET /api/transactions
# ===========================================================================

def test_seller_sees_completed_transaction(client):
    """AC1: seller sees a past transaction where they were the seller."""
    test_client, test_db = client
    seller_id, buyer_id = seed_completed_deal(test_db)
    login_as(test_client, seller_id)

    resp = test_client.get("/api/transactions?role=seller")

    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["transactions"]) == 1
    assert data["transactions"][0]["listingTitle"] == "Intro to Algorithms 3E"
    assert data["transactions"][0]["counterpartyDisplayName"] == "Buyer1"


def test_buyer_sees_completed_transaction(client):
    """AC1: buyer sees a past transaction where they were the buyer."""
    test_client, test_db = client
    seller_id, buyer_id = seed_completed_deal(test_db)
    login_as(test_client, buyer_id)

    resp = test_client.get("/api/transactions?role=buyer")

    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["transactions"]) == 1
    assert data["transactions"][0]["counterpartyDisplayName"] == "Seller1"


def test_history_unauthenticated_blocked(client):
    """AC2: unauthenticated request is blocked."""
    test_client, test_db = client
    resp = test_client.get("/api/transactions?role=buyer")
    assert resp.status_code == 401


def test_history_empty_state_for_new_user(client):
    """AC3: a user with no completed transactions gets an empty list."""
    test_client, test_db = client
    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    new_user_id = _create_user(conn, "S1999999", "NewUser")
    conn.commit()
    conn.close()

    login_as(test_client, new_user_id)

    resp = test_client.get("/api/transactions?role=buyer")

    assert resp.status_code == 200
    assert resp.get_json()["transactions"] == []


def test_history_does_not_leak_other_users_transactions(client):
    """A user only sees their own transactions, not everyone else's."""
    test_client, test_db = client
    seller_id, buyer_id = seed_completed_deal(test_db)

    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    unrelated_user_id = _create_user(conn, "S1888888", "Unrelated")
    conn.commit()
    conn.close()

    login_as(test_client, unrelated_user_id)

    resp = test_client.get("/api/transactions?role=buyer")
    assert resp.get_json()["transactions"] == []

    resp = test_client.get("/api/transactions?role=seller")
    assert resp.get_json()["transactions"] == []


def test_resolved_offer_outcomes_include_accepted_and_rejected(client):
    """Accepted and rejected offers appear in transaction offer outcomes."""
    test_client, test_db = client
    seller_id, buyer_id = seed_completed_deal(test_db)

    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    rejected_listing_id = _create_listing(conn, seller_id, "Rejected Listing")
    conn.commit()
    conn.close()
    _create_rejected_offer(test_db, seller_id, buyer_id, rejected_listing_id, 12.0)

    login_as(test_client, seller_id)

    resp = test_client.get("/api/transactions/offers")

    assert resp.status_code == 200
    statuses = {offer["status"] for offer in resp.get_json()["offers"]}
    assert statuses == {"Accepted", "Rejected"}
