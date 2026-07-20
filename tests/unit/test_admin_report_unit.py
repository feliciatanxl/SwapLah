# tests/unit/test_admin_reports.py

import pytest
from app.db import (
    admin_delete_reported_listing,
    create_report,
    get_all_reports,
    get_report_by_id,
    create_listing,
    get_listing_by_id,
    soft_delete_listing
)

@pytest.fixture
def app():
    from app import create_app
    app = create_app(testing=True)
    app.config['DATABASE'] = ':memory:'
    return app

def test_get_all_reports_empty(app):
    with app.app_context():
        reports = get_all_reports()
        assert reports == []
        assert isinstance(reports, list)

def test_get_all_reports_with_data(app):
    with app.app_context():
        # Create a listing
        create_listing(
            title='Test Listing',
            description='Test Description',
            price=100,
            seller_id=1,
            category='Electronics'
        )
        
        # Create reports
        create_report(listing_id=1, reporter_id=2, reason='Spam', description='Spam report')
        create_report(listing_id=1, reporter_id=3, reason='Fraud', description='Fraudulent listing')
        
        reports = get_all_reports()
        
        assert len(reports) == 2
        assert reports[0]['listing_title'] == 'Test Listing'
        assert reports[0]['listing_category'] == 'Electronics'
        assert reports[0]['reason'] in ['Spam', 'Fraud']
        assert reports[0]['status'] == 'Pending'
        assert 'reporter_display_name' in reports[0]
        assert 'created_at' in reports[0]
        assert 'description' in reports[0]

def test_get_all_reports_join_fields(app):
    with app.app_context():
        # Create listing and report with specific data
        create_listing(
            title='Specific Listing',
            description='Test',
            price=50,
            seller_id=1,
            category='Books'
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
            title='Test Listing',
            description='Test Description',
            price=100,
            seller_id=1,
            category='Electronics'
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
            title='Test Listing',
            description='Test',
            price=100,
            seller_id=1,
            category='Electronics'
        )
        create_report(listing_id=1, reporter_id=2, reason='Spam')
        
        # First deletion succeeds
        success, _ = admin_delete_reported_listing(1)
        assert success is True
        
        # Second deletion should fail (report already resolved)
        success, error = admin_delete_reported_listing(1)
        assert success is False
        assert error == "not_found"