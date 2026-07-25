"""Fast API tests for seller avatar, rating, and time on homepage listing cards.

The homepage now renders listing cards client-side from the /api/listings
JSON payload (see app/templates/index.html), so these tests check that
payload directly rather than scraping server-rendered HTML. The client-side
formatting itself (avatar markup, rounded rating, Singapore time strings) is
exercised in a real browser by tests/ui/selenium/test_listing_detail_selenium.py
and the other Selenium specs.
"""

# pylint: disable=redefined-outer-name

import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app

SELLER_IMG = "https://cdn.example.com/seller.png"


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


def login_as(test_client, user_id, display_name="Listing Viewer"):
    """Authenticate a test session before accessing protected homepage listings."""
    with test_client.session_transaction() as session:
        session["user_id"] = user_id
        session["email"] = f"user{user_id}@mymail.nyp.edu.sg"
        session["display_name"] = display_name
        session["role"] = "user"


def insert_listing(test_db, seller_id, title, *, listing_date="2026-07-24 04:46:00",
                   last_modified_timestamp=None, category="Textbooks", condition="Good"):
    """Insert a listing with a fixed UTC listing_date and return its ID."""
    conn = sqlite3.connect(test_db)
    cursor = conn.execute(
        """
        INSERT INTO listings (seller_id, title, description, price, category,
                              item_condition, image_url, listing_date, last_modified_timestamp)
        VALUES (?, ?, 'desc', '20.00', ?, ?, '["https://e.com/a.jpg"]', ?, ?)
        """,
        (
            seller_id, title, category, condition, listing_date,
            last_modified_timestamp or listing_date,
        ),
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
    """A listing card's API payload includes the seller's saved image URL."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S9900001", "Kai", SELLER_IMG)
    login_as(test_client, seller_id, "Kai")
    insert_listing(test_db, seller_id, "Imaged Item")

    data = test_client.get("/api/listings").get_json()
    assert data["listings"][0]["sellerProfileImageUrl"] == SELLER_IMG


def test_card_uses_initials_fallback_without_image(client):
    """A card for a seller with no image has a null seller image URL."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S9900002", "Nora")
    login_as(test_client, seller_id, "Nora")
    insert_listing(test_db, seller_id, "Plain Item")

    data = test_client.get("/api/listings").get_json()
    assert data["listings"][0]["sellerProfileImageUrl"] is None


def test_card_shows_seller_name(client):
    """The API payload includes the seller's display name."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S9900003", "Kai", SELLER_IMG)
    login_as(test_client, seller_id, "Kai")
    insert_listing(test_db, seller_id, "Named Item")

    data = test_client.get("/api/listings").get_json()
    assert data["listings"][0]["seller"] == "Kai"


def test_card_shows_formatted_rating_when_reviews_exist(client):
    """A seller with reviews has a pre-rounded average, not a long float."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S9900004", "Kai", SELLER_IMG)
    login_as(test_client, seller_id, "Kai")
    reviewer_one = create_user(test_db, "S9900005", "R1")
    reviewer_two = create_user(test_db, "S9900006", "R2")
    insert_listing(test_db, seller_id, "Rated Item")
    add_review(test_db, reviewer_one, seller_id, 3)
    add_review(test_db, reviewer_two, seller_id, 2)

    data = test_client.get("/api/listings").get_json()
    listing = data["listings"][0]
    assert listing["sellerAvgRating"] == 2.5
    assert listing["sellerReviewCount"] == 2


def test_card_shows_new_when_no_reviews(client):
    """A seller with no reviews has a zero review count for the New fallback."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S9900007", "Kai", SELLER_IMG)
    login_as(test_client, seller_id, "Kai")
    insert_listing(test_db, seller_id, "Fresh Item", condition="Good")

    data = test_client.get("/api/listings").get_json()
    listing = data["listings"][0]
    assert not listing["sellerReviewCount"]
    assert listing["sellerAvgRating"] is None


def test_card_renders_singapore_time(client):
    """The API payload exposes the raw UTC listing date for client-side formatting."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S9900008", "Kai", SELLER_IMG)
    login_as(test_client, seller_id, "Kai")
    insert_listing(test_db, seller_id, "Timed Item", listing_date="2026-07-24 04:46:00")

    data = test_client.get("/api/listings").get_json()
    listing = data["listings"][0]
    assert listing["listingDate"] == "2026-07-24 04:46:00"
    assert listing["lastModifiedTimestamp"] == listing["listingDate"]


def test_card_renders_updated_time_when_listing_was_edited(client):
    """Edited listing cards expose a lastModifiedTimestamp distinct from listingDate."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S9900009", "Kai", SELLER_IMG)
    login_as(test_client, seller_id, "Kai")
    insert_listing(
        test_db,
        seller_id,
        "Edited Item",
        listing_date="2026-07-24 04:46:00",
        last_modified_timestamp="2026-07-24 05:46:00",
    )

    data = test_client.get("/api/listings").get_json()
    listing = data["listings"][0]
    assert listing["listingDate"] == "2026-07-24 04:46:00"
    assert listing["lastModifiedTimestamp"] == "2026-07-24 05:46:00"
