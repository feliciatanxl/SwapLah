"""Unit tests for seller avatar/rating fields on listing-card queries."""

# pylint: disable=redefined-outer-name

import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app.db import (
    create_listing,
    create_review,
    get_all_listings,
    search_active_listings,
    update_user_images,
)


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Point database helpers at an isolated SQLite database."""
    db_path = tmp_path / "listing_card_avatar.db"
    monkeypatch.setattr(db_module, "DATABASE", db_path)
    db_module.init_db()
    return db_path


def create_user(test_db, student_id, display_name, profile_image_url=None):
    """Insert a user and return its ID."""
    conn = sqlite3.connect(test_db)
    cursor = conn.execute(
        """
        INSERT INTO users (student_id, first_name, last_name, display_name, email,
                           contact_number, password_hash, role, status, profile_image_url)
        VALUES (?, ?, 'Test', ?, ?, '91234567', ?, 'user', 'Active', ?)
        """,
        (student_id, display_name, display_name,
         f"{student_id.lower()}@mymail.nyp.edu.sg",
         generate_password_hash("Password1"), profile_image_url),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def seed_listing(test_db, seller_id, title="Item", category="Textbooks", condition="Good"):
    """Create a listing owned by the seller and return it."""
    return create_listing(seller_id, title, "desc", "20.00", category, condition, "[]")


def test_active_listing_query_includes_seller_profile_image(test_db):
    """search_active_listings exposes the seller's saved profile image URL."""
    seller_id = create_user(test_db, "S9700001", "Kai", "https://cdn.example.com/kai.png")
    seed_listing(test_db, seller_id)

    rows = search_active_listings()
    assert rows[0]["seller_profile_image_url"] == "https://cdn.example.com/kai.png"


def test_get_all_listings_includes_seller_profile_image(test_db):
    """get_all_listings also carries the seller profile image URL."""
    seller_id = create_user(test_db, "S9700002", "Kai", "https://cdn.example.com/kai.png")
    seed_listing(test_db, seller_id)

    assert get_all_listings()[0]["seller_profile_image_url"] == "https://cdn.example.com/kai.png"


def test_search_result_includes_seller_profile_image(test_db):
    """A keyword search result carries the seller image."""
    seller_id = create_user(test_db, "S9700003", "Kai", "https://cdn.example.com/kai.png")
    seed_listing(test_db, seller_id, title="Rare Algorithms Book")

    rows = search_active_listings("Algorithms")
    assert len(rows) == 1
    assert rows[0]["seller_profile_image_url"] == "https://cdn.example.com/kai.png"


def test_category_and_condition_filter_include_seller_profile_image(test_db):
    """Category and condition filters still return the seller image."""
    seller_id = create_user(test_db, "S9700004", "Kai", "https://cdn.example.com/kai.png")
    seed_listing(test_db, seller_id, category="Electronics", condition="New")

    rows = search_active_listings("", "Electronics", "New")
    assert rows[0]["seller_profile_image_url"] == "https://cdn.example.com/kai.png"


def test_missing_seller_image_returns_none(test_db):
    """A seller without an image yields a None seller_profile_image_url."""
    seller_id = create_user(test_db, "S9700005", "NoPic")
    seed_listing(test_db, seller_id)

    assert search_active_listings()[0]["seller_profile_image_url"] is None


def test_updating_profile_image_changes_existing_listing_output(test_db):
    """Updating users.profile_image_url updates existing card output without a row edit."""
    seller_id = create_user(test_db, "S9700006", "Kai")
    listing = seed_listing(test_db, seller_id)

    assert search_active_listings()[0]["seller_profile_image_url"] is None

    update_user_images(seller_id, "https://cdn.example.com/new.png", None)
    assert search_active_listings()[0]["seller_profile_image_url"] == "https://cdn.example.com/new.png"

    # The listings row itself never stores a profile image.
    conn = sqlite3.connect(test_db)
    columns = [row[1] for row in conn.execute("PRAGMA table_info(listings)")]
    row_keys = conn.execute("SELECT * FROM listings WHERE id=?", (listing["id"],)).description
    conn.close()
    assert "profile_image_url" not in columns
    assert "seller_profile_image_url" not in columns
    assert not any(col[0].endswith("profile_image_url") for col in row_keys)


def test_query_reports_live_seller_rating(test_db):
    """The card query aggregates the seller's live rounded average and review count."""
    seller_id = create_user(test_db, "S9700007", "Kai")
    reviewer_one = create_user(test_db, "S9700008", "R1")
    reviewer_two = create_user(test_db, "S9700009", "R2")
    seed_listing(test_db, seller_id)
    create_review(offer_id=None, reviewer_id=reviewer_one, reviewed_user_id=seller_id,
                  rating=3, comment="ok")
    create_review(offer_id=None, reviewer_id=reviewer_two, reviewed_user_id=seller_id,
                  rating=2, comment="meh")

    row = search_active_listings()[0]
    assert row["seller_review_count"] == 2
    assert row["seller_avg_rating"] == 2.5


def test_query_reports_no_rating_when_no_reviews(test_db):
    """A seller with no reviews reports a zero count and NULL average."""
    seller_id = create_user(test_db, "S9700010", "Kai")
    seed_listing(test_db, seller_id)

    row = search_active_listings()[0]
    assert row["seller_review_count"] == 0
    assert row["seller_avg_rating"] is None
