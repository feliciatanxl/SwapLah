"""API tests for per-user hasReviewed state in transaction history."""

# pylint: disable=redefined-outer-name

import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a Flask test client backed by an isolated temporary database."""
    test_db = tmp_path / "test_history_review_state.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client, test_db


def create_user(test_db, student_id, display_name):
    """Insert a user and return its ID."""
    conn = sqlite3.connect(test_db)
    cursor = conn.execute(
        """
        INSERT INTO users (student_id, first_name, last_name, display_name,
                           email, contact_number, password_hash, role, status)
        VALUES (?, ?, 'Test', ?, ?, '91234567', ?, 'user', 'Active')
        """,
        (student_id, display_name, display_name,
         f"{student_id.lower()}@mymail.nyp.edu.sg", generate_password_hash("Password1")),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def seed_completed_deal(test_db):
    """Seed a seller, buyer, listing and accept an offer; return their IDs."""
    seller_id = create_user(test_db, "S3200001", "Seller")
    buyer_id = create_user(test_db, "S3200002", "Buyer")
    conn = sqlite3.connect(test_db)
    conn.execute(
        """
        INSERT INTO listings (seller_id, title, description, price, category,
                              item_condition, image_url, listing_date, last_modified_timestamp)
        VALUES (?, 'Deal Item', 'desc', '20.00', 'Textbooks', 'Good', '[]',
                '2026-06-09 10:00:00', '2026-06-09 10:00:00')
        """,
        (seller_id,),
    )
    listing_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute(
        """
        INSERT INTO offers (listing_id, buyer_id, offer_type, proposed_price,
                            swap_listing_id, status, created_at)
        VALUES (?, ?, 'cash', 20.0, NULL, 'Pending', '2026-06-09 10:00:00')
        """,
        (listing_id, buyer_id),
    )
    offer_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()
    db_module.accept_offer(offer_id)
    return seller_id, buyer_id, offer_id


def login_as(test_client, user_id):
    """Log a user into the test session."""
    with test_client.session_transaction() as sess:
        sess["user_id"] = user_id


def get_transaction(test_client, role):
    """Return the first transaction dict for a role."""
    resp = test_client.get(f"/api/transactions?role={role}")
    assert resp.status_code == 200
    return resp.get_json()["transactions"][0]


def test_has_reviewed_is_false_before_reviewing(client):
    """A buyer who has not reviewed sees hasReviewed false and no reviewedAt."""
    test_client, test_db = client
    _seller_id, buyer_id, _offer_id = seed_completed_deal(test_db)
    login_as(test_client, buyer_id)

    transaction = get_transaction(test_client, "buyer")
    assert transaction["hasReviewed"] is False
    assert transaction["reviewedAt"] is None


def test_has_reviewed_is_true_after_reviewing(client):
    """After the buyer reviews, hasReviewed is true with a Singapore reviewedAt."""
    test_client, test_db = client
    _seller_id, buyer_id, offer_id = seed_completed_deal(test_db)
    login_as(test_client, buyer_id)

    assert test_client.post(
        "/api/reviews", json={"offer_id": offer_id, "rating": 5}
    ).status_code == 201

    transaction = get_transaction(test_client, "buyer")
    assert transaction["hasReviewed"] is True
    assert transaction["reviewedAt"].endswith("+08:00")


def test_one_participant_review_does_not_mark_the_other(client):
    """The buyer reviewing does not flag the seller's side as reviewed."""
    test_client, test_db = client
    seller_id, buyer_id, offer_id = seed_completed_deal(test_db)

    login_as(test_client, buyer_id)
    assert test_client.post(
        "/api/reviews", json={"offer_id": offer_id, "rating": 5}
    ).status_code == 201

    login_as(test_client, seller_id)
    seller_transaction = get_transaction(test_client, "seller")
    assert seller_transaction["hasReviewed"] is False


def test_transactions_expose_offer_id_for_review_actions(client):
    """Each transaction carries the offerId the review modal needs."""
    test_client, test_db = client
    _seller_id, buyer_id, offer_id = seed_completed_deal(test_db)
    login_as(test_client, buyer_id)

    transaction = get_transaction(test_client, "buyer")
    assert transaction["offerId"] == offer_id
