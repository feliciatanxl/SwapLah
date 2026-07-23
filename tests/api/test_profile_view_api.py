"""Real-database integration tests for profile visibility and stats rendering."""

import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Create a Flask test client with an isolated profile database."""
    test_db = tmp_path / "test_profile_view.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client, test_db


def seed_user(test_db, student_id, email, display_name):
    """Create one user and return the generated ID."""
    conn = sqlite3.connect(test_db)
    cursor = conn.execute(
        """
        INSERT INTO users (
            student_id, first_name, last_name, display_name,
            email, contact_number, password_hash, role, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            student_id,
            "Profile",
            "User",
            display_name,
            email,
            "91234567",
            generate_password_hash("Password123"),
            "user",
            "Active",
        ),
    )
    conn.commit()
    conn.close()
    return cursor.lastrowid


def seed_review(test_db, reviewed_user_id, reviewer_id, rating):
    """Create one review for a user."""
    conn = sqlite3.connect(test_db)
    conn.execute(
        "INSERT INTO reviews (reviewed_user_id, reviewer_id, rating, comment) VALUES (?, ?, ?, ?)",
        (reviewed_user_id, reviewer_id, rating, ""),
    )
    conn.commit()
    conn.close()


def _login(test_client, user_id):
    """Set the logged-in user for a request."""
    with test_client.session_transaction() as session:
        session["user_id"] = user_id


def test_own_profile_shows_edit_profile_and_account_details(client):
    """A user viewing their own profile sees editable account controls."""
    test_client, test_db = client
    user_id = seed_user(test_db, "S30000001", "own@mymail.nyp.edu.sg", "OwnUser")
    _login(test_client, user_id)

    response = test_client.get("/profile")

    assert response.status_code == 200
    assert b"Edit profile" in response.data
    assert b"Account Details" in response.data


def test_other_profile_hides_edit_profile_and_account_details(client):
    """A user viewing someone else's profile does not see account controls."""
    test_client, test_db = client
    viewer_id = seed_user(test_db, "S30000002", "viewer@mymail.nyp.edu.sg", "Viewer")
    owner_id = seed_user(test_db, "S30000003", "owner@mymail.nyp.edu.sg", "Owner")
    _login(test_client, viewer_id)

    response = test_client.get(f"/profile/{owner_id}")

    assert response.status_code == 200
    assert b"Edit profile" not in response.data
    assert b"Account Details" not in response.data


def test_visiting_own_id_via_view_profile_route_redirects_to_profile(client):
    """Visiting /profile/<own_id> redirects to the canonical own-profile page."""
    test_client, test_db = client
    user_id = seed_user(test_db, "S30000004", "self@mymail.nyp.edu.sg", "SelfViewer")
    _login(test_client, user_id)

    response = test_client.get(f"/profile/{user_id}", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")


def test_profile_shows_no_reviews_yet_when_user_has_no_reviews(client):
    """A user with no reviews sees the empty-state message instead of a rating."""
    test_client, test_db = client
    viewer_id = seed_user(test_db, "S30000005", "viewer2@mymail.nyp.edu.sg", "Viewer2")
    owner_id = seed_user(test_db, "S30000006", "fresh@mymail.nyp.edu.sg", "FreshOwner")
    _login(test_client, viewer_id)

    response = test_client.get(f"/profile/{owner_id}")

    assert response.status_code == 200
    assert b"No reviews yet" in response.data


def test_profile_shows_average_rating_and_review_count_from_seeded_reviews(client):
    """Seeded reviews are aggregated into the displayed average rating and count."""
    test_client, test_db = client
    viewer_id = seed_user(test_db, "S30000007", "viewer3@mymail.nyp.edu.sg", "Viewer3")
    owner_id = seed_user(test_db, "S30000008", "rated@mymail.nyp.edu.sg", "RatedOwner")
    reviewer_id = seed_user(test_db, "S30000009", "reviewer3@mymail.nyp.edu.sg", "Reviewer3")
    seed_review(test_db, owner_id, reviewer_id, 4)
    seed_review(test_db, owner_id, reviewer_id, 5)
    _login(test_client, viewer_id)

    response = test_client.get(f"/profile/{owner_id}")

    assert response.status_code == 200
    assert b"4.5" in response.data
    assert b"2 reviews" in response.data


def test_missing_user_profile_redirects_to_index(client):
    """Viewing a profile for a user that does not exist redirects home with a flash."""
    test_client, test_db = client
    viewer_id = seed_user(test_db, "S30000010", "viewer4@mymail.nyp.edu.sg", "Viewer4")
    _login(test_client, viewer_id)

    response = test_client.get("/profile/999999", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
