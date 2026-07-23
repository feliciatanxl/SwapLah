"""API tests for server-side admin authorization."""

import sqlite3
import time

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Create a Flask test client with an isolated admin database."""
    test_db = tmp_path / "test_admin_authorization.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client, test_db


def seed_user(test_db, role="user", status="Active"):
    """Create one user with the supplied role/status and return its ID."""
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
            f"S{cursor_seed(role, status)}",
            "Admin",
            "Tester",
            f"{role}-{status}",
            f"{role}-{status}@mymail.nyp.edu.sg",
            "91234567",
            generate_password_hash("Password123"),
            role,
            status,
        ),
    )
    conn.commit()
    conn.close()
    return cursor.lastrowid


def cursor_seed(role, status):
    """Return a stable numeric suffix for test users."""
    return abs(hash((role, status))) % 90000000 + 10000000


def login_as(test_client, user_id, role):
    """Set a logged-in user session."""
    with test_client.session_transaction() as session:
        session["user_id"] = user_id
        session["email"] = f"user{user_id}@mymail.nyp.edu.sg"
        session["display_name"] = f"User {user_id}"
        session["role"] = role
        session["last_activity"] = time.time()


def test_admin_user_can_access_admin_page(client):
    """Active admins can access /admin."""
    test_client, test_db = client
    admin_id = seed_user(test_db, role="admin")
    login_as(test_client, admin_id, "admin")

    response = test_client.get("/admin")

    assert response.status_code == 200
    assert b"Admin" in response.data


def test_normal_user_is_denied_admin_page(client):
    """Logged-in non-admin users are denied server-side."""
    test_client, test_db = client
    user_id = seed_user(test_db, role="user")
    login_as(test_client, user_id, "user")

    response = test_client.get("/admin")

    assert response.status_code == 403


def test_unauthenticated_user_is_redirected_from_admin_page(client):
    """Logged-out users are redirected to login for /admin."""
    test_client, _ = client

    response = test_client.get("/admin", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_suspended_admin_is_denied_admin_page(client):
    """Suspended users are denied even if their session role says admin."""
    test_client, test_db = client
    user_id = seed_user(test_db, role="admin", status="Suspended")
    login_as(test_client, user_id, "admin")

    response = test_client.get("/admin")

    assert response.status_code == 403


def test_admin_subpath_is_protected_before_routing(client):
    """Admin subpaths require admin authorization even when the route is missing."""
    test_client, test_db = client
    user_id = seed_user(test_db, role="user")
    login_as(test_client, user_id, "user")

    response = test_client.get("/admin/users")

    assert response.status_code == 403
