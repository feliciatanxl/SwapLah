import sqlite3

import pytest
from werkzeug.security import check_password_hash, generate_password_hash

import app.db as db_module
from app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "test_profile_update.db"
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
            "S12345678",
            "Original",
            "User",
            "OriginalUser",
            "s12345678@mymail.nyp.edu.sg",
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


def login_session(test_client, user_id):
    with test_client.session_transaction() as session:
        session["user_id"] = user_id
        session["email"] = "s12345678@mymail.nyp.edu.sg"
        session["display_name"] = "OriginalUser"
        session["role"] = "user"


def get_user(test_db):
    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    user = conn.execute(
        "SELECT * FROM users WHERE student_id = ?",
        ("S12345678",),
    ).fetchone()
    conn.close()
    return user


def test_edit_profile_page_loads_for_logged_in_user(client):
    test_client, test_db = client
    user_id = create_test_user(test_db)
    login_session(test_client, user_id)

    response = test_client.get("/profile/edit")

    assert response.status_code == 200
    assert b"Edit Profile" in response.data
    assert b"Original" in response.data
    assert b"OriginalUser" in response.data
    assert b"s12345678@mymail.nyp.edu.sg" in response.data
    assert b"S12345678" in response.data


def test_logged_in_user_can_update_editable_profile_details(client):
    test_client, test_db = client
    user_id = create_test_user(test_db)
    login_session(test_client, user_id)

    response = test_client.post(
        "/profile/edit",
        data={
            "first_name": "Updated",
            "last_name": "Name",
            "display_name": "UpdatedName",
            "contact_number": "98765432",
            "password": "",
            "confirm_password": "",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/profile" in response.headers["Location"]

    user = get_user(test_db)
    assert user["first_name"] == "Updated"
    assert user["last_name"] == "Name"
    assert user["display_name"] == "UpdatedName"
    assert user["contact_number"] == "98765432"


def test_email_and_student_id_cannot_be_changed(client):
    test_client, test_db = client
    user_id = create_test_user(test_db)
    login_session(test_client, user_id)

    response = test_client.post(
        "/profile/edit",
        data={
            "first_name": "Updated",
            "last_name": "Name",
            "display_name": "UpdatedName",
            "contact_number": "98765432",
            "email": "changed@mymail.nyp.edu.sg",
            "student_id": "S99999999",
            "password": "",
            "confirm_password": "",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302

    user = get_user(test_db)
    assert user["email"] == "s12345678@mymail.nyp.edu.sg"
    assert user["student_id"] == "S12345678"


def test_update_profile_rejects_missing_required_fields(client):
    test_client, test_db = client
    user_id = create_test_user(test_db)
    login_session(test_client, user_id)

    response = test_client.post(
        "/profile/edit",
        data={
            "first_name": "",
            "last_name": "Name",
            "display_name": "UpdatedName",
            "contact_number": "98765432",
            "password": "",
            "confirm_password": "",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Please fill in all required profile fields" in response.data

    user = get_user(test_db)
    assert user["first_name"] == "Original"


def test_update_profile_rejects_invalid_contact_number(client):
    test_client, test_db = client
    user_id = create_test_user(test_db)
    login_session(test_client, user_id)

    response = test_client.post(
        "/profile/edit",
        data={
            "first_name": "Updated",
            "last_name": "Name",
            "display_name": "UpdatedName",
            "contact_number": "abc123",
            "password": "",
            "confirm_password": "",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Please enter a valid contact number" in response.data

    user = get_user(test_db)
    assert user["contact_number"] == "91234567"


def test_update_profile_rejects_password_mismatch(client):
    test_client, test_db = client
    user_id = create_test_user(test_db)
    login_session(test_client, user_id)

    response = test_client.post(
        "/profile/edit",
        data={
            "first_name": "Updated",
            "last_name": "Name",
            "display_name": "UpdatedName",
            "contact_number": "98765432",
            "password": "NewPassword123",
            "confirm_password": "DifferentPassword123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Passwords do not match" in response.data


def test_update_profile_can_change_password(client):
    test_client, test_db = client
    user_id = create_test_user(test_db)
    login_session(test_client, user_id)

    response = test_client.post(
        "/profile/edit",
        data={
            "first_name": "Updated",
            "last_name": "Name",
            "display_name": "UpdatedName",
            "contact_number": "98765432",
            "password": "NewPassword123",
            "confirm_password": "NewPassword123",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302

    user = get_user(test_db)
    assert check_password_hash(user["password_hash"], "NewPassword123")


def test_logged_out_user_cannot_access_edit_profile(client):
    test_client, _ = client

    response = test_client.get("/profile/edit", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_invalid_session_redirects_to_login(client):
    test_client, _ = client

    with test_client.session_transaction() as session:
        session["user_id"] = 999999

    response = test_client.get("/profile/edit", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]