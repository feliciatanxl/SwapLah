"""
API integration tests for POST /api/transactions/<id>/buyer-review.

Uses a real temporary SQLite database with seeded users, listings, offers,
and transactions, exercising the actual accept_offer() -> create_review()
path end to end. Mirrors test_seller_review_api.py but for the buyer
reviewing the seller.
"""
import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "test_buyer_review.db"
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


def _create_offer_and_accept(test_db, buyer_id, listing_id, price):
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
    return offer_id


def seed_completed_deal(test_db, seller_name="Seller1", buyer_name="Buyer1", price=25.0):
    """Seed a seller, buyer, listing, and an accepted offer/transaction. Returns ids."""
    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    seller_id = _create_user(conn, "S1000001", seller_name)
    buyer_id = _create_user(conn, "S1000002", buyer_name)
    listing_id = _create_listing(conn, seller_id, "Intro to Algorithms 3E")
    conn.commit()
    conn.close()

    offer_id = _create_offer_and_accept(test_db, buyer_id, listing_id, price)

    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    transaction_id = conn.execute(
        "SELECT id FROM transactions WHERE offer_id = ?", (offer_id,)
    ).fetchone()["id"]
    conn.close()

    return seller_id, buyer_id, transaction_id


def seed_pending_offer(test_db, seller_name="Seller1", buyer_name="Buyer1"):
    """Seed a seller, buyer, listing, and a still-Pending (not completed) offer."""
    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    seller_id = _create_user(conn, "S1000001", seller_name)
    buyer_id = _create_user(conn, "S1000002", buyer_name)
    listing_id = _create_listing(conn, seller_id, "Uncompleted Deal Item")
    conn.execute(
        """
        INSERT INTO offers (listing_id, buyer_id, offer_type, proposed_price,
                            swap_listing_id, status, created_at)
        VALUES (?, ?, 'cash', ?, NULL, 'Pending', '2026-06-10 10:00:00')
        """,
        (listing_id, buyer_id, 15.0),
    )
    conn.commit()
    conn.close()

    return seller_id, buyer_id


def login_as(test_client, user_id):
    with test_client.session_transaction() as sess:
        sess["user_id"] = user_id


# ===========================================================================
# AC1: buyer submits a valid 1-5 rating with optional comment for the seller
# ===========================================================================

def test_buyer_can_submit_review_with_comment(client):
    """AC1: buyer leaves a rating + comment for the seller on a completed deal."""
    test_client, test_db = client
    seller_id, buyer_id, transaction_id = seed_completed_deal(test_db)
    login_as(test_client, buyer_id)

    resp = test_client.post(
        f"/api/transactions/{transaction_id}/buyer-review",
        json={"rating": 5, "comment": "Item exactly as described."},
    )

    assert resp.status_code == 201
    data = resp.get_json()
    assert data["review"]["rating"] == 5
    assert data["review"]["comment"] == "Item exactly as described."
    assert data["review"]["reviewedUserId"] == seller_id
    assert data["review"]["reviewerId"] == buyer_id
    assert data["review"]["transactionId"] == transaction_id


def test_buyer_can_submit_review_without_comment(client):
    """AC1: comment is optional — omitting it still saves the rating."""
    test_client, test_db = client
    _seller_id, buyer_id, transaction_id = seed_completed_deal(test_db)
    login_as(test_client, buyer_id)

    resp = test_client.post(
        f"/api/transactions/{transaction_id}/buyer-review",
        json={"rating": 4},
    )

    assert resp.status_code == 201
    assert resp.get_json()["review"]["comment"] == ""


# ===========================================================================
# AC2: transaction is not completed
# ===========================================================================

def test_review_rejected_for_pending_offer_with_no_transaction(client):
    """AC2: no transaction exists yet (offer still Pending) -> rejected."""
    test_client, test_db = client
    _seller_id, buyer_id = seed_pending_offer(test_db)
    login_as(test_client, buyer_id)

    resp = test_client.post("/api/transactions/999999/buyer-review", json={"rating": 5})

    assert resp.status_code == 404
    assert "error" in resp.get_json()


