"""Unit tests for user administration helpers."""

from datetime import datetime, timedelta

import pytest
from werkzeug.security import generate_password_hash

from app import db as app_db
from app import user_admin


def create_test_user(email, student_id, display_name="Test User", status="Active"):
    """Create a test user and return the user ID."""
    conn = app_db.get_db_connection()
    cursor = conn.execute(
        """
        INSERT INTO users (
            student_id,
            first_name,
            last_name,
            display_name,
            email,
            contact_number,
            password_hash,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            student_id,
            "Test",
            "User",
            display_name,
            email,
            "91234567",
            generate_password_hash("password123"),
            status,
        ),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def test_get_all_users_empty(tmp_path, monkeypatch):
    """get_all_users returns empty list when no users exist."""
    test_db = tmp_path / "test_swaplah.db"
    monkeypatch.setattr(app_db, "DATABASE", test_db)

    app_db.init_db()

    users = user_admin.get_all_users()

    assert users == []


def test_get_all_users_returns_all_users_excluding_password_hash(tmp_path, monkeypatch):
    """get_all_users returns all seeded users, each without password_hash."""
    test_db = tmp_path / "test_swaplah.db"
    monkeypatch.setattr(app_db, "DATABASE", test_db)

    app_db.init_db()

    user1_id = create_test_user("alice@example.com", "S001", "Alice")
    user2_id = create_test_user("bob@example.com", "S002", "Bob")

    users = user_admin.get_all_users()

    assert len(users) == 2

    # Find each user by id and verify fields
    alice = next(u for u in users if u["id"] == user1_id)
    bob = next(u for u in users if u["id"] == user2_id)

    assert alice["student_id"] == "S001"
    assert alice["display_name"] == "Alice"
    assert alice["email"] == "alice@example.com"
    assert alice["status"] == "Active"
    assert alice["role"] == "user"  # assuming default role is 'user'
    assert "created_at" in alice
    assert "password_hash" not in alice

    assert bob["student_id"] == "S002"
    assert bob["display_name"] == "Bob"
    assert "password_hash" not in bob


def test_get_all_users_orders_by_created_at_desc(tmp_path, monkeypatch):
    """get_all_users returns newest user first."""
    test_db = tmp_path / "test_swaplah.db"
    monkeypatch.setattr(app_db, "DATABASE", test_db)

    app_db.init_db()

    # Insert two users with explicit created_at times
    now = datetime.now()
    earlier = now - timedelta(seconds=10)
    later = now

    conn = app_db.get_db_connection()
    # Insert older user
    conn.execute(
        """
        INSERT INTO users (
            student_id, first_name, last_name, display_name, email,
            contact_number, password_hash, status, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "S003",
            "Old",
            "User",
            "OldUser",
            "old@example.com",
            "91234567",
            generate_password_hash("pass"),
            "Active",
            earlier.isoformat(),
        ),
    )
    # Insert newer user
    conn.execute(
        """
        INSERT INTO users (
            student_id, first_name, last_name, display_name, email,
            contact_number, password_hash, status, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "S004",
            "New",
            "User",
            "NewUser",
            "new@example.com",
            "91234567",
            generate_password_hash("pass"),
            "Active",
            later.isoformat(),
        ),
    )
    conn.commit()
    conn.close()

    users = user_admin.get_all_users()

    assert len(users) == 2
    assert users[0]["display_name"] == "NewUser"
    assert users[1]["display_name"] == "OldUser"


def test_update_user_status_flips_active_to_suspended(tmp_path, monkeypatch):
    """update_user_status changes Active to Suspended and returns updated dict."""
    test_db = tmp_path / "test_swaplah.db"
    monkeypatch.setattr(app_db, "DATABASE", test_db)

    app_db.init_db()

    user_id = create_test_user("flip@example.com", "S005", "FlipUser", status="Active")

    updated = user_admin.update_user_status(user_id, "Suspended")

    assert updated is not None
    assert updated["id"] == user_id
    assert updated["status"] == "Suspended"

    # Verify in DB
    conn = app_db.get_db_connection()
    row = conn.execute("SELECT status FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    assert row["status"] == "Suspended"


def test_update_user_status_flips_suspended_to_active(tmp_path, monkeypatch):
    """update_user_status changes Suspended to Active and returns updated dict."""
    test_db = tmp_path / "test_swaplah.db"
    monkeypatch.setattr(app_db, "DATABASE", test_db)

    app_db.init_db()

    user_id = create_test_user("flip2@example.com", "S006", "FlipUser2", status="Suspended")

    updated = user_admin.update_user_status(user_id, "Active")

    assert updated is not None
    assert updated["id"] == user_id
    assert updated["status"] == "Active"

    conn = app_db.get_db_connection()
    row = conn.execute("SELECT status FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    assert row["status"] == "Active"


def test_update_user_status_invalid_status_raises_valueerror_no_db_change(tmp_path, monkeypatch):
    """Invalid status raises ValueError and leaves DB unchanged."""
    test_db = tmp_path / "test_swaplah.db"
    monkeypatch.setattr(app_db, "DATABASE", test_db)

    app_db.init_db()

    user_id = create_test_user("invalid@example.com", "S007", "InvalidUser", status="Active")

    with pytest.raises(ValueError, match="Invalid status"):
        user_admin.update_user_status(user_id, "Banned")

    # Verify status unchanged
    conn = app_db.get_db_connection()
    row = conn.execute("SELECT status FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    assert row["status"] == "Active"


def test_update_user_status_nonexistent_user_returns_none(tmp_path, monkeypatch):
    """update_user_status returns None when user_id does not exist."""
    test_db = tmp_path / "test_swaplah.db"
    monkeypatch.setattr(app_db, "DATABASE", test_db)

    app_db.init_db()

    result = user_admin.update_user_status(999999, "Active")
    assert result is None