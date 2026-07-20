
import pytest
from app import create_app
from app.db import create_listing, create_report, get_listing_by_id, get_report_by_id

@pytest.fixture
def client():
    app = create_app(testing=True)
    app.config['DATABASE'] = ':memory:'
    with app.test_client() as client:
        with app.app_context():
            # Seed users
            conn = app.db_connection()
            conn.execute(
                'INSERT INTO users (id, username, email, password, role) VALUES (1, "admin", "admin@test.com", "hash", "admin")'
            )
            conn.execute(
                'INSERT INTO users (id, username, email, password, role) VALUES (2, "user", "user@test.com", "hash", "user")'
            )
            conn.commit()
            
            # Seed listing and report
            create_listing(title='Test Listing', description='Test', price=100, seller_id=2, category='Electronics')
            create_report(listing_id=1, reporter_id=2, reason='Spam', description='Test report')
        yield client

def login_as(client, user_id):
    with client.session_transaction() as sess:
        sess['user_id'] = user_id

def test_ac1_admin_delete_success(client):
    """AC1: Admin can successfully soft-delete a reported listing."""
    login_as(client, 1)  # Admin user
    
    # Verify listing is active
    listing = get_listing_by_id(1)
    assert listing['status'] == 'Active'
    
    response = client.post('/admin/reports/1/delete-listing')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    
    # Verify listing is soft-deleted
    listing = get_listing_by_id(1)
    assert listing['status'] == 'Deleted'
    
    # Verify report is resolved
    report = get_report_by_id(1)
    assert report['status'] == 'Resolved'

def test_ac2_deleted_listing_hidden_from_listings(client):
    """AC2: Deleted listing is hidden from GET /api/listings."""
    login_as(client, 1)  # Admin user
    
    # Delete the listing
    response = client.post('/admin/reports/1/delete-listing')
    assert response.status_code == 200
    
    # Try to get listings
    response = client.get('/api/listings')
    assert response.status_code == 200
    data = response.get_json()
    
    # Should not include the deleted listing
    listings = data.get('listings', [])
    assert all(l['id'] != 1 for l in listings)

def test_ac3_non_admin_forbidden(client):
    """AC3: Non-admin users get 403 error."""
    login_as(client, 2)  # Regular user
    
    response = client.post('/admin/reports/1/delete-listing')
    assert response.status_code == 403
    
    # Verify nothing changed
    listing = get_listing_by_id(1)
    assert listing['status'] == 'Active'
    report = get_report_by_id(1)
    assert report['status'] == 'Pending'

def test_ac4_nonexistent_report_404(client):
    """AC4: 404 for already-deleted or nonexistent report."""
    login_as(client, 1)  # Admin user
    
    # Try with non-existent report
    response = client.post('/admin/reports/999/delete-listing')
    assert response.status_code == 404
    data = response.get_json()
    assert data['success'] is False
    assert 'not found' in data['error'].lower()
    
    # Delete the valid report first
    response = client.post('/admin/reports/1/delete-listing')
    assert response.status_code == 200
    
    # Try again with already-resolved report
    response = client.post('/admin/reports/1/delete-listing')
    assert response.status_code == 404
    data = response.get_json()
    assert data['success'] is False
    assert 'not found' in data['error'].lower()

def test_unauthenticated_user(client):
    """Test that unauthenticated users cannot access admin endpoint."""
    response = client.post('/admin/reports/1/delete-listing')
    # Should redirect to login or return 401
    assert response.status_code in (302, 401)