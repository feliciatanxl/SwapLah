# pylint: disable=missing-module-docstring,missing-function-docstring,redefined-outer-name,duplicate-code
import sqlite3
import sys
from pathlib import Path

import pytest

import app.db as db_module
from app import create_app

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def client(tmp_path):
    """Create a Flask test client using a temporary SQLite database."""
    test_db = tmp_path / "test_swaplah.db"
    db_module.DATABASE = test_db

    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client


def get_user_by_email(email):
    """Retrieve one user from the test database by email."""
    conn = sqlite3.connect(db_module.DATABASE)
    conn.row_factory = sqlite3.Row
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,),
    ).fetchone()
    conn.close()
    return user


def test_register_valid_nyp_email_creates_account(client):
    response = client.post(
        "/register",
        data={
            "student_id": "S10234567",
            "first_name": "Felicia",
            "last_name": "Tan",
            "display_name": "Felicia",
            "email": "s10234567@mymail.nyp.edu.sg",
            "contact_number": "91234567",
            "password": "Password123",
            "confirm_password": "Password123",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    user = get_user_by_email("s10234567@mymail.nyp.edu.sg")
    assert user is not None
    assert user["student_id"] == "S10234567"
    assert user["display_name"] == "Felicia"
    assert user["status"] == "Active"
    assert user["role"] == "user"


def test_register_rejects_non_nyp_email(client):
    response = client.post(
        "/register",
        data={
            "student_id": "S10234568",
            "first_name": "John",
            "last_name": "Lim",
            "display_name": "John",
            "email": "john@gmail.com",
            "contact_number": "91234568",
            "password": "Password123",
            "confirm_password": "Password123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"@mymail.nyp.edu.sg" in response.data

    user = get_user_by_email("john@gmail.com")
    assert user is None


def test_register_rejects_empty_required_fields(client):
    response = client.post(
        "/register",
        data={
            "student_id": "",
            "first_name": "Felicia",
            "last_name": "Tan",
            "display_name": "Felicia",
            "email": "s10234569@mymail.nyp.edu.sg",
            "contact_number": "91234569",
            "password": "Password123",
            "confirm_password": "Password123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Please fill in all required fields" in response.data

    user = get_user_by_email("s10234569@mymail.nyp.edu.sg")
    assert user is None


def test_register_rejects_duplicate_email(client):
    form_data = {
        "student_id": "S10234570",
        "first_name": "Kai",
        "last_name": "Lim",
        "display_name": "Kai",
        "email": "s10234570@mymail.nyp.edu.sg",
        "contact_number": "91234570",
        "password": "Password123",
        "confirm_password": "Password123",
    }

    first_response = client.post("/register", data=form_data)
    assert first_response.status_code == 302

    duplicate_data = form_data.copy()
    duplicate_data["student_id"] = "S10234571"

    second_response = client.post(
        "/register",
        data=duplicate_data,
        follow_redirects=True,
    )

    assert second_response.status_code == 200
    assert b"Email or Student ID already exists" in second_response.data


def test_register_rejects_duplicate_student_id(client):
    first_data = {
        "student_id": "S10234572",
        "first_name": "A",
        "last_name": "Tan",
        "display_name": "StudentA",
        "email": "s10234572@mymail.nyp.edu.sg",
        "contact_number": "91234572",
        "password": "Password123",
        "confirm_password": "Password123",
    }

    second_data = {
        "student_id": "S10234572",
        "first_name": "B",
        "last_name": "Lim",
        "display_name": "StudentB",
        "email": "s10234573@mymail.nyp.edu.sg",
        "contact_number": "91234573",
        "password": "Password123",
        "confirm_password": "Password123",
    }

    first_response = client.post("/register", data=first_data)
    assert first_response.status_code == 302

    second_response = client.post(
        "/register",
        data=second_data,
        follow_redirects=True,
    )

    assert second_response.status_code == 200
    assert b"Email or Student ID already exists" in second_response.data


def test_register_password_is_hashed_not_plaintext(client):
    plain_password = "Password123"

    response = client.post(
        "/register",
        data={
            "student_id": "S10234574",
            "first_name": "Hash",
            "last_name": "Test",
            "display_name": "HashTest",
            "email": "s10234574@mymail.nyp.edu.sg",
            "contact_number": "91234574",
            "password": plain_password,
            "confirm_password": plain_password,
        },
    )

    assert response.status_code == 302

    user = get_user_by_email("s10234574@mymail.nyp.edu.sg")
    assert user is not None
    assert user["password_hash"] != plain_password
    assert "scrypt:" in user["password_hash"] or "pbkdf2:" in user["password_hash"]
