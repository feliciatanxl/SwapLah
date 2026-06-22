"""Tests for blocking protected pages from logged-out users."""

import sqlite3
import time

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a Flask test client with an isolated test database."""
    test_db = tmp_path / "test_protected_pages.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client, test_db


def create_test_user(test_db):
    """Create and return a test user ID."""
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
            "S22223333",
            "Protected",
            "Tester",
            "ProtectedTester",
            "s22223333@mymail.nyp.edu.sg",
            "91234567",
            generate_password_hash("Password123"),
            "user",
            "Active",
        ),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def login_test_user(test_client, user_id):
    """Set a logged-in user session."""
    with test_client.session_transaction() as session:
        session["user_id"] = user_id
        session["email"] = "s22223333@mymail.nyp.edu.sg"
        session["display_name"] = "ProtectedTester"
        session["role"] = "user"
        session["last_activity"] = time.time()


@pytest.mark.parametrize(
    "protected_url",
    [
        "/profile",
        "/profile/edit",
        "/sell",
        "/offers",
        "/history",
    ],
)
def test_logged_out_user_is_redirected_from_protected_pages(client, protected_url):
    """Logged-out users should be redirected from protected pages."""
    test_client, _ = client

    response = test_client.get(protected_url, follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_logged_out_after_logout_cannot_access_profile(client):
    """Users should not access protected pages after logging out."""
    test_client, test_db = client
    user_id = create_test_user(test_db)
    login_test_user(test_client, user_id)

    logout_response = test_client.get("/logout", follow_redirects=False)
    profile_response = test_client.get("/profile", follow_redirects=False)

    assert logout_response.status_code == 302
    assert profile_response.status_code == 302
    assert "/login" in profile_response.headers["Location"]


def test_logged_in_user_can_access_sell_page(client):
    """Logged-in users should still access protected pages."""
    test_client, test_db = client
    user_id = create_test_user(test_db)
    login_test_user(test_client, user_id)

    response = test_client.get("/sell")

    assert response.status_code == 200