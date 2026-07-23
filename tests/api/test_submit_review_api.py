"""Real-database integration tests for review submission and its effect on profile stats."""

import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Create a Flask test client with an isolated review database."""
    test_db = tmp_path / "test_submit_review.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client, test_db


def seed_user(test_db, student_id, email, display_name):
    """Create one user and return the generated ID."""
    conn = sqlite3.connect(test_db)
    cursor = conn.execute(
        """
        INSERT INTO users (
            student_id, first_name, last_name, display_name,
            email, contact_number, password_hash, role, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            student_id,
            "Review",
            "User",
            display_name,
            email,
            "91234567",
            generate_password_hash("Password123"),
            "user",
            "Active",
        ),
    )
    conn.commit()
    conn.close()
    return cursor.lastrowid


def seed_accepted_offer(test_db, seller_id, buyer_id):
    """Create a listing and an accepted offer between seller and buyer, return the offer ID."""
    conn = sqlite3.connect(test_db)
    listing_cursor = conn.execute(
        """
        INSERT INTO listings (
            seller_id, title, description, price, category, item_condition,
            image_url, listing_date, last_modified_timestamp, status
        )
        VALUES (?, 'Textbook', 'Used textbook', '10.00', 'Textbooks', 'Good',
                'https://example.com/image.png', '2026-07-01', '2026-07-01', 'Sold')
        """,
        (seller_id,),
    )
    listing_id = listing_cursor.lastrowid
    offer_cursor = conn.execute(
        """
        INSERT INTO offers (listing_id, buyer_id, offer_type, proposed_price, status)
        VALUES (?, ?, 'cash', 10.00, 'Accepted')
        """,
        (listing_id, buyer_id),
    )
    conn.commit()
    conn.close()
    return offer_cursor.lastrowid


def _login(test_client, user_id):
    """Set the logged-in user for a request."""
    with test_client.session_transaction() as session:
        session["user_id"] = user_id


def test_submitted_review_updates_reviewed_users_profile_stats(client):
    """Submitting a review is reflected in the reviewed user's average rating and count."""
    test_client, test_db = client
    seller_id = seed_user(test_db, "S20000001", "seller@mymail.nyp.edu.sg", "Seller")
    buyer_id = seed_user(test_db, "S20000002", "buyer@mymail.nyp.edu.sg", "Buyer")
    offer_id = seed_accepted_offer(test_db, seller_id, buyer_id)
    _login(test_client, buyer_id)

    response = test_client.post(
        "/api/reviews", json={"offer_id": offer_id, "rating": 4, "comment": "Smooth trade"}
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["average_rating"] == 4
    assert body["review_count"] == 1

    profile_response = test_client.get(f"/profile/{seller_id}")
    assert profile_response.status_code == 200
    assert b"1 review" in profile_response.data
    assert b"Smooth trade" in profile_response.data


def test_seller_review_of_buyer_appears_on_buyers_profile(client):
    """A seller-authored review is visible on the buyer's public profile."""
    test_client, test_db = client
    seller_id = seed_user(test_db, "S20000003", "seller2@mymail.nyp.edu.sg", "SellerTwo")
    buyer_id = seed_user(test_db, "S20000004", "buyer2@mymail.nyp.edu.sg", "BuyerTwo")
    offer_id = seed_accepted_offer(test_db, seller_id, buyer_id)
    _login(test_client, seller_id)

    response = test_client.post(
        "/api/reviews", json={"offer_id": offer_id, "rating": 5, "comment": "Great buyer"}
    )
    assert response.status_code == 201

    _login(test_client, 999999)
    profile_response = test_client.get(f"/profile/{buyer_id}")

    assert profile_response.status_code == 200
    assert b"SellerTwo" in profile_response.data
    assert b"Great buyer" in profile_response.data
