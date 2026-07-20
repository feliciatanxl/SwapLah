# app/routes/reports.py

from flask import Blueprint, request, jsonify, session
from app.db import create_report, get_listing_by_id

reports_bp = Blueprint('reports', __name__, url_prefix='/api')

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
    # AC5: Check authentication
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Get JSON data
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400
    
    # AC2: Validate reason
    reason = data.get('reason')
    if not reason:
        return jsonify({"error": "reason is required"}), 400
    
    # AC3: Validate description
    description = data.get('description')
    if not description or not description.strip():
        return jsonify({"error": "description is required"}), 400
    
    # Validate reason against allowed list
    allowed_reasons = [
        "Counterfeit",
        "Prohibited item",
        "Spam",
        "Inappropriate content",
        "Other"
    ]
    if reason not in allowed_reasons:
        return jsonify({
            "error": f"reason must be one of: {', '.join(allowed_reasons)}"
        }), 400
    
    try:
        # AC4: This will raise ValueError if listing not found or deleted
        report = create_report(listing_id, user_id, reason, description)
        
        # AC1: Return success with 201 status
        return jsonify({
            "message": "Report created successfully",
            "report": report
        }), 201
        
    except ValueError as e:
        # AC4: Handle listing not found or deleted
        if "Listing not found" in str(e) or "Listing is already deleted" in str(e):
            return jsonify({"error": "Listing not found"}), 404
        # Handle other validation errors
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500