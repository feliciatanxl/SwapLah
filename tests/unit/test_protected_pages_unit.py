"""Unit tests for protected page access helper."""

from flask import Flask, session

from app import _redirect_logged_out_user


def create_minimal_test_app():
    """Create a minimal Flask app with a login route."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret-key"

    @app.route("/login")
    def login():
        return "Login page"

    return app


def test_redirect_logged_out_user_redirects_to_login():
    """Helper should redirect when user is not logged in."""
    app = create_minimal_test_app()

    with app.test_request_context("/sell"):
        response = _redirect_logged_out_user("Please log in.")

        assert response.status_code == 302
        assert "/login" in response.location


def test_redirect_logged_out_user_allows_logged_in_user():
    """Helper should return None when user is logged in."""
    app = create_minimal_test_app()

    with app.test_request_context("/sell"):
        session["user_id"] = 1

        response = _redirect_logged_out_user("Please log in.")

        assert response is None