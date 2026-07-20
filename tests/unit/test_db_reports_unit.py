

import pytest
from app.db import create_report, get_db_connection, init_db

@pytest.fixture
def setup_db():
    """Set up test database with required tables"""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create test user
    cursor.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
        ('testuser', 'test@example.com', 'hash')
    )
    user_id = cursor.lastrowid
    
    # Create test listing
    cursor.execute("""
        INSERT INTO listings (title, description, price, seller_id, status, created_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
    """, ('Test Listing', 'Description', 100, user_id, 'Active'))
    listing_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    yield {'user_id': user_id, 'listing_id': listing_id}
    
    # Cleanup
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reports")
    cursor.execute("DELETE FROM listings")
    cursor.execute("DELETE FROM users")
    conn.commit()
    conn.close()

def test_create_report_success(setup_db):
    """Test successful report creation"""
    report = create_report(
        listing_id=setup_db['listing_id'],
        reporter_id=setup_db['user_id'],
        reason='Counterfeit',
        description='This appears to be a fake product.'
    )
    
    assert report['listing_id'] == setup_db['listing_id']
    assert report['reporter_id'] == setup_db['user_id']
    assert report['reason'] == 'Counterfeit'
    assert report['description'] == 'This appears to be a fake product.'
    assert 'created_at' in report

def test_create_report_listing_not_found(setup_db):
    """Test error when listing doesn't exist"""
    with pytest.raises(ValueError, match="Listing not found"):
        create_report(
            listing_id=99999,
            reporter_id=setup_db['user_id'],
            reason='Spam',
            description='Test description'
        )

def test_create_report_listing_deleted(setup_db):
    """Test error when listing is deleted"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE listings SET status = 'Deleted' WHERE id = ?",
        (setup_db['listing_id'],)
    )
    conn.commit()
    conn.close()
    
    with pytest.raises(ValueError, match="Listing is already deleted"):
        create_report(
            listing_id=setup_db['listing_id'],
            reporter_id=setup_db['user_id'],
            reason='Spam',
            description='Test description'
        )

def test_create_report_invalid_reason(setup_db):
    """Test error with invalid reason"""
    with pytest.raises(ValueError, match="Reason must be one of"):
        create_report(
            listing_id=setup_db['listing_id'],
            reporter_id=setup_db['user_id'],
            reason='Invalid reason',
            description='Test description'
        )

def test_create_report_short_description(setup_db):
    """Test error with description too short"""
    with pytest.raises(ValueError, match="Description must be at least 10 characters"):
        create_report(
            listing_id=setup_db['listing_id'],
            reporter_id=setup_db['user_id'],
            reason='Spam',
            description='Too short'
        )

def test_create_report_duplicate(setup_db):
    """Test error when user already reported the listing"""
    # First report
    create_report(
        listing_id=setup_db['listing_id'],
        reporter_id=setup_db['user_id'],
        reason='Spam',
        description='This is spam.'
    )
    
    # Second report from same user
    with pytest.raises(ValueError, match="You have already reported this listing"):
        create_report(
            listing_id=setup_db['listing_id'],
            reporter_id=setup_db['user_id'],
            reason='Counterfeit',
            description='This is also counterfeit.'
        )