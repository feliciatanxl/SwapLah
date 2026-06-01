import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "test_login.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client, test_db


def create_test_user(test_db, email="s12345678@mymail.nyp.edu.sg", password="Password123", status="Active"):
    conn = sqlite3.connect(test_db)
    conn.execute(
        """
        INSERT INTO users (
            student_id, first_name, last_name, display_name,
            email, contact_number, password_hash, role, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "S12345678",
            "Test",
            "User",
            "TestUser",
            email,
            "91234567",
            generate_password_hash(password),
            "user",
            status,
        ),
    )
    conn.commit()
    conn.close()


def test_login_with_valid_credentials_creates_session(client):
    test_client, test_db = client
    create_test_user(test_db)

    response = test_client.post(
        "/login",
        data={
            "email": "s12345678@mymail.nyp.edu.sg",
            "password": "Password123",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/profile" in response.headers["Location"]

    with test_client.session_transaction() as session:
        assert session["email"] == "s12345678@mymail.nyp.edu.sg"
        assert session["display_name"] == "TestUser"
        assert session["role"] == "user"


def test_login_rejects_invalid_password(client):
    test_client, test_db = client
    create_test_user(test_db)

    response = test_client.post(
        "/login",
        data={
            "email": "s12345678@mymail.nyp.edu.sg",
            "password": "WrongPassword",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Invalid email or password" in response.data

    with test_client.session_transaction() as session:
        assert "user_id" not in session


def test_login_rejects_unknown_email(client):
    test_client, _ = client

    response = test_client.post(
        "/login",
        data={
            "email": "unknown@mymail.nyp.edu.sg",
            "password": "Password123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Invalid email or password" in response.data


def test_login_blocks_suspended_user(client):
    test_client, test_db = client
    create_test_user(test_db, status="Suspended")

    response = test_client.post(
        "/login",
        data={
            "email": "s12345678@mymail.nyp.edu.sg",
            "password": "Password123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"account has been suspended" in response.data

    with test_client.session_transaction() as session:
        assert "user_id" not in session


def test_logged_in_user_can_access_profile(client):
    test_client, test_db = client
    create_test_user(test_db)

    test_client.post(
        "/login",
        data={
            "email": "s12345678@mymail.nyp.edu.sg",
            "password": "Password123",
        },
    )

    response = test_client.get("/profile")

    assert response.status_code == 200


def test_logged_out_user_cannot_access_profile(client):
    test_client, _ = client

    response = test_client.get("/profile", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]