"""API/template tests: the profile Avg rating card shows a clean one-dp value."""

# pylint: disable=redefined-outer-name

import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a Flask test client backed by an isolated temporary database."""
    test_db = tmp_path / "test_profile_rating_format.db"
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


def login_as(test_client, user_id):
    """Log a user into the test session."""
    with test_client.session_transaction() as sess:
        sess["user_id"] = user_id


def seed_seller_with_repeating_average(test_db):
    """Create a seller whose average is 8/3 = 2.666... and return the id."""
    seller_id = create_user(test_db, "S2000001", "Seller")
    for index, rating in enumerate((3, 3, 2)):
        reviewer = create_user(test_db, f"S200001{index}", f"Rev{index}")
        add_review(test_db, reviewer, seller_id, rating)
    return seller_id


def test_own_profile_shows_rounded_average_not_raw_decimal(client):
    """The owner's Avg rating card shows 2.7, never the raw repeating decimal."""
    test_client, test_db = client
    seller_id = seed_seller_with_repeating_average(test_db)
    login_as(test_client, seller_id)

    html = test_client.get("/profile").get_data(as_text=True)
    assert "2.7" in html
    assert "2.6666" not in html


def test_public_profile_shows_same_rounded_average(client):
    """A viewer sees the same rounded 2.7 average on the public profile."""
    test_client, test_db = client
    seller_id = seed_seller_with_repeating_average(test_db)
    viewer_id = create_user(test_db, "S2000099", "Viewer")
    login_as(test_client, viewer_id)

    html = test_client.get(f"/profile/{seller_id}").get_data(as_text=True)
    assert "2.7" in html
    assert "2.6666" not in html


def test_profile_and_listing_seller_average_match(client):
    """The profile card average matches the listing-detail seller rating."""
    test_client, test_db = client
    seller_id = seed_seller_with_repeating_average(test_db)
    listing = db_module.create_listing(
        seller_id, "Item", "desc", "20.00", "Textbooks", "Good", "[]")

    login_as(test_client, seller_id)
    profile_html = test_client.get("/profile").get_data(as_text=True)
    listing_data = test_client.get(f"/api/listings/{listing['id']}").get_json()

    assert "2.7" in profile_html
    assert listing_data["listing"]["sellerRating"]["average_rating"] == 2.7
    assert "2.6666" not in profile_html


def test_zero_reviews_shows_empty_state(client):
    """A profile with no reviews shows the empty state, not a number."""
    test_client, test_db = client
    user_id = create_user(test_db, "S2000002", "Fresh")
    login_as(test_client, user_id)

    html = test_client.get("/profile").get_data(as_text=True)
    assert "No reviews yet" in html


def test_whole_number_average_renders_without_trailing_zero(client):
    """A whole-number average renders as 4 via the shared format_rating filter."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S2000003", "Seller")
    for index, rating in enumerate((4, 4, 4)):
        reviewer = create_user(test_db, f"S200030{index}", f"Rev{index}")
        add_review(test_db, reviewer, seller_id, rating)
    login_as(test_client, seller_id)

    html = test_client.get("/profile").get_data(as_text=True)
    assert "4<span" in html  # "4" immediately before the /5 suffix span
    assert "4.0<span" not in html
