import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app.db import get_user_by_id


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    db_path = tmp_path / "profile_db_unit.db"
    monkeypatch.setattr(db_module, "DATABASE", db_path)
    db_module.init_db()
    return db_path


def test_get_user_by_id_returns_account_details(test_db):
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
            "S88888888",
            "Account",
            "Viewer",
            "AccountViewer",
            "s88888888@mymail.nyp.edu.sg",
            "98887777",
            generate_password_hash("Password123"),
            "user",
            "Active",
        ),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    user = get_user_by_id(user_id)

    assert user is not None
    assert user["student_id"] == "S88888888"
    assert user["first_name"] == "Account"
    assert user["last_name"] == "Viewer"
    assert user["display_name"] == "AccountViewer"
    assert user["email"] == "s88888888@mymail.nyp.edu.sg"
    assert user["contact_number"] == "98887777"


def test_get_user_by_id_returns_none_for_missing_user(test_db):
    user = get_user_by_id(999999)

    assert user is None