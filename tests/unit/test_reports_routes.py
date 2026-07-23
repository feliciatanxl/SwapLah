import pytest
import app.db as db_module
from app import create_app
from app.routes.reports import reports_bp, ALLOWED_REASONS


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Create the Flask app against an isolated on-disk test database."""
    test_db = tmp_path / "test_reports_routes_unit.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = "reports-routes-test-secret"
    
    with flask_app.app_context():
        yield flask_app


def test_validate_report_payload_valid(app):
    """Test valid payload returns reason and description."""
    with app.app_context():
        from app.routes.reports import _validate_report_payload
        reason, description, error = _validate_report_payload({
            'reason': 'Spam',
            'description': 'This is spam'
        })
        assert reason == 'Spam'
        assert description == 'This is spam'
        assert error is None


def test_validate_report_payload_missing_reason(app):
    """Test missing reason returns error response (covers line 26)."""
    with app.app_context():
        from app.routes.reports import _validate_report_payload
        _, _, error = _validate_report_payload({'description': 'test'})
        assert error[1] == 400
        assert error[0].json['error'] == 'reason is required'


def test_validate_report_payload_missing_description(app):
    """Test missing description returns error response."""
    with app.app_context():
        from app.routes.reports import _validate_report_payload
        _, _, error = _validate_report_payload({'reason': 'Spam'})
        assert error[1] == 400
        assert error[0].json['error'] == 'description is required'


def test_validate_report_payload_invalid_reason(app):
    """Test invalid reason returns error with allowed reasons."""
    with app.app_context():
        from app.routes.reports import _validate_report_payload
        _, _, error = _validate_report_payload({
            'reason': 'Invalid',
            'description': 'test'
        })
        assert error[1] == 400
        assert 'reason must be one of' in error[0].json['error']


def test_create_listing_report_unauthenticated(app):
    """Test 401 when not logged in (covers line 59)."""
    with app.test_client() as client:
        response = client.post('/api/listings/1/reports', json={
            'reason': 'Spam',
            'description': 'This is spam'
        })
        assert response.status_code == 401
        assert response.json['error'] == 'Unauthorized'


def test_create_listing_report_invalid_json(app):
    """Test 400 when invalid JSON is sent (covers _validate_report_payload not data branch)."""
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 1
        
        response = client.post('/api/listings/1/reports', data='invalid json', 
                              content_type='application/json')
        assert response.status_code == 400
        assert response.json['error'] == 'Invalid JSON data'


def test_create_listing_report_success(app, monkeypatch):
    """Test 201 success (covers line 66-72)."""
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 1
        
        # Mock create_report to return a report
        def mock_create_report(listing_id, user_id, reason, description):
            return {
                'id': 1,
                'listing_id': listing_id,
                'reporter_id': user_id,
                'reason': reason,
                'description': description,
                'status': 'Pending'
            }
        
        monkeypatch.setattr('app.routes.reports.create_report', mock_create_report)
        
        response = client.post('/api/listings/1/reports', json={
            'reason': 'Spam',
            'description': 'This is spam'
        })
        assert response.status_code == 201
        assert response.json['message'] == 'Report created successfully'
        assert 'report' in response.json


def test_create_listing_report_listing_not_found(app, monkeypatch):
    """Test 404 when listing not found (covers line 75-76)."""
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 1
        
        # Mock create_report to raise ValueError with listing not found message
        def mock_create_report(listing_id, user_id, reason, description):
            raise ValueError("Listing not found")
        
        monkeypatch.setattr('app.routes.reports.create_report', mock_create_report)
        
        response = client.post('/api/listings/999/reports', json={
            'reason': 'Spam',
            'description': 'This is spam'
        })
        assert response.status_code == 404
        assert response.json['error'] == 'Listing not found'


def test_create_listing_report_value_error(app, monkeypatch):
    """Test 400 for other ValueError (covers line 78)."""
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 1
        
        # Mock create_report to raise ValueError with other message
        def mock_create_report(listing_id, user_id, reason, description):
            raise ValueError("Some other error")
        
        monkeypatch.setattr('app.routes.reports.create_report', mock_create_report)
        
        response = client.post('/api/listings/1/reports', json={
            'reason': 'Spam',
            'description': 'This is spam'
        })
        assert response.status_code == 400
        assert response.json['error'] == 'Some other error'


def test_create_listing_report_generic_exception(app, monkeypatch):
    """Test 500 for generic exception (covers line 79-80)."""
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 1
        
        # Mock create_report to raise generic Exception
        def mock_create_report(listing_id, user_id, reason, description):
            raise Exception("Database connection error")
        
        monkeypatch.setattr('app.routes.reports.create_report', mock_create_report)
        
        response = client.post('/api/listings/1/reports', json={
            'reason': 'Spam',
            'description': 'This is spam'
        })
        assert response.status_code == 500
        assert response.json['error'] == 'Internal server error'