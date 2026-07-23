import pytest
from flask import Flask, session
from app.routes.reports import reports_bp, _validate_report_payload

@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = 'test-secret'
    app.register_blueprint(reports_bp)
    return app

def test_validate_report_payload_valid():
    reason, description, error = _validate_report_payload({
        'reason': 'Spam',
        'description': 'This is spam'
    })
    assert reason == 'Spam'
    assert description == 'This is spam'
    assert error is None

def test_validate_report_payload_missing_reason():
    _, _, error = _validate_report_payload({'description': 'test'})
    assert error[1] == 400
    assert error[0].json['error'] == 'reason is required'

def test_validate_report_payload_missing_description():
    _, _, error = _validate_report_payload({'reason': 'Spam'})
    assert error[1] == 400
    assert error[0].json['error'] == 'description is required'

def test_validate_report_payload_invalid_reason():
    _, _, error = _validate_report_payload({
        'reason': 'Invalid',
        'description': 'test'
    })
    assert error[1] == 400
    assert 'reason must be one of' in error[0].json['error']

def test_create_listing_report_unauthenticated(app):
    with app.test_client() as client:
        response = client.post('/api/listings/1/reports', json={
            'reason': 'Spam',
            'description': 'This is spam'
        })
        assert response.status_code == 401
        assert response.json['error'] == 'Unauthorized'