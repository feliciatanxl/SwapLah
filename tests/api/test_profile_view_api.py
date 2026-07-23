"""
API integration tests for GET /profile and GET /profile/<user_id>.

Uses a real temporary SQLite database with seeded users and reviews,
exercising the actual get_user_rating_stats() and get_reviews_for_user()
SQL and the is_own_profile template gating.
"""
import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "test_profile_view.db"
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


def create_review(test_db, reviewed_user_id, reviewer_id, rating, comment=""):
    conn = sqlite3.connect(test_db)
    conn.execute(
        """
        INSERT INTO reviews (reviewed_user_id, reviewer_id, rating, comment)
        VALUES (?, ?, ?, ?)
        """,
        (reviewed_user_id, reviewer_id, rating, comment),
    )
    conn.commit()
    conn.close()


def login_as(test_client, user_id):
    with test_client.session_transaction() as sess:
        sess["user_id"] = user_id


# ===========================================================================
# GET /profile — own profile
# ===========================================================================

def test_own_profile_shows_edit_controls_and_real_rating(client):
    """Own profile shows Edit Profile, Account Details, and the real rating."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S4000001", "Seller")
    reviewer_id = create_user(test_db, "S4000002", "Reviewer")
    create_review(test_db, seller_id, reviewer_id, rating=4)
    create_review(test_db, seller_id, reviewer_id, rating=4)

    login_as(test_client, seller_id)
    resp = test_client.get("/profile")
    html = resp.get_data(as_text=True)

    assert resp.status_code == 200
    assert "Edit profile" in html
    assert "Account Details" in html
    assert "Reviews (2)" in html


def test_own_profile_no_reviews_shows_empty_state(client):
    """A brand-new user viewing their own profile sees the empty review state."""
    test_client, test_db = client
    user_id = create_user(test_db, "S4000003", "NewUser")

    login_as(test_client, user_id)
    resp = test_client.get("/profile")
    html = resp.get_data(as_text=True)

    assert resp.status_code == 200
    assert "No reviews yet" in html
    assert "Reviews (0)" in html


def test_profile_redirects_to_login_when_logged_out(client):
    """An unauthenticated request to /profile redirects to the login page."""
    test_client, _test_db = client

    resp = test_client.get("/profile")

    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


# ===========================================================================
# GET /profile/<user_id> — another user's profile
# ===========================================================================

def test_other_profile_hides_edit_controls(client):
    """Viewing another user's profile hides Edit Profile and Account Details."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S4000004", "Seller")
    viewer_id = create_user(test_db, "S4000005", "Viewer")

    login_as(test_client, viewer_id)
    resp = test_client.get(f"/profile/{seller_id}")
    html = resp.get_data(as_text=True)

    assert resp.status_code == 200
    assert "Edit profile" not in html
    assert "Account Details" not in html


def test_other_profile_shows_real_average_rating_and_review(client):
    """Another user's profile shows their real average rating and review content."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S4000006", "Seller")
    viewer_id = create_user(test_db, "S4000007", "Viewer")
    create_review(test_db, seller_id, viewer_id, rating=5, comment="Great seller!")

    login_as(test_client, viewer_id)
    resp = test_client.get(f"/profile/{seller_id}")
    html = resp.get_data(as_text=True)

    assert resp.status_code == 200
    assert "Reviews (1)" in html
    assert "Great seller!" in html


def test_viewing_own_id_via_profile_id_route_redirects(client):
    """Requesting /profile/<own_id> redirects to /profile."""
    test_client, test_db = client
    user_id = create_user(test_db, "S4000008", "SelfViewer")

    login_as(test_client, user_id)
    resp = test_client.get(f"/profile/{user_id}")

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")


def test_unknown_user_profile_redirects_to_index(client):
    """Requesting a profile for a non-existent user redirects to the homepage."""
    test_client, test_db = client
    viewer_id = create_user(test_db, "S4000009", "Viewer")

    login_as(test_client, viewer_id)
    resp = test_client.get("/profile/999999")

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")


def test_logged_out_user_can_view_another_profile(client):
    """Viewing another user's profile does not require being logged in."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S4000010", "Seller")

    resp = test_client.get(f"/profile/{seller_id}")

    assert resp.status_code == 200
