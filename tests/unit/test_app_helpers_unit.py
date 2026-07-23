"""Unit tests for Flask app helper functions."""

import pytest
from flask import Flask, session
from werkzeug.security import generate_password_hash

import app as app_module


@pytest.fixture
def helper_app():
    """Create a minimal Flask app for helper tests."""
    flask_app = Flask(__name__)
    flask_app.config["SECRET_KEY"] = "test-secret-key"

    @flask_app.route("/login")
    def login():
        return "Login"

    @flask_app.route("/profile")
    def profile():
        return "Profile"

    return flask_app


def test_load_secret_key_requires_environment_value(monkeypatch):
    """Secret key helper should fail fast when SECRET_KEY is missing."""
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError):
        app_module._load_secret_key()


def test_load_secret_key_returns_environment_value(monkeypatch):
    """Secret key helper should return the configured value."""
    monkeypatch.setenv("SECRET_KEY", "unit-secret")

    assert app_module._load_secret_key() == "unit-secret"


def test_admin_helpers_identify_only_active_admins():
    """Admin helper should require an active admin user."""
    assert app_module._is_admin_user(None) is False
    assert app_module._is_admin_user({"role": "user", "status": "Active"}) is False
    assert app_module._is_admin_user({"role": "admin", "status": "Suspended"}) is False
    assert app_module._is_admin_user({"role": "admin", "status": "Active"}) is True
    assert app_module._admin_denied_response() == ("Forbidden", 403)


def test_require_admin_redirects_logged_out_user(helper_app):
    """Logged-out admin requests should redirect to login."""
    with helper_app.test_request_context("/admin/settings"):
        response = app_module._require_admin_response()

        assert response.status_code == 302
        assert "/login" in response.location


def test_require_admin_blocks_non_admin_user(helper_app, monkeypatch):
    """Logged-in non-admin users should receive a forbidden response."""
    monkeypatch.setattr(
        app_module,
        "get_user_by_id",
        lambda user_id: {"id": user_id, "role": "user", "status": "Active"},
    )

    with helper_app.test_request_context("/admin/settings"):
        session["user_id"] = 7

        assert app_module._require_admin_response() == ("Forbidden", 403)


def test_admin_required_allows_active_admin(helper_app, monkeypatch):
    """Admin decorator should call the wrapped view for active admins."""
    monkeypatch.setattr(
        app_module,
        "get_user_by_id",
        lambda user_id: {"id": user_id, "role": "admin", "status": "Active"},
    )

    def protected_view():
        return "allowed"

    with helper_app.test_request_context("/admin"):
        session["user_id"] = 1

        assert app_module.admin_required(protected_view)() == "allowed"


def test_handle_login_requires_credentials(helper_app, monkeypatch):
    """Login helper should reject missing credentials."""
    monkeypatch.setattr(app_module, "render_template", lambda template: template)

    with helper_app.test_request_context("/login", method="POST", data={}):
        assert app_module._handle_login() == "login.html"


def test_handle_login_rejects_unknown_user(helper_app, monkeypatch):
    """Login helper should reject users that cannot be found."""
    monkeypatch.setattr(app_module, "render_template", lambda template: template)
    monkeypatch.setattr(app_module, "get_user_by_email", lambda email: None)

    with helper_app.test_request_context(
        "/login",
        method="POST",
        data={"email": "missing@mymail.nyp.edu.sg", "password": "Password123"},
    ):
        assert app_module._handle_login() == "login.html"


def test_handle_login_rejects_suspended_user(helper_app, monkeypatch):
    """Login helper should reject suspended accounts."""
    user = {
        "id": 3,
        "email": "suspended@mymail.nyp.edu.sg",
        "display_name": "Suspended",
        "role": "user",
        "status": "Suspended",
        "password_hash": generate_password_hash("Password123"),
    }

    monkeypatch.setattr(app_module, "render_template", lambda template: template)
    monkeypatch.setattr(app_module, "get_user_by_email", lambda email: user)

    with helper_app.test_request_context(
        "/login",
        method="POST",
        data={"email": user["email"], "password": "Password123"},
    ):
        assert app_module._handle_login() == "login.html"


def test_handle_login_sets_session_for_valid_user(helper_app, monkeypatch):
    """Login helper should create a session for active users."""
    user = {
        "id": 4,
        "email": "active@mymail.nyp.edu.sg",
        "display_name": "Active",
        "role": "user",
        "status": "Active",
        "password_hash": generate_password_hash("Password123"),
    }

    monkeypatch.setattr(app_module, "get_user_by_email", lambda email: user)

    with helper_app.test_request_context(
        "/login",
        method="POST",
        data={"email": user["email"], "password": "Password123"},
    ):
        response = app_module._handle_login()

        assert response.status_code == 302
        assert "/profile" in response.location
        assert session["user_id"] == user["id"]
        assert session["email"] == user["email"]
