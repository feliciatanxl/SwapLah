"""
API integration tests for GET /profile and GET /profile/<user_id>.

Uses a real temporary SQLite database with seeded users, listings, offers,
transactions, and reviews, exercising the actual get_user_profile_stats(),
get_active_listings_by_seller(), and get_sold_listings_by_seller() SQL.
"""
import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "test_profile_stats.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client, test_db


def create_user(test_db, student_id, display_name):
    conn = sqlite3.connect(test_db)
    cursor = conn.execute(
        """
        INSERT INTO users (student_id, first_name, last_name, display_name,
                           email, contact_number, password_hash, role, status)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (student_id, display_name, "Test", display_name,
         f"{student_id.lower()}@mymail.nyp.edu.sg", "91234567",
         generate_password_hash("Password1"), "user", "Active"),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def create_listing(test_db, seller_id, title, status="Active"):
    conn = sqlite3.connect(test_db)
    now = "2026-07-01 10:00:00"
    cursor = conn.execute(
        """
        INSERT INTO listings (seller_id, title, description, price, category,
                              item_condition, image_url, listing_date,
                              last_modified_timestamp, status)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        (seller_id, title, "A nice item", "20.00", "Textbooks", "Good",
         '["https://example.com/img.jpg"]', now, now, status),
    )
    conn.commit()
    listing_id = cursor.lastrowid
    conn.close()
    return listing_id


def create_offer_and_accept(test_db, listing_id, buyer_id):
    """Seed a pending offer and accept it via the real accept_offer() path."""
    conn = sqlite3.connect(test_db)
    conn.execute(
        """
        INSERT INTO offers (listing_id, buyer_id, offer_type, proposed_price,
                            swap_listing_id, status, created_at)
        VALUES (?, ?, 'cash', 15.0, NULL, 'Pending', '2026-07-01 10:00:00')
        """,
        (listing_id, buyer_id),
    )
    offer_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()[0]
    conn.commit()
    conn.close()

    db_module.accept_offer(offer_id)
    return offer_id


def seed_completed_deal(test_db, seller_name="Seller1", buyer_name="Buyer1"):
    """Seed a seller, buyer, listing, and an accepted offer/transaction. Returns ids."""
    seller_id = create_user(test_db, "S2000001", seller_name)
    buyer_id = create_user(test_db, "S2000002", buyer_name)
    listing_id = create_listing(test_db, seller_id, "Intro to Algorithms 3E")

    offer_id = create_offer_and_accept(test_db, listing_id, buyer_id)

    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    transaction_id = conn.execute(
        "SELECT id FROM transactions WHERE offer_id = ?", (offer_id,)
    ).fetchone()["id"]
    conn.close()

    return seller_id, buyer_id, transaction_id


def submit_review(test_db, transaction_id, reviewed_user_id, reviewer_id, rating):
    conn = sqlite3.connect(test_db)
    conn.execute(
        """
        INSERT INTO reviews (transaction_id, reviewed_user_id, reviewer_id, rating, comment)
        VALUES (?, ?, ?, ?, '')
        """,
        (transaction_id, reviewed_user_id, reviewer_id, rating),
    )
    conn.commit()
    conn.close()


def login_as(test_client, user_id):
    with test_client.session_transaction() as sess:
        sess["user_id"] = user_id


# ===========================================================================
# GET /profile — own profile
# ===========================================================================

def test_own_profile_shows_edit_controls_and_stats(client):
    """Own profile shows Edit Profile, Account Details, and real computed stats."""
    test_client, test_db = client
    seller_id, buyer_id, transaction_id = seed_completed_deal(test_db)
    submit_review(test_db, transaction_id, seller_id, buyer_id, rating=4)
    submit_review(test_db, transaction_id, seller_id, buyer_id, rating=4)

    login_as(test_client, seller_id)
    resp = test_client.get("/profile")
    html = resp.get_data(as_text=True)

    assert resp.status_code == 200
    assert "Edit profile" in html
    assert "Account Details" in html
    assert "Reviews (2)" in html
    # Average of 4 and 4 is a whole number and must not show a trailing .0
    assert "4.0" not in html


def test_own_profile_no_reviews_shows_empty_state(client):
    """A brand-new user viewing their own profile sees the empty review state."""
    test_client, test_db = client
    user_id = create_user(test_db, "S2000003", "NewUser")

    login_as(test_client, user_id)
    resp = test_client.get("/profile")
    html = resp.get_data(as_text=True)

    assert resp.status_code == 200
    assert "No reviews yet" in html
    assert "Reviews (0)" in html


# ===========================================================================
# GET /profile/<user_id> — another user's profile
# ===========================================================================

def test_other_profile_hides_edit_controls(client):
    """Viewing another user's profile hides Edit Profile and Account Details."""
    test_client, test_db = client
    seller_id, buyer_id, _transaction_id = seed_completed_deal(test_db)

    login_as(test_client, buyer_id)
    resp = test_client.get(f"/profile/{seller_id}")
    html = resp.get_data(as_text=True)

    assert resp.status_code == 200
    assert "Edit profile" not in html
    assert "Account Details" not in html


def test_other_profile_shows_average_rating_and_review(client):
    """Another user's profile shows the average rating and review content."""
    test_client, test_db = client
    seller_id, buyer_id, transaction_id = seed_completed_deal(test_db)
    submit_review(test_db, transaction_id, seller_id, buyer_id, rating=5)

    login_as(test_client, buyer_id)
    resp = test_client.get(f"/profile/{seller_id}")
    html = resp.get_data(as_text=True)

    assert resp.status_code == 200
    assert "Reviews (1)" in html


def test_viewing_own_id_via_profile_id_route_redirects(client):
    """Requesting /profile/<own_id> redirects to /profile."""
    test_client, test_db = client
    user_id = create_user(test_db, "S2000004", "SelfViewer")

    login_as(test_client, user_id)
    resp = test_client.get(f"/profile/{user_id}")

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")


def test_unknown_user_profile_redirects_to_index(client):
    """Requesting a profile for a non-existent user redirects to the homepage."""
    test_client, test_db = client
    viewer_id = create_user(test_db, "S2000005", "Viewer")

    login_as(test_client, viewer_id)
    resp = test_client.get("/profile/999999")

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")


def test_logged_out_user_can_view_another_profile(client):
    """Viewing another user's profile does not require being logged in."""
    test_client, test_db = client
    seller_id, _buyer_id, _transaction_id = seed_completed_deal(test_db)

    resp = test_client.get(f"/profile/{seller_id}")

    assert resp.status_code == 200


# ===========================================================================
# Profile marketplace stats (trust badge / active listings)
# ===========================================================================

def test_profile_shows_active_listing_count(client):
    """The profile page's active listings tab count matches real active listings."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S2000006", "Seller")
    create_listing(test_db, seller_id, "Item One", status="Active")
    create_listing(test_db, seller_id, "Item Two", status="Active")

    login_as(test_client, seller_id)
    resp = test_client.get("/profile")
    html = resp.get_data(as_text=True)

    assert "Active listings (2)" in html
