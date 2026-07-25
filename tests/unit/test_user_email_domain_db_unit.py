"""Unit tests for user email validation and SQLite compatibility guards."""

# pylint: disable=redefined-outer-name

import sqlite3

import pytest
from werkzeug.security import check_password_hash, generate_password_hash

import app.db as db_module
from app import email_validation


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Create an isolated database with the current schema and guards."""
    db_path = tmp_path / "email_domain_unit.db"
    monkeypatch.setattr(db_module, "DATABASE", db_path)
    db_module.init_db()
    return db_path


def user_values(email, password_hash=None):
    """Return valid create_user arguments with a configurable email."""
    return (
        "S6000001",
        "Email",
        "Student",
        "EmailStudent",
        email,
        "91234567",
        password_hash or generate_password_hash("Password123"),
    )


@pytest.mark.parametrize(
    ("email", "expected"),
    [
        ("student@mymail.nyp.edu.sg", "student@mymail.nyp.edu.sg"),
        ("  STUDENT@MYMAIL.NYP.EDU.SG  ", "student@mymail.nyp.edu.sg"),
    ],
)
def test_normalize_student_email_accepts_exact_domain(email, expected):
    """Valid emails are stripped and normalized to lowercase."""
    assert email_validation.normalize_student_email(email) == expected
    assert email_validation.is_valid_student_email(email) is True


@pytest.mark.parametrize(
    "email",
    [
        "student@nyp.edu.sg",
        "student@mymail.nyp.edu.sg.attacker.com",
        "student@othermymail.nyp.edu.sg",
        "student@@mymail.nyp.edu.sg",
        "",
        "   ",
        None,
    ],
)
def test_normalize_student_email_rejects_invalid_or_missing_email(email):
    """Only one non-empty local part and the exact student domain are allowed."""
    with pytest.raises(ValueError, match="Email must end exactly"):
        email_validation.normalize_student_email(email)

    assert email_validation.is_valid_student_email(email) is False


def test_create_user_normalizes_email_and_preserves_password_hash(test_db):
    """The database helper stores canonical email and the supplied secure hash."""
    assert test_db.exists()
    password_hash = generate_password_hash("Password123")

    user = db_module.create_user(
        *user_values("  STUDENT@MYMAIL.NYP.EDU.SG  ", password_hash)
    )

    assert user["email"] == "student@mymail.nyp.edu.sg"
    assert user["password_hash"] != "Password123"
    assert check_password_hash(user["password_hash"], "Password123")


@pytest.mark.parametrize(
    "email",
    [
        "student@nyp.edu.sg",
        "student@mymail.nyp.edu.sg.attacker.com",
        "",
        None,
    ],
)
def test_create_user_rejects_invalid_email_before_insert(test_db, email):
    """Direct use of the create-user helper cannot bypass domain validation."""
    with pytest.raises(ValueError, match="Email must end exactly"):
        db_module.create_user(*user_values(email))

    conn = sqlite3.connect(test_db)
    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    assert user_count == 0


def test_new_schema_rejects_invalid_direct_sql_insert(test_db):
    """Raw SQL inserts are also protected for newly created databases."""
    conn = sqlite3.connect(test_db)

    with pytest.raises(sqlite3.IntegrityError, match="email must end exactly"):
        conn.execute(
            """
            INSERT INTO users (
                student_id, first_name, last_name, display_name,
                email, contact_number, password_hash
            )
            VALUES ('S6000002', 'Raw', 'Insert', 'RawInsert',
                    'raw@nyp.edu.sg', '91234567', 'hash')
            """
        )

    conn.close()


def test_database_guard_accepts_valid_email_with_uppercase_characters(test_db):
    """Raw legacy-style casing remains compatible when the domain is exact."""
    conn = sqlite3.connect(test_db)
    conn.execute(
        """
        INSERT INTO users (
            student_id, first_name, last_name, display_name,
            email, contact_number, password_hash
        )
        VALUES ('S6000005', 'Upper', 'Case', 'UpperCase',
                'Student@MYMAIL.NYP.EDU.SG', '91234567', 'hash')
        """
    )
    conn.commit()
    stored_email = conn.execute(
        "SELECT email FROM users WHERE student_id='S6000005'"
    ).fetchone()[0]
    conn.close()

    assert stored_email == "Student@MYMAIL.NYP.EDU.SG"


def test_init_db_adds_guards_without_deleting_legacy_users(tmp_path, monkeypatch):
    """Startup adds triggers to an old schema while retaining legacy rows."""
    db_path = tmp_path / "legacy_email_domain.db"
    monkeypatch.setattr(db_module, "DATABASE", db_path)
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL UNIQUE,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            display_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            contact_number TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            status TEXT NOT NULL DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        INSERT INTO users (
            student_id, first_name, last_name, display_name,
            email, contact_number, password_hash
        )
        VALUES ('S6000003', 'Legacy', 'User', 'LegacyUser',
                'legacy@nyp.edu.sg', '91234567', 'hash')
        """
    )
    conn.commit()
    conn.close()

    db_module.init_db()

    conn = sqlite3.connect(db_path)
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
    trigger_names = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='users'"
        ).fetchall()
    }
    assert trigger_names == {
        "validate_users_email_insert",
        "validate_users_email_update",
    }

    conn.execute("UPDATE users SET status='Suspended' WHERE student_id='S6000003'")
    conn.commit()
    status = conn.execute(
        "SELECT status FROM users WHERE student_id='S6000003'"
    ).fetchone()[0]
    assert status == "Suspended"
    with pytest.raises(sqlite3.IntegrityError, match="email must end exactly"):
        conn.execute(
            """
            INSERT INTO users (
                student_id, first_name, last_name, display_name,
                email, contact_number, password_hash
            )
            VALUES ('S6000004', 'New', 'Invalid', 'NewInvalid',
                    'new@nyp.edu.sg', '91234567', 'hash')
            """
        )
    conn.close()
