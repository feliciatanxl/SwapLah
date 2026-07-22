import pytest
import app.db as db_module
from app.db import (
    admin_delete_reported_listing,
    create_report,
    get_all_reports,
    get_report_by_id,
    create_listing,
    get_listing_by_id,
    soft_delete_listing
)

TEST_CONDITION = 'Good'
TEST_IMAGE_URL = 'https://example.com/image.jpg'


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Create the Flask app against an isolated on-disk test database."""
    test_db = tmp_path / "test_admin_report_unit.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    from app import create_app
    flask_app = create_app()
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = "admin-report-test-secret"
    
    with flask_app.app_context():
        yield flask_app

def test_get_all_reports_empty(app):
    with app.app_context():
        reports = get_all_reports()
        assert reports == []
        assert isinstance(reports, list)

def test_get_all_reports_with_data(app):
    with app.app_context():
        # Create a listing
        create_listing(
            seller_id=1,
            title='Test Listing',
            description='Test Description',
            price=100,
            category='Electronics',
            condition=TEST_CONDITION,
            image_url=TEST_IMAGE_URL,
        )
        
        # Create reports
        create_report(listing_id=1, reporter_id=2, reason='Spam', description='Spam report')
        create_report(listing_id=1, reporter_id=3, reason='Other', description='Fraudulent listing')
        
        reports = get_all_reports()
        
        assert len(reports) == 2
        assert reports[0]['listing_title'] == 'Test Listing'
        assert reports[0]['listing_category'] == 'Electronics'
        assert reports[0]['reason'] in ['Spam', 'Other']
        assert reports[0]['status'] == 'Pending'
        assert 'reporter_display_name' in reports[0]
        assert 'created_at' in reports[0]
        assert 'description' in reports[0]

def test_get_all_reports_join_fields(app):
    with app.app_context():
        # Create listing and report with specific data
        create_listing(
            seller_id=1,
            title='Specific Listing',
            description='Test',
            price=50,
            category='Books',
            condition=TEST_CONDITION,
            image_url=TEST_IMAGE_URL,
        )
        
        # Need to create a user with specific display name for reporter
        from app.db import get_db_connection
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO users (id, student_id, first_name, last_name, display_name, email, contact_number, password_hash) '
            'VALUES (2, "S12345", "Test", "User", "TestUser", "test@test.com", "12345678", "hash")'
        )
        conn.commit()
        conn.close()
        
        create_report(listing_id=1, reporter_id=2, reason='Test Reason', description='Test Description')
        
        reports = get_all_reports()
        
        assert len(reports) == 1
        report = reports[0]
        assert report['listing_title'] == 'Specific Listing'
        assert report['listing_category'] == 'Books'
        assert report['reporter_display_name'] == 'TestUser'
        assert report['reason'] == 'Test Reason'
        assert report['description'] == 'Test Description'
        assert report['status'] == 'Pending'

def test_admin_delete_reported_listing_success(app):
    with app.app_context():
        # Create listing and user
        from app.db import get_db_connection
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO users (id, student_id, first_name, last_name, display_name, email, contact_number, password_hash) '
            'VALUES (1, "S12345", "Test", "User", "TestUser", "test@test.com", "12345678", "hash")'
        )
        conn.commit()
        conn.close()
        
        create_listing(
            seller_id=1,
            title='Test Listing',
            description='Test Description',
            price=100,
            category='Electronics',
            condition=TEST_CONDITION,
            image_url=TEST_IMAGE_URL,
        )
        
        create_report(listing_id=1, reporter_id=2, reason='Spam')
        
        # Get the listing to verify it's active
        listing = get_listing_by_id(1)
        assert listing['status'] == 'Active'
        
        # Admin soft-deletes the reported listing
        success, error = admin_delete_reported_listing(1)
        assert success is True
        assert error is None
        
        # Verify listing is soft-deleted
        listing = get_listing_by_id(1)
        assert listing is None  # get_listing_by_id only returns Active listings
        
        # Verify report is resolved
        report = get_report_by_id(1)
        assert report['status'] == 'Resolved'

def test_admin_delete_reported_listing_not_found(app):
    with app.app_context():
        success, error = admin_delete_reported_listing(999)
        assert success is False
        assert error == "not_found"

def test_admin_delete_reported_listing_already_resolved(app):
    with app.app_context():
        # Create listing and user
        from app.db import get_db_connection
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO users (id, student_id, first_name, last_name, display_name, email, contact_number, password_hash) '
            'VALUES (1, "S12345", "Test", "User", "TestUser", "test@test.com", "12345678", "hash")'
        )
        conn.commit()
        conn.close()
        
        create_listing(
            seller_id=1,
            title='Test Listing',
            description='Test',
            price=100,
            category='Electronics',
            condition=TEST_CONDITION,
            image_url=TEST_IMAGE_URL,
        )
        create_report(listing_id=1, reporter_id=2, reason='Spam')
        
        # First deletion succeeds
        success, _ = admin_delete_reported_listing(1)
        assert success is True
        
        # Second deletion should fail (report already resolved)
        success, error = admin_delete_reported_listing(1)
        assert success is False
        assert error == "not_found"