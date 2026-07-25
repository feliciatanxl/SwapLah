"""API tests for registration and login email-domain enforcement."""

# pylint: disable=redefined-outer-name

import sqlite3

import pytest
from werkzeug.security import check_password_hash, generate_password_hash

import app.db as db_module
from app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a Flask client backed by an isolated current-schema database."""
    test_db = tmp_path / "email_domain_api.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)
    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client, test_db


def registration_data(email):
    """Return a complete registration form with a configurable email."""
    return {
        "student_id": "S7000001",
        "first_name": "Domain",
        "last_name": "Student",
        "display_name": "DomainStudent",
        "email": email,
        "contact_number": "91234567",
        "password": "Password123",
        "confirm_password": "Password123",
    }


def get_users(test_db):
    """Return all user rows from a test database."""
    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    users = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
    conn.close()
    return users


def test_registration_accepts_valid_student_email(client):
    """The exact student email domain is accepted."""
    test_client, test_db = client

    response = test_client.post(
        "/register",
        data=registration_data("student@mymail.nyp.edu.sg"),
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.location.endswith("/login")
    assert get_users(test_db)[0]["email"] == "student@mymail.nyp.edu.sg"


def test_registration_normalizes_uppercase_domain_and_hashes_password(client):
    """Uppercase input is accepted, stored lowercase, and never stores plaintext."""
    test_client, test_db = client

    response = test_client.post(
        "/register",
        data=registration_data("  STUDENT@MYMAIL.NYP.EDU.SG  "),
        follow_redirects=False,
    )

    assert response.status_code == 302
    user = get_users(test_db)[0]
    assert user["email"] == "student@mymail.nyp.edu.sg"
    assert user["password_hash"] != "Password123"
    assert check_password_hash(user["password_hash"], "Password123")


@pytest.mark.parametrize(
    "email",
    [
        "student@nyp.edu.sg",
        "student@mymail.nyp.edu.sg.attacker.com",
        "",
    ],
)
def test_registration_rejects_invalid_or_missing_email(client, email):
    """Invalid, fake-suffix, and missing email values do not create accounts."""
    test_client, test_db = client

    response = test_client.post(
        "/register",
        data=registration_data(email),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert get_users(test_db) == []
    if email:
        assert b"@mymail.nyp.edu.sg" in response.data
    else:
        assert b"Please fill in all required fields" in response.data


def test_legacy_invalid_domain_account_cannot_log_in(tmp_path, monkeypatch):
    """Correct credentials cannot activate a legacy account outside the domain."""
    test_db = tmp_path / "legacy_login.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)
    conn = sqlite3.connect(test_db)
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
            email, contact_number, password_hash, role, status
        )
        VALUES (?, 'Legacy', 'User', 'LegacyUser', ?, '91234567', ?, 'user', 'Active')
        """,
        (
            "S7000002",
            "john12@nyp.edu.sg",
            generate_password_hash("Password123"),
        ),
    )
    conn.commit()
    conn.close()

    flask_app = create_app()
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as test_client:
        response = test_client.post(
            "/login",
            data={"email": "john12@nyp.edu.sg", "password": "Password123"},
        )

        assert response.status_code == 200
        assert b"Invalid email or password" in response.data
        with test_client.session_transaction() as login_session:
            assert "user_id" not in login_session
