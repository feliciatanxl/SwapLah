"""API tests for the seller profile image field on GET /api/listings."""

# pylint: disable=redefined-outer-name

import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app
from app.db import create_listing

SELLER_IMG = "https://cdn.example.com/seller.png"


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a Flask test client backed by an isolated temporary database."""
    test_db = tmp_path / "test_listing_card_api.db"
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
    """Authenticate a test session before accessing protected listing APIs."""
    with test_client.session_transaction() as session:
        session["user_id"] = user_id
        session["email"] = f"user{user_id}@mymail.nyp.edu.sg"
        session["display_name"] = f"User {user_id}"
        session["role"] = "user"


def find_item(payload, title):
    """Return the listing item with the given title from an API payload."""
    return next(item for item in payload["listings"] if item["title"] == title)


def test_api_listings_includes_seller_profile_image(client):
    """GET /api/listings exposes the seller's saved profile image URL."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S9800001", "Kai", SELLER_IMG)
    login_as(test_client, seller_id)
    create_listing(seller_id, "Imaged Item", "desc", "20.00", "Textbooks", "Good", "[]")

    payload = test_client.get("/api/listings").get_json()
    assert find_item(payload, "Imaged Item")["sellerProfileImageUrl"] == SELLER_IMG


def test_api_listings_seller_image_null_when_absent(client):
    """A seller without an image serialises the field as null."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S9800002", "NoPic")
    login_as(test_client, seller_id)
    create_listing(seller_id, "Plain Item", "desc", "10.00", "Electronics", "New", "[]")

    payload = test_client.get("/api/listings").get_json()
    assert find_item(payload, "Plain Item")["sellerProfileImageUrl"] is None


def test_api_listings_preserves_existing_fields(client):
    """The added field does not disturb the existing listing serialisation."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S9800003", "Kai", SELLER_IMG)
    login_as(test_client, seller_id)
    create_listing(seller_id, "Full Item", "desc", "15.00", "Textbooks", "Good", "[]")

    item = find_item(test_client.get("/api/listings").get_json(), "Full Item")
    for key in (
        "id", "sellerId", "title", "description", "price", "category",
        "condition", "imageUrl", "listingDate", "lastModifiedTimestamp", "status",
    ):
        assert key in item
    assert item["sellerId"] == seller_id
    assert item["title"] == "Full Item"


def test_api_listings_search_and_filter_keep_seller_image(client):
    """Search and category/condition filters still return the seller image."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S9800004", "Kai", SELLER_IMG)
    login_as(test_client, seller_id)
    create_listing(seller_id, "Rare Book", "desc", "20.00", "Textbooks", "Good", "[]")
    create_listing(seller_id, "Mouse", "desc", "5.00", "Electronics", "New", "[]")

    searched = test_client.get("/api/listings?search=Rare").get_json()
    assert len(searched["listings"]) == 1
    assert searched["listings"][0]["sellerProfileImageUrl"] == SELLER_IMG

    filtered = test_client.get("/api/listings?category=Electronics&condition=New").get_json()
    assert len(filtered["listings"]) == 1
    assert filtered["listings"][0]["title"] == "Mouse"
    assert filtered["listings"][0]["sellerProfileImageUrl"] == SELLER_IMG


def test_api_listings_pagination_metadata_intact(client):
    """Pagination metadata still renders alongside the seller image field."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S9800005", "Kai", SELLER_IMG)
    login_as(test_client, seller_id)
    create_listing(seller_id, "Only Item", "desc", "20.00", "Textbooks", "Good", "[]")

    payload = test_client.get("/api/listings?page=1").get_json()
    assert payload["page"] == 1
    assert payload["totalListings"] == 1
    assert payload["listings"][0]["sellerProfileImageUrl"] == SELLER_IMG
