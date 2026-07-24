# pylint: disable=missing-module-docstring,missing-function-docstring,redefined-outer-name,duplicate-code
import sqlite3

import pytest
from werkzeug.security import check_password_hash, generate_password_hash

import app.db as db_module
from app.db import get_user_by_id, update_user_account


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    db_path = tmp_path / "profile_update_unit.db"
    monkeypatch.setattr(db_module, "DATABASE", db_path)
    db_module.init_db()
    return db_path


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
            "S22222222",
            "Old",
            "Name",
            "OldName",
            "s22222222@mymail.nyp.edu.sg",
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


def test_update_user_account_updates_editable_fields_only(test_db):
    user_id = create_test_user(test_db)

    update_user_account(
        user_id=user_id,
        first_name="New",
        last_name="User",
        display_name="NewUser",
        contact_number="98765432",
    )

    user = get_user_by_id(user_id)

    assert user["student_id"] == "S22222222"
    assert user["email"] == "s22222222@mymail.nyp.edu.sg"
    assert user["first_name"] == "New"
    assert user["last_name"] == "User"
    assert user["display_name"] == "NewUser"
    assert user["contact_number"] == "98765432"


def test_update_user_account_can_update_password_hash(test_db):
    user_id = create_test_user(test_db)
    new_hash = generate_password_hash("NewPassword123")

    update_user_account(
        user_id=user_id,
        first_name="New",
        last_name="User",
        display_name="NewUser",
        contact_number="98765432",
        password_hash=new_hash,
    )

    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    conn.close()

    assert check_password_hash(user["password_hash"], "NewPassword123")
    assert user["password_hash"] != "Password123"


def test_update_user_account_does_not_change_missing_user(  # pylint: disable=unused-argument
    test_db,
):
    update_user_account(
        user_id=999999,
        first_name="Ghost",
        last_name="User",
        display_name="GhostUser",
        contact_number="90000000",
    )

    user = get_user_by_id(999999)

    assert user is None
