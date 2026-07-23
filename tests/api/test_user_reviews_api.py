"""API tests for user review retrieval."""

import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Create a Flask test client with an isolated review database."""
    test_db = tmp_path / "test_user_reviews.db"
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


def seed_review(test_db, reviewed_user_id, reviewer_id):
    """Create one completed transaction and a review linked to it."""
    conn = sqlite3.connect(test_db)
    conn.execute(
        """
        INSERT INTO transactions (
            offer_id, listing_id, seller_id, buyer_id, transaction_type, amount
        )
        VALUES (1, 1, ?, ?, 'cash', 10.0)
        """,
        (reviewer_id, reviewed_user_id),
    )
    transaction_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()[0]
    conn.execute(
        """
        INSERT INTO reviews (transaction_id, reviewed_user_id, reviewer_id, rating, comment)
        VALUES (?, ?, ?, ?, ?)
        """,
        (transaction_id, reviewed_user_id, reviewer_id, 5, "Reliable campus seller."),
    )
    conn.commit()
    conn.close()


def test_get_user_reviews_returns_reviews(client):
    """GET /api/users/<id>/reviews returns public reviews for an existing user."""
    test_client, test_db = client
    reviewed_id = seed_user(test_db, "S10000001", "reviewed@mymail.nyp.edu.sg", "Reviewed")
    reviewer_id = seed_user(test_db, "S10000002", "reviewer@mymail.nyp.edu.sg", "Reviewer")
    seed_review(test_db, reviewed_id, reviewer_id)

    response = test_client.get(f"/api/users/{reviewed_id}/reviews")

    assert response.status_code == 200
    reviews = response.get_json()["reviews"]
    assert len(reviews) == 1
    assert reviews[0]["rating"] == 5
    assert reviews[0]["comment"] == "Reliable campus seller."
    assert reviews[0]["reviewer_display_name"] == "Reviewer"
    assert "password_hash" not in reviews[0]


def test_get_user_reviews_returns_empty_list_for_user_without_reviews(client):
    """GET /api/users/<id>/reviews returns an empty list when no reviews exist."""
    test_client, test_db = client
    user_id = seed_user(test_db, "S10000003", "noreviews@mymail.nyp.edu.sg", "NoReviews")

    response = test_client.get(f"/api/users/{user_id}/reviews")

    assert response.status_code == 200
    assert response.get_json() == {"reviews": []}


def test_get_user_reviews_returns_404_for_missing_user(client):
    """GET /api/users/<id>/reviews rejects an unknown user."""
    test_client, _ = client

    response = test_client.get("/api/users/999999/reviews")

    assert response.status_code == 404
    assert response.get_json() == {"error": "User not found."}
