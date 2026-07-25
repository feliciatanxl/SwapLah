"""Unit tests for profile/cover image database helpers."""

# pylint: disable=redefined-outer-name

import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app.db import get_user_by_id, update_user_account, update_user_images


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Point database helpers at an isolated SQLite database."""
    db_path = tmp_path / "profile_images_unit.db"
    monkeypatch.setattr(db_module, "DATABASE", db_path)
    db_module.init_db()
    return db_path


def create_user(test_db):
    """Insert a user and return its ID."""
    conn = sqlite3.connect(test_db)
    cursor = conn.execute(
        """
        INSERT INTO users (student_id, first_name, last_name, display_name,
                           email, contact_number, password_hash, role, status)
        VALUES ('S7000001','Image','User','ImageUser','s7000001@mymail.nyp.edu.sg',
                '91234567', ?, 'user', 'Active')
        """,
        (generate_password_hash("Password1"),),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def test_new_user_has_null_image_fields(test_db):
    """A freshly created user starts with no configured images."""
    user_id = create_user(test_db)
    user = get_user_by_id(user_id)
    assert user["profile_image_url"] is None
    assert user["cover_image_url"] is None


def test_update_user_images_persists_values(test_db):
    """Saved image URLs are retrievable through get_user_by_id."""
    user_id = create_user(test_db)
    update_user_images(user_id, "https://example.com/a.jpg", "https://example.com/c.jpg")

    user = get_user_by_id(user_id)
    assert user["profile_image_url"] == "https://example.com/a.jpg"
    assert user["cover_image_url"] == "https://example.com/c.jpg"


def test_updating_account_details_preserves_images(test_db):
    """Editing normal profile fields does not clear stored images."""
    user_id = create_user(test_db)
    update_user_images(user_id, "https://example.com/a.jpg", "https://example.com/c.jpg")

    update_user_account(
        user_id=user_id,
        first_name="Changed",
        last_name="Name",
        display_name="ChangedName",
        contact_number="98765432",
    )

    user = get_user_by_id(user_id)
    assert user["display_name"] == "ChangedName"
    assert user["profile_image_url"] == "https://example.com/a.jpg"
    assert user["cover_image_url"] == "https://example.com/c.jpg"


def test_images_can_be_cleared_back_to_null(test_db):
    """Storing None clears an image back to the default state."""
    user_id = create_user(test_db)
    update_user_images(user_id, "https://example.com/a.jpg", "https://example.com/c.jpg")
    update_user_images(user_id, None, None)

    user = get_user_by_id(user_id)
    assert user["profile_image_url"] is None
    assert user["cover_image_url"] is None
