"""Fast UI tests for seller avatar, rating, and time on homepage listing cards."""

# pylint: disable=redefined-outer-name

import re
import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app

SELLER_IMG = "https://cdn.example.com/seller.png"
STAR = r'bi-star-fill text-warning"></i>\s*'


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a Flask test client backed by an isolated temporary database."""
    test_db = tmp_path / "home_listing_card.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client, test_db


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


def insert_listing(test_db, seller_id, title, *, listing_date="2026-07-24 04:46:00",
                   category="Textbooks", condition="Good"):
    """Insert a listing with a fixed UTC listing_date and return its ID."""
    conn = sqlite3.connect(test_db)
    cursor = conn.execute(
        """
        INSERT INTO listings (seller_id, title, description, price, category,
                              item_condition, image_url, listing_date, last_modified_timestamp)
        VALUES (?, ?, 'desc', '20.00', ?, ?, '["https://e.com/a.jpg"]', ?, ?)
        """,
        (seller_id, title, category, condition, listing_date, listing_date),
    )
    conn.commit()
    listing_id = cursor.lastrowid
    conn.close()
    return listing_id


def add_review(test_db, reviewer_id, reviewed_id, rating):
    """Insert a review row directly."""
    conn = sqlite3.connect(test_db)
    conn.execute(
        "INSERT INTO reviews (offer_id, reviewed_user_id, reviewer_id, rating, comment) "
        "VALUES (NULL, ?, ?, ?, 'ok')",
        (reviewed_id, reviewer_id, rating),
    )
    conn.commit()
    conn.close()


def test_card_renders_saved_seller_image_via_macro(client):
    """A listing card shows the seller image using the reusable avatar macro."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S9900001", "Kai", SELLER_IMG)
    insert_listing(test_db, seller_id, "Imaged Item")

    page = test_client.get("/").get_data(as_text=True)
    assert SELLER_IMG in page
    assert 'class="avatar-mini me-1 avatar-img"' in page
    assert 'onerror="this.onerror=null;this.src=' in page


def test_card_uses_initials_fallback_without_image(client):
    """A card for a seller with no image shows the initials circle."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S9900002", "Nora")
    insert_listing(test_db, seller_id, "Plain Item")

    page = test_client.get("/").get_data(as_text=True)
    assert '<span class="avatar-mini me-1">N</span>' in page
    assert SELLER_IMG not in page


def test_card_shows_seller_name(client):
    """The seller display name renders beside the avatar."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S9900003", "Kai", SELLER_IMG)
    insert_listing(test_db, seller_id, "Named Item")

    assert "Kai" in test_client.get("/").get_data(as_text=True)


def test_card_shows_formatted_rating_when_reviews_exist(client):
    """A seller with reviews shows the formatted average, not a long float."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S9900004", "Kai", SELLER_IMG)
    reviewer_one = create_user(test_db, "S9900005", "R1")
    reviewer_two = create_user(test_db, "S9900006", "R2")
    insert_listing(test_db, seller_id, "Rated Item")
    add_review(test_db, reviewer_one, seller_id, 3)
    add_review(test_db, reviewer_two, seller_id, 2)

    page = test_client.get("/").get_data(as_text=True)
    assert re.search(STAR + r"2\.5", page)
    assert "2.50" not in page


def test_card_shows_new_when_no_reviews(client):
    """A seller with no reviews shows the New empty state beside the star."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S9900007", "Kai", SELLER_IMG)
    insert_listing(test_db, seller_id, "Fresh Item", condition="Good")

    page = test_client.get("/").get_data(as_text=True)
    assert re.search(STAR + r"New", page)


def test_card_renders_singapore_time(client):
    """The listing time uses the Singapore-time filter, not the raw UTC value."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S9900008", "Kai", SELLER_IMG)
    insert_listing(test_db, seller_id, "Timed Item", listing_date="2026-07-24 04:46:00")

    page = test_client.get("/").get_data(as_text=True)
    assert "24 Jul 2026, 12:46 PM" in page
    assert "2026-07-24 04:46:00" not in page
