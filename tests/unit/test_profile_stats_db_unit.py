"""Unit tests for profile stats and review retrieval database functions."""

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    """Point the db module at an isolated temporary SQLite database."""
    monkeypatch.setattr(db_module, "DATABASE", tmp_path / "test_profile_stats.db")
    db_module.init_db()
    return db_module


def _create_user(db, display_name):
    """Insert a user and return their ID."""
    conn = db.get_db_connection()
    cursor = conn.execute(
        """
        INSERT INTO users (
            student_id, first_name, last_name, display_name,
            email, contact_number, password_hash, role, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"S{display_name}",
            display_name,
            "Test",
            display_name,
            f"{display_name.lower()}@mymail.nyp.edu.sg",
            "91234567",
            generate_password_hash("Password123"),
            "user",
            "Active",
        ),
    )
    conn.commit()
    conn.close()
    return cursor.lastrowid


def test_get_user_profile_stats_for_user_with_no_activity(isolated_db):
    """A brand new user has zeroed stats, no rating, and a New Seller badge."""
    user_id = _create_user(isolated_db, "NoActivity")

    stats = isolated_db.get_user_profile_stats(user_id)

    assert stats["active_count"] == 0
    assert stats["review_count"] == 0
    assert stats["average_rating"] is None
    assert stats["total_sales"] == 0
    assert stats["trust_badge"] == "New Seller"
    assert stats["response_rate"] is None


def test_get_user_profile_stats_computes_average_rating_and_review_count(isolated_db):
    """Average rating and review count reflect all reviews received by the user."""
    seller_id = _create_user(isolated_db, "Seller")
    buyer_id = _create_user(isolated_db, "Buyer")
    conn = isolated_db.get_db_connection()
    conn.execute(
        "INSERT INTO reviews (reviewed_user_id, reviewer_id, rating, comment) VALUES (?, ?, ?, ?)",
        (seller_id, buyer_id, 4, "Good"),
    )
    conn.execute(
        "INSERT INTO reviews (reviewed_user_id, reviewer_id, rating, comment) VALUES (?, ?, ?, ?)",
        (seller_id, buyer_id, 5, "Great"),
    )
    conn.commit()
    conn.close()

    stats = isolated_db.get_user_profile_stats(seller_id)

    assert stats["review_count"] == 2
    assert stats["average_rating"] == 4.5


def test_get_user_profile_stats_active_count_and_trust_badge(isolated_db):
    """Active listing count feeds the Active Seller trust badge."""
    seller_id = _create_user(isolated_db, "ActiveSeller")
    isolated_db.create_listing(
        seller_id=seller_id,
        title="Textbook",
        description="Used textbook",
        price="10.00",
        category="Textbooks",
        condition="Good",
        image_url="https://example.com/image.png",
    )

    stats = isolated_db.get_user_profile_stats(seller_id)

    assert stats["active_count"] == 1
    assert stats["trust_badge"] == "Active Seller"


def test_get_user_profile_stats_response_rate_from_responded_offers(isolated_db):
    """Response rate is the share of offers that are no longer pending.

    Two separate listings are used because accepting an offer auto-rejects
    other pending offers on the *same* listing, which would make every offer
    "responded to" regardless of the seller's own behaviour.
    """
    seller_id = _create_user(isolated_db, "Responder")
    buyer_id = _create_user(isolated_db, "Buyer2")
    responded_listing = isolated_db.create_listing(
        seller_id=seller_id,
        title="Calculator",
        description="Scientific calculator",
        price="20.00",
        category="Electronics",
        condition="Good",
        image_url="https://example.com/image.png",
    )
    still_pending_listing = isolated_db.create_listing(
        seller_id=seller_id,
        title="Notebook",
        description="Unused notebook",
        price="5.00",
        category="Stationery",
        condition="New",
        image_url="https://example.com/image.png",
    )
    accepted = isolated_db.create_offer(
        responded_listing["id"], buyer_id, "cash", proposed_price=20.00
    )
    isolated_db.create_offer(still_pending_listing["id"], buyer_id, "cash", proposed_price=5.00)
    isolated_db.accept_offer(accepted["id"])

    stats = isolated_db.get_user_profile_stats(seller_id)

    assert stats["response_rate"] == 50


def test_get_reviews_for_user_returns_only_that_users_reviews(isolated_db):
    """Reviews for one user do not leak into another user's review list."""
    user_a = _create_user(isolated_db, "UserA")
    user_b = _create_user(isolated_db, "UserB")
    reviewer = _create_user(isolated_db, "Reviewer")
    conn = isolated_db.get_db_connection()
    conn.execute(
        "INSERT INTO reviews (reviewed_user_id, reviewer_id, rating, comment) VALUES (?, ?, ?, ?)",
        (user_a, reviewer, 5, "Great trade"),
    )
    conn.execute(
        "INSERT INTO reviews (reviewed_user_id, reviewer_id, rating, comment) VALUES (?, ?, ?, ?)",
        (user_b, reviewer, 3, "Okay trade"),
    )
    conn.commit()
    conn.close()

    reviews = isolated_db.get_reviews_for_user(user_a)

    assert len(reviews) == 1
    assert reviews[0]["rating"] == 5
    assert reviews[0]["reviewer_name"] == "Reviewer"


def test_get_reviews_for_user_returns_empty_list_when_no_reviews(isolated_db):
    """A user with no reviews yields an empty list, not an error."""
    user_id = _create_user(isolated_db, "Fresh")

    reviews = isolated_db.get_reviews_for_user(user_id)

    assert reviews == []
