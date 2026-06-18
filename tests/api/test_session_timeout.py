"""Tests for 30-minute inactivity session timeout."""

import sqlite3
import time

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a Flask test client with an isolated test database."""
    test_db = tmp_path / "test_session_timeout.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client, test_db


def create_test_user(test_db):
    """Create and return an active test user ID."""
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
            "S11112222",
            "Session",
            "Tester",
            "SessionTester",
            "s11112222@mymail.nyp.edu.sg",
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


def set_logged_in_session(test_client, user_id, last_activity):
    """Set a logged-in session with a chosen last activity timestamp."""
    with test_client.session_transaction() as session:
        session["user_id"] = user_id
        session["email"] = "s11112222@mymail.nyp.edu.sg"
        session["display_name"] = "SessionTester"
        session["role"] = "user"
        session["last_activity"] = last_activity


def test_expired_session_redirects_to_login(client):
    """Expired sessions should be cleared and redirected to login."""
    test_client, test_db = client
    user_id = create_test_user(test_db)
    expired_time = time.time() - (31 * 60)

    set_logged_in_session(test_client, user_id, expired_time)

    response = test_client.get("/profile", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    with test_client.session_transaction() as session:
        assert "user_id" not in session


def test_active_session_before_30_minutes_can_access_profile(client):
    """Sessions with recent activity should remain logged in."""
    test_client, test_db = client
    user_id = create_test_user(test_db)
    active_time = time.time() - (10 * 60)

    set_logged_in_session(test_client, user_id, active_time)

    response = test_client.get("/profile")

    assert response.status_code == 200
    assert b"SessionTester" in response.data

    with test_client.session_transaction() as session:
        assert session["user_id"] == user_id
        assert session["last_activity"] > active_time