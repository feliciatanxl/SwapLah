"""API/template tests for seller and reviewer avatar propagation."""

# pylint: disable=redefined-outer-name

import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app
from app.db import create_listing, create_review, update_user_images

SELLER_IMG = "https://cdn.example.com/seller.png"
REVIEWER_IMG = "https://cdn.example.com/reviewer.png"
NEW_IMG = "https://cdn.example.com/updated.png"


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a Flask test client backed by an isolated temporary database."""
    test_db = tmp_path / "avatar_propagation.db"
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


def login_as(test_client, user_id):
    """Authenticate a test session before accessing protected listing routes."""
    with test_client.session_transaction() as session:
        session["user_id"] = user_id
        session["email"] = f"user{user_id}@mymail.nyp.edu.sg"
        session["display_name"] = f"User {user_id}"
        session["role"] = "user"


# --- Listing seller avatar ----------------------------------------------

def test_listing_page_renders_seller_image(client):
    """The listing detail page shows the seller's saved profile image."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S9400001", "Seller", SELLER_IMG)
    login_as(test_client, seller_id)
    listing = create_listing(seller_id, "Item", "desc", "20.00", "Textbooks", "Good", "[]")

    page = test_client.get(f"/listing/{listing['id']}").get_data(as_text=True)
    assert SELLER_IMG in page
    assert "avatar-img" in page


def test_listing_page_seller_fallback_and_details(client):
    """Without a seller image, initials show and contact/rating still render."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S9400002", "Seller")
    login_as(test_client, seller_id)
    reviewer_id = create_user(test_db, "S9400003", "Reviewer")
    create_review(offer_id=None, reviewer_id=reviewer_id, reviewed_user_id=seller_id,
                  rating=5, comment="Great")
    listing = create_listing(seller_id, "Item", "desc", "20.00", "Textbooks", "Good", "[]")

    page = test_client.get(f"/listing/{listing['id']}").get_data(as_text=True)
    assert '<span class="avatar-mini">' in page
    assert "avatar-img" not in page
    assert "s9400002@mymail.nyp.edu.sg" in page
    assert "91234567" in page
    assert "average rating" in page


def test_listing_json_api_includes_seller_profile_image(client):
    """The JSON listing-detail API exposes the seller profile image URL."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S9400004", "Seller", SELLER_IMG)
    login_as(test_client, seller_id)
    listing = create_listing(seller_id, "Item", "desc", "20.00", "Textbooks", "Good", "[]")

    data = test_client.get(f"/api/listings/{listing['id']}").get_json()
    assert data["listing"]["seller"]["profileImageUrl"] == SELLER_IMG


# --- Reviewer avatar on profile -----------------------------------------

def test_profile_review_card_renders_reviewer_image(client):
    """A review card on the reviewed user's profile shows the reviewer image."""
    test_client, test_db = client
    reviewed_id = create_user(test_db, "S9400005", "Reviewed")
    reviewer_id = create_user(test_db, "S9400006", "Reviewer", REVIEWER_IMG)
    create_review(offer_id=None, reviewer_id=reviewer_id, reviewed_user_id=reviewed_id,
                  rating=5, comment="Nice")

    page = test_client.get(f"/profile/{reviewed_id}").get_data(as_text=True)
    assert REVIEWER_IMG in page


def test_profile_review_card_reviewer_fallback(client):
    """A reviewer without an image shows the initials fallback on the review card."""
    test_client, test_db = client
    reviewed_id = create_user(test_db, "S9400007", "Reviewed")
    reviewer_id = create_user(test_db, "S9400008", "Reviewer")
    create_review(offer_id=None, reviewer_id=reviewer_id, reviewed_user_id=reviewed_id,
                  rating=4, comment="Fine")

    page = test_client.get(f"/profile/{reviewed_id}").get_data(as_text=True)
    assert 'class="offer-avatar bg-soft-blue text-blue"' in page


def test_changing_reviewer_image_updates_existing_review_card(client):
    """Updating a reviewer's image changes their existing review card image."""
    test_client, test_db = client
    reviewed_id = create_user(test_db, "S9400009", "Reviewed")
    reviewer_id = create_user(test_db, "S9400010", "Reviewer")
    create_review(offer_id=None, reviewer_id=reviewer_id, reviewed_user_id=reviewed_id,
                  rating=5, comment="Great")

    before = test_client.get(f"/profile/{reviewed_id}").get_data(as_text=True)
    assert NEW_IMG not in before

    update_user_images(reviewer_id, NEW_IMG, None)

    after = test_client.get(f"/profile/{reviewed_id}").get_data(as_text=True)
    assert NEW_IMG in after


def test_reviews_api_includes_reviewer_profile_image(client):
    """GET /api/users/<id>/reviews includes the reviewer profile image field."""
    test_client, test_db = client
    reviewed_id = create_user(test_db, "S9400011", "Reviewed")
    reviewer_id = create_user(test_db, "S9400012", "Reviewer", REVIEWER_IMG)
    create_review(offer_id=None, reviewer_id=reviewer_id, reviewed_user_id=reviewed_id,
                  rating=5, comment="Nice")

    reviews = test_client.get(f"/api/users/{reviewed_id}/reviews").get_json()["reviews"]
    assert reviews[0]["reviewer_profile_image_url"] == REVIEWER_IMG
