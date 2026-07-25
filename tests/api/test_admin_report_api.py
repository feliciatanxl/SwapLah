import pytest
import app.db as db_module
from app import create_app
from app.db import create_listing, create_report, get_db_connection

@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a Flask test client using an isolated SQLite database."""
    test_db = tmp_path / "test_admin_reports_api.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "admin-reports-api-test-secret"

    with flask_app.test_client() as test_client:
        with flask_app.app_context():
            # Seed users
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO users (id, student_id, first_name, last_name, display_name, email, contact_number, password_hash, role) '
                'VALUES (1, "S10001", "Admin", "User", "AdminUser", "admin@mymail.nyp.edu.sg", "12345678", "hash", "admin")'
            )
            conn.execute(
                'INSERT INTO users (id, student_id, first_name, last_name, display_name, email, contact_number, password_hash, role) '
                'VALUES (2, "S10002", "Regular", "User", "RegularUser", "user@mymail.nyp.edu.sg", "87654321", "hash", "user")'
            )
            conn.execute(
                'INSERT INTO users (id, student_id, first_name, last_name, display_name, email, contact_number, password_hash, role) '
                'VALUES (3, "S10003", "Test", "User", "TestUser", "test@mymail.nyp.edu.sg", "11111111", "hash", "user")'
            )
            conn.commit()
            conn.close()

            # Seed listings
            create_listing(
                seller_id=2,
                title='Test Listing 1',
                description='Test Description 1',
                price=100,
                category='Electronics',
                condition='Good',
                image_url='http://example.com/img1.jpg'
            )
            create_listing(
                seller_id=2,
                title='Test Listing 2',
                description='Test Description 2',
                price=200,
                category='Books',
                condition='Good',
                image_url='http://example.com/img2.jpg'
            )

            # Seed reports
            create_report(listing_id=1, reporter_id=3, reason='Spam', description='This is spam')
            create_report(listing_id=2, reporter_id=3, reason='Other', description='Fraudulent listing')
        yield test_client

def login_as(client, user_id):
    with client.session_transaction() as sess:
        sess['user_id'] = user_id

def test_ac1_admin_get_reports_success(client):
    """AC1: Admin can successfully get all reports."""
    login_as(client, 1)  # Admin user

    response = client.get('/admin/reports')
    assert response.status_code == 200
    data = response.get_json()

    assert 'reports' in data
    assert len(data['reports']) == 2

    # Verify report structure
    report = data['reports'][0]
    assert 'id' in report
    assert 'listing_id' in report
    assert 'listing_title' in report
    assert 'listing_category' in report
    assert 'reporter_display_name' in report
    assert 'reason' in report
    assert 'description' in report
    assert 'status' in report
    assert 'created_at' in report

def test_ac2_non_admin_forbidden(client):
    """AC2: Non-admin users get 403 error."""
    login_as(client, 2)  # Regular user

    response = client.get('/admin/reports')
    assert response.status_code == 403

    # Also test HTML endpoint
    response = client.get('/admin')
    assert response.status_code == 403

def test_ac2_not_logged_in_redirect(client):
    """AC2: Not logged in users get redirected."""
    response = client.get('/admin')
    # Should redirect to login (302) or return 401
    assert response.status_code in (302, 401)

    response = client.get('/admin/reports')
    assert response.status_code in (302, 401)

def test_ac3_each_item_has_required_fields(client):
    """AC3: Each report item has listing, reason, and description fields."""
    login_as(client, 1)  # Admin user

    response = client.get('/admin/reports')
    assert response.status_code == 200
    data = response.get_json()

    for report in data['reports']:
        # Check required fields
        assert 'listing_title' in report
        assert 'listing_category' in report
        assert 'reason' in report
        assert 'description' in report
        assert 'status' in report
        assert 'reporter_display_name' in report

        # Check values are not empty (unless description is None)
        assert report['listing_title'] is not None
        assert report['listing_category'] is not None
        assert report['reason'] is not None
        # Description can be None or empty
        assert report['status'] in ['Pending', 'Resolved']

def test_get_all_reports_html_template(client):
    """Test that the HTML endpoint renders the template with reports data."""
    login_as(client, 1)  # Admin user

    response = client.get('/admin')
    assert response.status_code == 200

    # Check that the response contains report data
    html = response.get_data(as_text=True)
    assert 'Test Listing 1' in html
    assert 'Test Listing 2' in html
    assert 'Spam' in html
    assert 'Other' in html
    assert 'Status' in html

def test_empty_reports(client):
    """Test behavior when there are no reports."""
    # Delete all reports
    from app.db import get_db_connection
    with client.application.app_context():
        conn = get_db_connection()
        conn.execute('DELETE FROM reports')
        conn.commit()
        conn.close()

    login_as(client, 1)  # Admin user

    response = client.get('/admin/reports')
    assert response.status_code == 200
    data = response.get_json()
    assert data['reports'] == []
