# app/routes/reports.py

from flask import Blueprint, request, jsonify, session
from app.db import create_report, get_listing_by_id

reports_bp = Blueprint('reports', __name__, url_prefix='/api')

ALLOWED_REASONS = [
    "Counterfeit",
    "Prohibited item",
    "Spam",
    "Inappropriate content",
    "Other"
]


def _validate_report_payload(data):
    """
    Validate the incoming report payload.

    Returns:
        (reason, description, None) on success
        (None, None, (response, status_code)) on validation failure
    """
    if not data:
        return None, None, (jsonify({"error": "Invalid JSON data"}), 400)

    reason = data.get('reason')
    if not reason:
        return None, None, (jsonify({"error": "reason is required"}), 400)

    description = data.get('description')
    if not description or not description.strip():
        return None, None, (jsonify({"error": "description is required"}), 400)

    if reason not in ALLOWED_REASONS:
        return None, None, (jsonify({
            "error": f"reason must be one of: {', '.join(ALLOWED_REASONS)}"
        }), 400)

    return reason, description, None


@reports_bp.route('/listings/<int:listing_id>/reports', methods=['POST'])
def create_listing_report(listing_id):
    """
    Create a new report for a listing.

    AC1: 201 + created report on success
    AC2: 400 if reason missing
    AC3: 400 if description missing
    AC4: 404 if listing not found or soft-deleted
    AC5: 401 if session["user_id"] missing
    """
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True)
    reason, description, error = _validate_report_payload(data)
    if error:
        return error

    try:
        report = create_report(listing_id, user_id, reason, description)
        return jsonify({
            "message": "Report created successfully",
            "report": report
        }), 201
    except ValueError as e:
        if "Listing not found" in str(e) or "Listing is already deleted" in str(e):
            return jsonify({"error": "Listing not found"}), 404
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500