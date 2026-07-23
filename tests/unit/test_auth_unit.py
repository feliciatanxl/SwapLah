import pytest
from flask import Flask, session, url_for
from app.auth import admin_required, _is_admin_user, _require_admin_response
from app import create_app


@pytest.fixture
def app():
    """Create a Flask app for testing auth."""
    flask_app = create_app()
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test-secret'
    return flask_app


def test_is_admin_user_valid():
    """Test _is_admin_user returns True for active admin."""
    user = {"role": "admin", "status": "Active"}
    assert _is_admin_user(user) is True


def test_is_admin_user_none():
    """Test _is_admin_user returns False for None."""
    assert _is_admin_user(None) is False


def test_is_admin_user_wrong_role():
    """Test _is_admin_user returns False for non-admin role."""
    user = {"role": "user", "status": "Active"}
    assert _is_admin_user(user) is False


def test_is_admin_user_inactive():
    """Test _is_admin_user returns False for inactive admin."""
    user = {"role": "admin", "status": "Inactive"}
    assert _is_admin_user(user) is False


def test_require_admin_response_no_session(app):
    """Test _require_admin_response redirects when no user_id in session."""
    with app.test_request_context():
        # No session set
        response = _require_admin_response()
        # Should be a redirect response
        assert response is not None
        # Check that it's a redirect tuple or response
        if isinstance(response, tuple):
            assert response[1] == 302 or "redirect" in str(response[0])
        else:
            # It might be a redirect response object
            assert response.status_code == 302 or "redirect" in str(response)


def test_require_admin_response_invalid_user(app, monkeypatch):
    """Test _require_admin_response returns Forbidden for non-admin user."""
    with app.test_request_context():
        session['user_id'] = 1
        
        # Mock get_user_by_id to return non-admin user
        def mock_get_user_by_id(user_id):
            return {"id": 1, "role": "user", "status": "Active"}
        
        monkeypatch.setattr('app.auth.get_user_by_id', mock_get_user_by_id)
        
        response = _require_admin_response()
        # Should be Forbidden
        if isinstance(response, tuple):
            assert response[0] == "Forbidden"
            assert response[1] == 403
        else:
            # It might be a response object
            assert response.status_code == 403


def test_require_admin_response_valid_admin(app, monkeypatch):
    """Test _require_admin_response returns None for valid admin."""
    with app.test_request_context():
        session['user_id'] = 1
        
        # Mock get_user_by_id to return admin user
        def mock_get_user_by_id(user_id):
            return {"id": 1, "role": "admin", "status": "Active"}
        
        monkeypatch.setattr('app.auth.get_user_by_id', mock_get_user_by_id)
        
        response = _require_admin_response()
        assert response is None


def test_admin_required_decorator_valid(app, monkeypatch):
    """Test admin_required decorator allows valid admin."""
    with app.test_request_context():
        session['user_id'] = 1
        
        # Mock get_user_by_id to return admin user
        def mock_get_user_by_id(user_id):
            return {"id": 1, "role": "admin", "status": "Active"}
        
        monkeypatch.setattr('app.auth.get_user_by_id', mock_get_user_by_id)
        
        @admin_required
        def test_view():
            return "Success", 200
        
        response = test_view()
        assert response == ("Success", 200)


def test_admin_required_decorator_no_session(app):
    """Test admin_required decorator redirects when no session."""
    with app.test_request_context():
        # No session set
        @admin_required
        def test_view():
            return "Success", 200
        
        response = test_view()
        # Should be a redirect
        if isinstance(response, tuple):
            assert response[1] == 302 or "redirect" in str(response[0])
        else:
            assert response.status_code == 302 or "redirect" in str(response)


def test_admin_required_decorator_invalid_user(app, monkeypatch):
    """Test admin_required decorator returns Forbidden for non-admin."""
    with app.test_request_context():
        session['user_id'] = 1
        
        # Mock get_user_by_id to return non-admin user
        def mock_get_user_by_id(user_id):
            return {"id": 1, "role": "user", "status": "Active"}
        
        monkeypatch.setattr('app.auth.get_user_by_id', mock_get_user_by_id)
        
        @admin_required
        def test_view():
            return "Success", 200
        
        response = test_view()
        # Should be Forbidden
        if isinstance(response, tuple):
            assert response[0] == "Forbidden"
            assert response[1] == 403
        else:
            assert response.status_code == 403