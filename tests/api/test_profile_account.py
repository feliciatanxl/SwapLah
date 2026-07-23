# pylint: disable=missing-module-docstring,missing-function-docstring,redefined-outer-name,duplicate-code
import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "test_profile_account.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client, test_db


def create_test_user(test_db):
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
            "S76543210",
            "Felicia",
            "Tan",
            "FeliciaT",
            "s76543210@mymail.nyp.edu.sg",
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


def test_profile_displays_logged_in_user_details(client):
    test_client, test_db = client
    user_id = create_test_user(test_db)

    with test_client.session_transaction() as session:
        session["user_id"] = user_id
        session["email"] = "s76543210@mymail.nyp.edu.sg"
        session["display_name"] = "FeliciaT"
        session["role"] = "user"

    response = test_client.get("/profile")

    assert response.status_code == 200
    assert b"S76543210" in response.data
    assert b"Felicia" in response.data
    assert b"Tan" in response.data
    assert b"FeliciaT" in response.data
    assert b"s76543210@mymail.nyp.edu.sg" in response.data
    assert b"91234567" in response.data


def test_profile_redirects_when_not_logged_in(client):
    test_client, _ = client

    response = test_client.get("/profile", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_redirects_when_session_user_missing(client):
    test_client, _ = client

    with test_client.session_transaction() as session:
        session["user_id"] = 999999

    response = test_client.get("/profile", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
