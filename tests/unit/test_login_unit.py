"""Unit tests for the login form handler."""

from werkzeug.security import generate_password_hash

import app as app_module


TEST_EMAIL = "loginuser@mymail.nyp.edu.sg"
TEST_PASSWORD = "Password123"


def _build_user(status="Active"):
    """Return a test user accepted by the login handler."""
    return {
        "id": 101,
        "email": TEST_EMAIL,
        "display_name": "Login User",
        "role": "user",
        "status": status,
        "password_hash": generate_password_hash(TEST_PASSWORD),
    }


def _create_test_client(monkeypatch):
    """Create a Flask test client without using the real database."""
    monkeypatch.setattr(app_module, "init_db", lambda: None)

    flask_app = app_module.create_app()
    flask_app.config["TESTING"] = True

    return flask_app.test_client()


def test_login_rejects_missing_email_and_password(monkeypatch):
    """Blank login fields should display a validation error."""
    client = _create_test_client(monkeypatch)

    response = client.post(
        "/login",
        data={
            "email": "",
            "password": "",
        },
    )

    assert response.status_code == 200
    assert b"Please enter your email and password." in response.data


def test_login_rejects_unknown_email(monkeypatch):
    """An email that is not registered should be rejected."""
    monkeypatch.setattr(
        app_module,
        "get_user_by_email",
        lambda _email: None,
    )
    client = _create_test_client(monkeypatch)

    response = client.post(
        "/login",
        data={
            "email": "unknown@mymail.nyp.edu.sg",
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200
    assert b"Invalid email or password." in response.data

    with client.session_transaction() as login_session:
        assert "user_id" not in login_session


def test_login_rejects_incorrect_password(monkeypatch):
    """A registered user with an incorrect password should be rejected."""
    user = _build_user()
    monkeypatch.setattr(
        app_module,
        "get_user_by_email",
        lambda _email: user,
    )
    client = _create_test_client(monkeypatch)

    response = client.post(
        "/login",
        data={
            "email": TEST_EMAIL,
            "password": "WrongPassword",
        },
    )

    assert response.status_code == 200
    assert b"Invalid email or password." in response.data

    with client.session_transaction() as login_session:
        assert "user_id" not in login_session


def test_login_rejects_suspended_user(monkeypatch):
    """A suspended account should not be allowed to log in."""
    suspended_user = _build_user(status="Suspended")
    monkeypatch.setattr(
        app_module,
        "get_user_by_email",
        lambda _email: suspended_user,
    )
    client = _create_test_client(monkeypatch)

    response = client.post(
        "/login",
        data={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200
    assert b"Your account has been suspended." in response.data

    with client.session_transaction() as login_session:
        assert "user_id" not in login_session


def test_login_creates_session_for_valid_user(monkeypatch):
    """Valid credentials should create a session and redirect to profile."""
    user = _build_user()
    received_emails = []

    def find_user(email):
        """Record the cleaned email received by the mocked database call."""
        received_emails.append(email)
        return user

    monkeypatch.setattr(
        app_module,
        "get_user_by_email",
        find_user,
    )
    client = _create_test_client(monkeypatch)

    response = client.post(
        "/login",
        data={
            "email": f"  {TEST_EMAIL.upper()}  ",
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")
    assert received_emails == [TEST_EMAIL]

    with client.session_transaction() as login_session:
        assert login_session["user_id"] == user["id"]
        assert login_session["email"] == user["email"]
        assert login_session["display_name"] == user["display_name"]
        assert login_session["role"] == user["role"]
        assert isinstance(login_session["last_activity"], float)