def test_review_rejected_for_nonexistent_transaction(client):
    """AC2: an entirely unknown transaction id is rejected."""
    test_client, test_db = client
    _seller_id, buyer_id, _transaction_id = seed_completed_deal(test_db)
    login_as(test_client, buyer_id)

    resp = test_client.post("/api/transactions/999999/buyer-review", json={"rating": 5})

    assert resp.status_code == 404


# ===========================================================================
# AC3: review is linked to the completed transaction and the seller's profile
# ===========================================================================

def test_review_is_linked_to_transaction_and_seller_profile(client):
    """AC3: the saved review is retrievable from the seller's public review list."""
    test_client, test_db = client
    seller_id, buyer_id, transaction_id = seed_completed_deal(test_db)
    login_as(test_client, buyer_id)

    test_client.post(
        f"/api/transactions/{transaction_id}/buyer-review",
        json={"rating": 5, "comment": "Great seller."},
    )

    resp = test_client.get(f"/api/users/{seller_id}/reviews")

    assert resp.status_code == 200
    reviews = resp.get_json()["reviews"]
    assert len(reviews) == 1
    assert reviews[0]["reviewed_user_id"] == seller_id
    assert reviews[0]["reviewer_id"] == buyer_id
    assert reviews[0]["rating"] == 5

    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT transaction_id FROM reviews").fetchone()
    conn.close()
    assert row["transaction_id"] == transaction_id


# ===========================================================================
# AC4: rating outside 1-5 is rejected
# ===========================================================================

@pytest.mark.parametrize("bad_rating", [0, 6, -1, 4.5, "five", True, None])
def test_review_rejects_invalid_rating(client, bad_rating):
    """AC4: ratings outside 1-5, or non-integer, are rejected with an error."""
    test_client, test_db = client
    _seller_id, buyer_id, transaction_id = seed_completed_deal(test_db)
    login_as(test_client, buyer_id)

    resp = test_client.post(
        f"/api/transactions/{transaction_id}/buyer-review",
        json={"rating": bad_rating},
    )

    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_review_rejects_missing_rating(client):
    """AC4: a request with no rating field at all is rejected."""
    test_client, test_db = client
    _seller_id, buyer_id, transaction_id = seed_completed_deal(test_db)
    login_as(test_client, buyer_id)

    resp = test_client.post(f"/api/transactions/{transaction_id}/buyer-review", json={})

    assert resp.status_code == 400


# ===========================================================================
# AC5: buyer was not involved in the completed transaction
# ===========================================================================

def test_seller_cannot_submit_buyer_review(client):
    """AC5: the seller of the transaction is not its buyer -> rejected."""
    test_client, test_db = client
    seller_id, _buyer_id, transaction_id = seed_completed_deal(test_db)
    login_as(test_client, seller_id)

    resp = test_client.post(
        f"/api/transactions/{transaction_id}/buyer-review", json={"rating": 5}
    )

    assert resp.status_code == 403
    assert "error" in resp.get_json()


def test_unrelated_user_cannot_submit_buyer_review(client):
    """AC5: a user with no relation to the transaction is rejected."""
    test_client, test_db = client
    _seller_id, _buyer_id, transaction_id = seed_completed_deal(test_db)

    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    unrelated_user_id = _create_user(conn, "S1999999", "Unrelated")
    conn.commit()
    conn.close()

    login_as(test_client, unrelated_user_id)

    resp = test_client.post(
        f"/api/transactions/{transaction_id}/buyer-review", json={"rating": 5}
    )

    assert resp.status_code == 403


def test_unauthenticated_user_cannot_submit_buyer_review(client):
    """Unauthenticated request is rejected before any other check."""
    test_client, test_db = client
    _seller_id, _buyer_id, transaction_id = seed_completed_deal(test_db)

    resp = test_client.post(
        f"/api/transactions/{transaction_id}/buyer-review", json={"rating": 5}
    )

    assert resp.status_code == 401
