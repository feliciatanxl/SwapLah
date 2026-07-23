"""API tests for admin user management endpoints."""

import sqlite3
import time

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Create a Flask test client with an isolated admin database."""
    test_db = tmp_path / "test_admin_users_api.db"
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
    user_id = cursor.lastrowid
    conn.close()
    return user_id


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


def test_admin_get_users_success(client):
    """Admin GET /admin/users returns all users without password_hash."""
    test_client, test_db = client
    admin_id = seed_user(test_db, role="admin")
    login_as(test_client, admin_id, "admin")

    # Create additional users
    user1 = seed_user(test_db, role="user", status="Active")
    user2 = seed_user(test_db, role="user", status="Suspended")

    response = test_client.get("/admin/users")
    assert response.status_code == 200
    data = response.get_json()
    assert "users" in data
    users = data["users"]
    assert len(users) == 3  # admin + two users

    # Check each user has expected fields and no password_hash
    for user in users:
        assert "student_id" in user
        assert "display_name" in user
        assert "email" in user
        assert "status" in user
        assert "role" in user
        assert "id" in user
        assert "password_hash" not in user

    # Verify raw response text does not contain password_hash
    assert "password_hash" not in response.text


def test_admin_get_users_403_non_admin(client):
    """Non-admin GET /admin/users returns 403."""
    test_client, test_db = client
    user_id = seed_user(test_db, role="user")
    login_as(test_client, user_id, "user")

    response = test_client.get("/admin/users")
    assert response.status_code == 403


def test_admin_get_users_redirect_unauthenticated(client):
    """Unauthenticated GET /admin/users redirects to login."""
    test_client, _ = client
    response = test_client.get("/admin/users", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_admin_post_status_active_to_suspended(client):
    """Admin POST /admin/users/<id>/status flips Active to Suspended."""
    test_client, test_db = client
    admin_id = seed_user(test_db, role="admin")
    login_as(test_client, admin_id, "admin")

    user_id = seed_user(test_db, role="user", status="Active")

    response = test_client.post(
        f"/admin/users/{user_id}/status",
        json={"status": "Suspended"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["user"]["id"] == user_id
    assert data["user"]["status"] == "Suspended"

    # Verify persistence via GET
    get_resp = test_client.get("/admin/users")
    users = get_resp.get_json()["users"]
    updated_user = next(u for u in users if u["id"] == user_id)
    assert updated_user["status"] == "Suspended"


def test_admin_post_status_suspended_to_active(client):
    """Admin POST /admin/users/<id>/status flips Suspended to Active."""
    test_client, test_db = client
    admin_id = seed_user(test_db, role="admin")
    login_as(test_client, admin_id, "admin")

    user_id = seed_user(test_db, role="user", status="Suspended")

    response = test_client.post(
        f"/admin/users/{user_id}/status",
        json={"status": "Active"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["user"]["status"] == "Active"

    # Verify persistence
    get_resp = test_client.get("/admin/users")
    users = get_resp.get_json()["users"]
    updated_user = next(u for u in users if u["id"] == user_id)
    assert updated_user["status"] == "Active"


def test_admin_post_status_invalid_400(client):
    """Admin POST with invalid status returns 400."""
    test_client, test_db = client
    admin_id = seed_user(test_db, role="admin")
    login_as(test_client, admin_id, "admin")

    user_id = seed_user(test_db, role="user", status="Active")

    response = test_client.post(
        f"/admin/users/{user_id}/status",
        json={"status": "Deleted"},
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert "error" in data

    # Verify user status unchanged
    get_resp = test_client.get("/admin/users")
    users = get_resp.get_json()["users"]
    user = next(u for u in users if u["id"] == user_id)
    assert user["status"] == "Active"


def test_admin_post_status_missing_body_400(client):
    """Admin POST with no JSON body returns 400."""
    test_client, test_db = client
    admin_id = seed_user(test_db, role="admin")
    login_as(test_client, admin_id, "admin")

    user_id = seed_user(test_db, role="user", status="Active")

    response = test_client.post(
        f"/admin/users/{user_id}/status",
        data="not json",  # no json
        content_type="application/json",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert "error" in data


def test_admin_post_status_nonexistent_user_404(client):
    """Admin POST with non-existent user_id returns 404."""
    test_client, test_db = client
    admin_id = seed_user(test_db, role="admin")
    login_as(test_client, admin_id, "admin")

    response = test_client.post(
        "/admin/users/999999/status",
        json={"status": "Active"},
    )
    assert response.status_code == 404
    data = response.get_json()
    assert data["success"] is False
    assert "error" in data


def test_non_admin_post_status_403_no_change(client):
    """Non-admin POST /admin/users/<id>/status returns 403 and does not change."""
    test_client, test_db = client
    # Create a non-admin user to log in
    user_id = seed_user(test_db, role="user", status="Active")
    login_as(test_client, user_id, "user")

    # Create a target user (different status to avoid unique email conflict)
    target_user = seed_user(test_db, role="user", status="Suspended")

    response = test_client.post(
        f"/admin/users/{target_user}/status",
        json={"status": "Active"},
    )
    assert response.status_code == 403

    # Verify with admin login that status unchanged (still Suspended)
    admin_id = seed_user(test_db, role="admin")
    login_as(test_client, admin_id, "admin")
    get_resp = test_client.get("/admin/users")
    users = get_resp.get_json()["users"]
    user = next(u for u in users if u["id"] == target_user)
    assert user["status"] == "Suspended"


def test_unauthenticated_post_status_redirect_or_401(client):
    """Unauthenticated POST /admin/users/<id>/status redirects or returns 401."""
    test_client, test_db = client
    # Create a user to target
    user_id = seed_user(test_db, role="user", status="Active")
    response = test_client.post(
        f"/admin/users/{user_id}/status",
        json={"status": "Suspended"},
        follow_redirects=False,
    )
    # The global before_request may return 401 or redirect; check either.
    assert response.status_code in (302, 401)
    if response.status_code == 302:
        assert "/login" in response.headers.get("Location", "")