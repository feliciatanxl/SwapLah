"""Unit tests for avatar-related fields in listing-detail and review queries."""

# pylint: disable=redefined-outer-name

import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app.db import (
    create_listing,
    create_review,
    get_listing_by_id,
    get_reviews_for_user,
    update_user_images,
)


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Point database helpers at an isolated SQLite database."""
    db_path = tmp_path / "avatar_db_unit.db"
    monkeypatch.setattr(db_module, "DATABASE", db_path)
    db_module.init_db()
    return db_path


def create_user(test_db, student_id, display_name, profile_image_url=None):
    """Insert a user (optionally with a profile image) and return its ID."""
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


def test_listing_detail_includes_seller_profile_image(test_db):
    """get_listing_by_id exposes the seller's stored profile image URL."""
    seller_id = create_user(test_db, "S9200001", "Seller", "https://cdn.example.com/s.png")
    listing = create_listing(seller_id, "Item", "desc", "20.00", "Textbooks", "Good", "[]")

    detail = get_listing_by_id(listing["id"])
    assert detail["seller_profile_image_url"] == "https://cdn.example.com/s.png"


def test_listing_detail_seller_image_is_none_when_unset(test_db):
    """A seller without an image yields a None seller_profile_image_url."""
    seller_id = create_user(test_db, "S9200002", "Seller")
    listing = create_listing(seller_id, "Item", "desc", "20.00", "Textbooks", "Good", "[]")

    detail = get_listing_by_id(listing["id"])
    assert detail["seller_profile_image_url"] is None


def test_reviews_include_reviewer_profile_image(test_db):
    """get_reviews_for_user exposes the reviewer's current profile image URL."""
    reviewed = create_user(test_db, "S9200003", "Reviewed")
    reviewer = create_user(test_db, "S9200004", "Reviewer", "https://cdn.example.com/r.png")
    create_review(offer_id=None, reviewer_id=reviewer, reviewed_user_id=reviewed,
                  rating=5, comment="Good")

    reviews = get_reviews_for_user(reviewed)
    assert reviews[0]["reviewer_profile_image_url"] == "https://cdn.example.com/r.png"


def test_changing_reviewer_image_updates_existing_reviews_without_row_edit(test_db):
    """Reviews read the live reviewer image; the review row is never rewritten."""
    reviewed = create_user(test_db, "S9200005", "Reviewed")
    reviewer = create_user(test_db, "S9200006", "Reviewer")
    create_review(offer_id=None, reviewer_id=reviewer, reviewed_user_id=reviewed,
                  rating=4, comment="Solid")

    assert get_reviews_for_user(reviewed)[0]["reviewer_profile_image_url"] is None

    update_user_images(reviewer, "https://cdn.example.com/new.png", None)

    reviews = get_reviews_for_user(reviewed)
    assert reviews[0]["reviewer_profile_image_url"] == "https://cdn.example.com/new.png"

    # The reviews table stores no image column - only the join changed.
    conn = sqlite3.connect(test_db)
    columns = [row[1] for row in conn.execute("PRAGMA table_info(reviews)")]
    conn.close()
    assert "profile_image_url" not in columns
    assert "reviewer_profile_image_url" not in columns


def test_reviewer_image_falls_back_to_none_for_deleted_reviewer(test_db):
    """A review whose reviewer_id is NULL yields a None image, not an error."""
    reviewed = create_user(test_db, "S9200007", "Reviewed")
    conn = sqlite3.connect(test_db)
    conn.execute(
        "INSERT INTO reviews (offer_id, reviewed_user_id, reviewer_id, rating, comment) "
        "VALUES (NULL, ?, NULL, 5, 'anon')",
        (reviewed,),
    )
    conn.commit()
    conn.close()

    reviews = get_reviews_for_user(reviewed)
    assert reviews[0]["reviewer_profile_image_url"] is None
