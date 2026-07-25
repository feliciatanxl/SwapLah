# pylint: disable=missing-module-docstring,missing-function-docstring,redefined-outer-name,duplicate-code
import sqlite3

import pytest
from werkzeug.security import check_password_hash

import app.db as db_module
from app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a Flask test client with a temporary unit-test database."""
    test_db = tmp_path / "unit_swaplah.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client, test_db


def test_register_page_renders(client):
    test_client, _ = client

    response = test_client.get("/register")

    assert response.status_code == 200
    assert b"Create your account" in response.data
    assert b"Student ID" in response.data
    assert b"NYP Email Address" in response.data


def test_database_creates_users_table(client):
    _, test_db = client

    conn = sqlite3.connect(test_db)
    table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
    ).fetchone()
    conn.close()

    assert table is not None


def test_register_rejects_invalid_email_domain(client):
    test_client, _ = client

    response = test_client.post(
        "/register",
        data={
            "student_id": "S90000001",
            "first_name": "Test",
            "last_name": "User",
            "display_name": "TestUser",
            "email": "test@gmail.com",
            "contact_number": "91234567",
            "password": "Password123",
            "confirm_password": "Password123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"@mymail.nyp.edu.sg" in response.data


def test_register_creates_user_with_hashed_password(client):
    test_client, test_db = client

    response = test_client.post(
        "/register",
        data={
            "student_id": "S90000002",
            "first_name": "Hash",
            "last_name": "User",
            "display_name": "HashUser",
            "email": "s90000002@mymail.nyp.edu.sg",
            "contact_number": "91234568",
            "password": "Password123",
            "confirm_password": "Password123",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302

    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?",
        ("s90000002@mymail.nyp.edu.sg",),
    ).fetchone()
    conn.close()

    assert user is not None
    assert user["password_hash"] != "Password123"
    assert check_password_hash(user["password_hash"], "Password123")
