import pytest
from app import create_app
import app.db as db_module


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Create the Flask app against an isolated on-disk test database."""
    test_db = tmp_path / "test_admin_routes_unit.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = "admin-routes-test-secret"

    with flask_app.app_context():
        yield flask_app


def login_as_admin(client):
    """Helper to log in as admin."""
    with client.session_transaction() as sess:
        sess['user_id'] = 1


def create_admin_user(app):
    """Helper to create an admin user in the test database."""
    from app.db import get_db_connection
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO users (id, student_id, first_name, last_name, display_name, email, contact_number, password_hash, role) '
        'VALUES (1, "S10001", "Admin", "User", "AdminUser", "admin@test.com", "12345678", "hash", "admin")'
    )
    conn.commit()
    conn.close()


def create_test_user(app):
    """Helper to create a regular user in the test database."""
    from app.db import get_db_connection
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO users (id, student_id, first_name, last_name, display_name, email, contact_number, password_hash, role) '
        'VALUES (2, "S10002", "Regular", "User", "RegularUser", "user@test.com", "87654321", "hash", "user")'
    )
    conn.commit()
    conn.close()


def create_test_listing(app, seller_id=2):
    """Helper to create a test listing."""
    from app.db import create_listing
    return create_listing(
        seller_id=seller_id,
        title='Test Listing',
        description='Test Description',
        price=100,
        category='Electronics',
        condition='Good',
        image_url='http://example.com/img.jpg'
    )


def create_test_report(app, listing_id=1, reporter_id=2):
    """Helper to create a test report."""
    from app.db import create_report
    return create_report(
        listing_id=listing_id,
        reporter_id=reporter_id,
        reason='Spam',
        description='This is spam'
    )


def test_admin_dashboard_success(app):
    """Test admin dashboard renders successfully (covers line 19-20)."""
    create_admin_user(app)

    with app.test_client() as client:
        login_as_admin(client)
        response = client.get('/admin')
        assert response.status_code == 200
        # Check that it renders HTML (not JSON)
        assert 'text/html' in response.content_type


def test_admin_dashboard_unauthenticated(app):
    """Test admin dashboard redirects when not logged in."""
    with app.test_client() as client:
        response = client.get('/admin')
        # Should redirect to login
        assert response.status_code == 302


def test_admin_dashboard_non_admin(app):
    """Test admin dashboard returns 403 for non-admin user."""
    create_test_user(app)

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 2
        response = client.get('/admin')
        # Should be forbidden
        assert response.status_code == 403


def test_api_admin_reports_success(app):
    """Test API returns reports as JSON (covers line 27-28)."""
    create_admin_user(app)

    with app.test_client() as client:
        login_as_admin(client)
        response = client.get('/admin/reports')
        assert response.status_code == 200
        data = response.get_json()
        assert 'reports' in data
        assert isinstance(data['reports'], list)


def test_delete_reported_listing_success(app):
    """Test successful deletion of reported listing (covers lines 35-47)."""
    create_admin_user(app)
    create_test_user(app)

    with app.test_client() as client:
        login_as_admin(client)

        # Create listing and report
        with app.app_context():
            listing = create_test_listing(app, seller_id=2)
            report = create_test_report(app, listing_id=1, reporter_id=2)

        response = client.post('/admin/reports/1/delete-listing')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['message'] == 'Listing soft-deleted successfully'
        assert 'report' in data


def test_delete_reported_listing_not_found(app):
    """Test 404 when report not found (covers line 37-39)."""
    create_admin_user(app)

    with app.test_client() as client:
        login_as_admin(client)
        response = client.post('/admin/reports/999/delete-listing')
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'Report or listing not found or already processed'


def test_delete_reported_listing_database_error(app, monkeypatch):
    """Test 500 when database error occurs (covers line 40-41)."""
    create_admin_user(app)

    # Mock admin_delete_reported_listing to return database error
    def mock_admin_delete_reported_listing(report_id):
        return False, "database_error"

    monkeypatch.setattr('app.routes.admin.admin_delete_reported_listing',
                        mock_admin_delete_reported_listing)

    with app.test_client() as client:
        login_as_admin(client)
        response = client.post('/admin/reports/1/delete-listing')
        assert response.status_code == 500
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'Database error'


def test_dismiss_report_success(app):
    """Test successful report dismissal (covers lines 58-69)."""
    create_admin_user(app)
    create_test_user(app)

    with app.test_client() as client:
        login_as_admin(client)

        # Create listing and report
        with app.app_context():
            listing = create_test_listing(app, seller_id=2)
            report = create_test_report(app, listing_id=1, reporter_id=2)

        response = client.post('/admin/reports/1/dismiss')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['message'] == 'Report dismissed successfully'
        assert 'report' in data


def test_dismiss_report_not_found(app):
    """Test 404 when report not found for dismissal."""
    create_admin_user(app)

    with app.test_client() as client:
        login_as_admin(client)
        response = client.post('/admin/reports/999/dismiss')
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert data['message'] == 'Report not found or already processed'


def test_dismiss_report_database_error(app, monkeypatch):
    """Test 500 when dismissal fails due to database error."""
    create_admin_user(app)

    # Mock dismiss_report to return database error
    def mock_dismiss_report(report_id):
        return None, "database_error"

    monkeypatch.setattr('app.routes.admin.dismiss_report', mock_dismiss_report)

    with app.test_client() as client:
        login_as_admin(client)
        response = client.post('/admin/reports/1/dismiss')
        assert response.status_code == 500
        data = response.get_json()
        assert data['success'] is False
        assert data['message'] == 'Failed to dismiss report'