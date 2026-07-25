"""Unit tests: profile average rating is normalised to one decimal place."""

# pylint: disable=redefined-outer-name

import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app.db import create_review, get_user_profile_stats, get_user_rating_stats


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Point database helpers at an isolated SQLite database."""
    db_path = tmp_path / "profile_rating_round.db"
    monkeypatch.setattr(db_module, "DATABASE", db_path)
    db_module.init_db()
    return db_path


def create_user(test_db, student_id, display_name):
    """Insert a user and return its ID."""
    conn = sqlite3.connect(test_db)
    cursor = conn.execute(
        """
        INSERT INTO users (student_id, first_name, last_name, display_name, email,
                           contact_number, password_hash, role, status)
        VALUES (?, ?, 'Test', ?, ?, '91234567', ?, 'user', 'Active')
        """,
        (student_id, display_name, display_name,
         f"{student_id.lower()}@mymail.nyp.edu.sg", generate_password_hash("Password1")),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def review_with_ratings(test_db, reviewed_id, ratings):
    """Create one review per rating from distinct reviewers."""
    for index, rating in enumerate(ratings):
        reviewer = create_user(test_db, f"R{index}{reviewed_id:05d}", f"Rev{index}")
        create_review(offer_id=None, reviewer_id=reviewer, reviewed_user_id=reviewed_id,
                      rating=rating, comment="ok")


def test_repeating_decimal_average_rounds_to_one_dp(test_db):
    """An 8/3 = 2.666... average is normalised to 2.7."""
    user_id = create_user(test_db, "S1000001", "Seller")
    review_with_ratings(test_db, user_id, [3, 3, 2])  # sum 8 over 3 -> 2.666...

    assert get_user_profile_stats(user_id)["average_rating"] == 2.7


def test_whole_number_average_is_a_clean_float(test_db):
    """A whole-number average is a clean one-dp float (4.0), not a long value."""
    user_id = create_user(test_db, "S1000002", "Seller")
    review_with_ratings(test_db, user_id, [4, 4, 4])

    assert get_user_profile_stats(user_id)["average_rating"] == 4.0


def test_no_reviews_average_is_none(test_db):
    """With no reviews the average is None and the count is zero."""
    user_id = create_user(test_db, "S1000003", "Seller")
    stats = get_user_profile_stats(user_id)
    assert stats["average_rating"] is None
    assert stats["review_count"] == 0


def test_profile_and_seller_rating_helpers_match(test_db):
    """The profile stats average matches the listing seller rating average."""
    user_id = create_user(test_db, "S1000004", "Seller")
    review_with_ratings(test_db, user_id, [5, 4, 4])  # 13/3 -> 4.333 -> 4.3

    profile_avg = get_user_profile_stats(user_id)["average_rating"]
    seller_avg = get_user_rating_stats(user_id)["average_rating"]
    assert profile_avg == seller_avg == 4.3


def test_individual_review_ratings_are_not_rounded(test_db):
    """Only the average is rounded; stored review ratings remain integers."""
    user_id = create_user(test_db, "S1000005", "Seller")
    review_with_ratings(test_db, user_id, [3, 2])

    conn = sqlite3.connect(test_db)
    ratings = [r[0] for r in conn.execute(
        "SELECT rating FROM reviews WHERE reviewed_user_id=?", (user_id,))]
    conn.close()
    assert sorted(ratings) == [2, 3]
