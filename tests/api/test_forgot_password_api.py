"""API tests for the internal (email-free) account-verification password reset."""

# pylint: disable=redefined-outer-name

import sqlite3
import time

import pytest
from werkzeug.security import check_password_hash, generate_password_hash

import app.db as db_module
from app import create_app

GENERIC_FAILURE = b"Unable to verify the account details."
EMAIL = "s8000001@mymail.nyp.edu.sg"
STUDENT_ID = "S8000001"
CONTACT = "91234567"


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a Flask test client backed by an isolated temporary database."""
    test_db = tmp_path / "test_forgot_password.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client, test_db


def create_user(test_db, status="Active", role="user", password="OldPassword1"):
    """Insert the known verification user and return its ID."""
    conn = sqlite3.connect(test_db)
    cursor = conn.execute(
        """
        INSERT INTO users (student_id, first_name, last_name, display_name, email,
                           contact_number, password_hash, role, status)
        VALUES (?, 'Reset', 'User', 'ResetUser', ?, ?, ?, ?, ?)
        """,
        (STUDENT_ID, EMAIL, CONTACT, generate_password_hash(password), role, status),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def verify(test_client, email=EMAIL, student_id=STUDENT_ID, contact=CONTACT):
    """Submit the forgot-password verification form."""
    return test_client.post(
        "/forgot-password",
        data={"email": email, "student_id": student_id, "contact_number": contact},
        follow_redirects=False,
    )


def password_hash_of(test_db, user_id):
    """Return the stored password hash for a user."""
    conn = sqlite3.connect(test_db)
    row = conn.execute("SELECT password_hash FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return row[0]


# --- forgot-password verification ---------------------------------------

def test_forgot_password_get_renders_three_fields(client):
    """The verification form requests email, Student ID and contact number."""
    test_client, _test_db = client
    page = test_client.get("/forgot-password").get_data(as_text=True)
    assert 'name="email"' in page
    assert 'name="student_id"' in page
    assert 'name="contact_number"' in page


def test_matching_details_grant_reset_session(client):
    """A correct triple redirects to /reset-password and stores only the user id."""
    test_client, test_db = client
    user_id = create_user(test_db)

    response = verify(test_client)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/reset-password")
    assert "token" not in response.headers["Location"]
    with test_client.session_transaction() as sess:
        assert sess["password_reset_user_id"] == user_id
        assert "password_reset_expires_at" in sess


@pytest.mark.parametrize(
    "email,student_id,contact",
    [
        (EMAIL, "S0000000", CONTACT),          # wrong student id
        (EMAIL, STUDENT_ID, "80000000"),       # wrong contact
        ("s8009999@mymail.nyp.edu.sg", STUDENT_ID, CONTACT),  # unknown email
        ("attacker@gmail.com", STUDENT_ID, CONTACT),          # invalid domain
        ("", STUDENT_ID, CONTACT),             # missing email
        (EMAIL, "", CONTACT),                  # missing student id
        (EMAIL, STUDENT_ID, ""),               # missing contact
    ],
)
def test_verification_failures_return_generic_message(client, email, student_id, contact):
    """Every failure mode yields the same generic message and no reset session."""
    test_client, test_db = client
    create_user(test_db)

    response = verify(test_client, email, student_id, contact)

    assert response.status_code == 200
    assert GENERIC_FAILURE in response.data
    with test_client.session_transaction() as sess:
        assert "password_reset_user_id" not in sess


def test_failed_attempt_counter_increments(client):
    """Each failed verification increments the session attempt counter."""
    test_client, test_db = client
    create_user(test_db)

    verify(test_client, email=EMAIL, student_id="S0000000")
    with test_client.session_transaction() as sess:
        assert sess["password_reset_attempts"] == 1

    verify(test_client, email=EMAIL, student_id="S0000000")
    with test_client.session_transaction() as sess:
        assert sess["password_reset_attempts"] == 2


def test_attempt_limit_blocks_further_verification(client):
    """After five failures, even a correct triple is blocked with a generic message."""
    test_client, test_db = client
    create_user(test_db)

    for _ in range(5):
        verify(test_client, email=EMAIL, student_id="S0000000")

    response = verify(test_client)  # correct details, but limit reached
    assert response.status_code == 200
    assert b"Too many verification attempts" in response.data
    with test_client.session_transaction() as sess:
        assert "password_reset_user_id" not in sess


# --- reset-password gating ----------------------------------------------

def test_reset_page_blocked_without_verified_session(client):
    """The reset page redirects to forgot-password without a reset session."""
    test_client, _test_db = client
    response = test_client.get("/reset-password", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/forgot-password")


def test_reset_page_blocked_after_expiry(client):
    """An expired reset session cannot access the reset page."""
    test_client, test_db = client
    create_user(test_db)
    verify(test_client)

    with test_client.session_transaction() as sess:
        sess["password_reset_expires_at"] = time.time() - 1

    response = test_client.get("/reset-password", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/forgot-password")


def test_verified_session_allows_reset_page(client):
    """A valid reset session renders the new-password form with no token."""
    test_client, test_db = client
    create_user(test_db)
    verify(test_client)

    response = test_client.get("/reset-password")
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'name="password"' in page
    assert 'name="confirm_password"' in page
    assert "token" not in page


def test_password_mismatch_is_rejected(client):
    """Mismatched passwords are rejected and the password is unchanged."""
    test_client, test_db = client
    user_id = create_user(test_db)
    verify(test_client)

    response = test_client.post(
        "/reset-password",
        data={"password": "BrandNewPass1", "confirm_password": "Different222"},
        follow_redirects=True,
    )
    assert b"Passwords do not match" in response.data
    assert check_password_hash(password_hash_of(test_db, user_id), "OldPassword1")


def test_successful_reset_updates_login_and_clears_session(client):
    """A valid reset hashes the new password, updates login, and clears the session."""
    test_client, test_db = client
    user_id = create_user(test_db)
    verify(test_client)

    response = test_client.post(
        "/reset-password",
        data={"password": "BrandNewPass1", "confirm_password": "BrandNewPass1"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")

    stored = password_hash_of(test_db, user_id)
    assert stored != "BrandNewPass1"
    assert check_password_hash(stored, "BrandNewPass1")
    assert not check_password_hash(stored, "OldPassword1")

    with test_client.session_transaction() as sess:
        assert "password_reset_user_id" not in sess
        assert "password_reset_expires_at" not in sess
        # Reset does not automatically log the user in.
        assert "user_id" not in sess

    old_login = test_client.post(
        "/login", data={"email": EMAIL, "password": "OldPassword1"}, follow_redirects=True
    )
    assert b"Invalid email or password" in old_login.data

    new_login = test_client.post(
        "/login", data={"email": EMAIL, "password": "BrandNewPass1"}, follow_redirects=False
    )
    assert new_login.status_code == 302
    assert "/profile" in new_login.headers["Location"]


def test_reset_cannot_be_reused_after_success(client):
    """A completed reset cannot be replayed; the reset page is re-gated."""
    test_client, test_db = client
    create_user(test_db)
    verify(test_client)
    test_client.post(
        "/reset-password",
        data={"password": "BrandNewPass1", "confirm_password": "BrandNewPass1"},
    )

    replay = test_client.post(
        "/reset-password",
        data={"password": "SecondPass22", "confirm_password": "SecondPass22"},
        follow_redirects=False,
    )
    assert replay.status_code == 302
    assert replay.headers["Location"].endswith("/forgot-password")


def test_suspended_user_resets_but_stays_suspended(client):
    """A suspended account may reset its password but remains blocked at login."""
    test_client, test_db = client
    user_id = create_user(test_db, status="Suspended")
    verify(test_client)
    test_client.post(
        "/reset-password",
        data={"password": "BrandNewPass1", "confirm_password": "BrandNewPass1"},
    )

    assert check_password_hash(password_hash_of(test_db, user_id), "BrandNewPass1")

    login = test_client.post(
        "/login", data={"email": EMAIL, "password": "BrandNewPass1"}, follow_redirects=True
    )
    assert b"suspended" in login.data.lower()

    conn = sqlite3.connect(test_db)
    row = conn.execute("SELECT status, role FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    assert row[0] == "Suspended"


def test_role_is_unchanged_after_reset(client):
    """Resetting the password never alters the account role."""
    test_client, test_db = client
    user_id = create_user(test_db, role="admin")
    verify(test_client)
    test_client.post(
        "/reset-password",
        data={"password": "BrandNewPass1", "confirm_password": "BrandNewPass1"},
    )

    conn = sqlite3.connect(test_db)
    role = conn.execute("SELECT role FROM users WHERE id=?", (user_id,)).fetchone()[0]
    conn.close()
    assert role == "admin"
