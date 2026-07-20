

import pytest
from app import create_app
from app.db import get_db_connection, init_db

@pytest.fixture
def client():
    """Create test client with session"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret'
    
    with app.test_client() as client:
        # Set up test data
        init_db()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create test user
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            ('testuser', 'test@example.com', 'hash')
        )
        user_id = cursor.lastrowid
        
        # Create another user (for testing different reporters)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            ('otheruser', 'other@example.com', 'hash')
        )
        other_id = cursor.lastrowid
        
        # Create test listing
        cursor.execute("""
            INSERT INTO listings (title, description, price, seller_id, status, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, ('Test Listing', 'Description', 100, user_id, 'Active'))
        listing_id = cursor.lastrowid
        
        # Create deleted listing
        cursor.execute("""
            INSERT INTO listings (title, description, price, seller_id, status, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, ('Deleted Listing', 'Description', 100, user_id, 'Deleted'))
        deleted_listing_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        # Store test data in client
        client.test_data = {
            'user_id': user_id,
            'other_id': other_id,
            'listing_id': listing_id,
            'deleted_listing_id': deleted_listing_id
        }
        
        yield client

def test_create_report_success(client):
    """AC1: Test successful report creation (201)"""
    with client.session_transaction() as session:
        session['user_id'] = client.test_data['user_id']
    
    response = client.post(
        f'/api/listings/{client.test_data["listing_id"]}/reports',
        json={
            'reason': 'Counterfeit',
            'description': 'This product appears to be a counterfeit item.'
        }
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['message'] == 'Report created successfully'
    assert 'report' in data
    assert data['report']['reason'] == 'Counterfeit'

def test_create_report_unauthenticated(client):
    """AC5: Test missing authentication (401)"""
    # No session user_id set
    response = client.post(
        f'/api/listings/{client.test_data["listing_id"]}/reports',
        json={
            'reason': 'Spam',
            'description': 'This is spam.'
        }
    )
    
    assert response.status_code == 401
    data = response.get_json()
    assert 'error' in data
    assert 'Unauthorized' in data['error']

def test_create_report_missing_reason(client):
    """AC2: Test missing reason (400)"""
    with client.session_transaction() as session:
        session['user_id'] = client.test_data['user_id']
    
    response = client.post(
        f'/api/listings/{client.test_data["listing_id"]}/reports',
        json={
            'description': 'This is spam.'
        }
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'reason is required' in data['error'].lower()

def test_create_report_missing_description(client):
    """AC3: Test missing description (400)"""
    with client.session_transaction() as session:
        session['user_id'] = client.test_data['user_id']
    
    response = client.post(
        f'/api/listings/{client.test_data["listing_id"]}/reports',
        json={
            'reason': 'Spam'
        }
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'description is required' in data['error'].lower()

def test_create_report_listing_not_found(client):
    """AC4: Test listing not found (404)"""
    with client.session_transaction() as session:
        session['user_id'] = client.test_data['user_id']
    
    response = client.post(
        '/api/listings/99999/reports',
        json={
            'reason': 'Spam',
            'description': 'This is spam.'
        }
    )
    
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
    assert 'Listing not found' in data['error']

def test_create_report_listing_deleted(client):
    """AC4: Test soft-deleted listing (404)"""
    with client.session_transaction() as session:
        session['user_id'] = client.test_data['user_id']
    
    response = client.post(
        f'/api/listings/{client.test_data["deleted_listing_id"]}/reports',
        json={
            'reason': 'Spam',
            'description': 'This is spam.'
        }
    )
    
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
    assert 'Listing not found' in data['error']

def test_create_report_duplicate(client):
    """Test duplicate report from same user"""
    with client.session_transaction() as session:
        session['user_id'] = client.test_data['user_id']
    
    # First report
    response1 = client.post(
        f'/api/listings/{client.test_data["listing_id"]}/reports',
        json={
            'reason': 'Spam',
            'description': 'This is spam.'
        }
    )
    assert response1.status_code == 201
    
    # Second report from same user
    response2 = client.post(
        f'/api/listings/{client.test_data["listing_id"]}/reports',
        json={
            'reason': 'Counterfeit',
            'description': 'This is counterfeit.'
        }
    )
    
    assert response2.status_code == 400
    data = response2.get_json()
    assert 'error' in data
    assert 'already reported' in data['error'].lower()

def test_create_report_invalid_reason(client):
    """Test invalid reason value"""
    with client.session_transaction() as session:
        session['user_id'] = client.test_data['user_id']
    
    response = client.post(
        f'/api/listings/{client.test_data["listing_id"]}/reports',
        json={
            'reason': 'Invalid Reason',
            'description': 'This is spam.'
        }
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'reason must be one of' in data['error'].lower()

def test_create_report_short_description(client):
    """Test description too short"""
    with client.session_transaction() as session:
        session['user_id'] = client.test_data['user_id']
    
    response = client.post(
        f'/api/listings/{client.test_data["listing_id"]}/reports',
        json={
            'reason': 'Spam',
            'description': 'Short'
        }
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'description' in data['error'].lower()