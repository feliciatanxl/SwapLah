
import pytest
from app.db import (
    admin_delete_reported_listing,
    create_report,
    get_report_by_id,
    create_listing,
    get_listing_by_id,
    soft_delete_listing
)
from app import create_app

@pytest.fixture
def app():
    app = create_app(testing=True)
    app.config['DATABASE'] = ':memory:'
    return app

def test_admin_delete_reported_listing_success(app):
    with app.app_context():
        # Create a listing
        create_listing(
            title='Test Listing',
            description='Test Description',
            price=100,
            seller_id=1,
            category='Electronics'
        )
        
        # Create a report
        create_report(listing_id=1, reporter_id=2, reason='Spam', description='Test report')
        
        # Get the listing to verify it's active
        listing = get_listing_by_id(1)
        assert listing['status'] == 'Active'
        
        # Admin soft-deletes the reported listing
        success, error = admin_delete_reported_listing(1)
        assert success is True
        assert error is None
        
        # Verify listing is soft-deleted
        listing = get_listing_by_id(1)
        assert listing['status'] == 'Deleted'
        
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
        # Create listing and report
        create_listing(title='Test', description='Test', price=100, seller_id=1, category='Electronics')
        create_report(listing_id=1, reporter_id=2, reason='Spam')
        
        # First deletion succeeds
        success, _ = admin_delete_reported_listing(1)
        assert success is True
        
        # Second deletion should fail (report already resolved)
        success, error = admin_delete_reported_listing(1)
        assert success is False
        assert error == "not_found"

def test_admin_delete_reported_listing_already_deleted_listing(app):
    with app.app_context():
        # Create listing
        create_listing(title='Test', description='Test', price=100, seller_id=1, category='Electronics')
        create_report(listing_id=1, reporter_id=2, reason='Spam')
        
        # Soft delete the listing first (as if seller deleted it)
        success, _ = soft_delete_listing(1, 1)
        assert success is True
        
        # Admin attempt should fail
        success, error = admin_delete_reported_listing(1)
        assert success is False
        assert error == "not_found"