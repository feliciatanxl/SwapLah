"""Unit tests for internal password-reset database helpers."""

# pylint: disable=redefined-outer-name

import sqlite3

import pytest
from werkzeug.security import check_password_hash, generate_password_hash

import app.db as db_module
from app.db import get_user_by_id
from app.user_admin import get_user_for_password_reset, update_user_password

EMAIL = "s9500001@mymail.nyp.edu.sg"
STUDENT_ID = "S9500001"
CONTACT = "91234567"


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Point database helpers at an isolated SQLite database."""
    db_path = tmp_path / "password_reset_db_unit.db"
    monkeypatch.setattr(db_module, "DATABASE", db_path)
    db_module.init_db()
    return db_path


def create_user(test_db, status="Active", role="user"):
    """Insert a known user and return its ID."""
    conn = sqlite3.connect(test_db)
    cursor = conn.execute(
        """
        INSERT INTO users (student_id, first_name, last_name, display_name, email,
                           contact_number, password_hash, role, status)
        VALUES (?, 'Reset', 'User', 'ResetUser', ?, ?, ?, ?, ?)
        """,
        (STUDENT_ID, EMAIL, CONTACT, generate_password_hash("OldPassword1"), role, status),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def test_all_three_fields_matching_returns_user(test_db):
    """A correct email, Student ID and contact number resolve to the user."""
    user_id = create_user(test_db)
    match = get_user_for_password_reset(EMAIL, STUDENT_ID, CONTACT)
    assert match is not None
    assert match["id"] == user_id


def test_email_is_normalised_before_matching(test_db):
    """A mixed-case, padded email still matches the stored normalized address."""
    create_user(test_db)
    match = get_user_for_password_reset(f"  {STUDENT_ID}@MyMail.Nyp.Edu.Sg  ", STUDENT_ID, CONTACT)
    assert match is not None


def test_wrong_student_id_returns_none(test_db):
    """A mismatched Student ID yields no match."""
    create_user(test_db)
    assert get_user_for_password_reset(EMAIL, "S0000000", CONTACT) is None


def test_wrong_contact_number_returns_none(test_db):
    """A mismatched contact number yields no match."""
    create_user(test_db)
    assert get_user_for_password_reset(EMAIL, STUDENT_ID, "80000000") is None


def test_invalid_domain_returns_none(test_db):
    """A non-NYP email is rejected before any lookup."""
    create_user(test_db)
    assert get_user_for_password_reset("attacker@gmail.com", STUDENT_ID, CONTACT) is None


def test_unknown_email_returns_none(test_db):
    """An unknown but valid NYP email yields no match."""
    create_user(test_db)
    assert get_user_for_password_reset("s9999999@mymail.nyp.edu.sg", STUDENT_ID, CONTACT) is None


def test_update_user_password_hashes_and_preserves_role_status(test_db):
    """Updating the password stores a hash and leaves role and status untouched."""
    user_id = create_user(test_db, status="Suspended", role="admin")

    update_user_password(user_id, generate_password_hash("BrandNewPass1"))

    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()

    assert row["password_hash"] != "BrandNewPass1"
    assert check_password_hash(row["password_hash"], "BrandNewPass1")
    assert not check_password_hash(row["password_hash"], "OldPassword1")
    assert row["status"] == "Suspended"
    assert row["role"] == "admin"

    # The public user view is unaffected structurally.
    assert get_user_by_id(user_id)["status"] == "Suspended"
