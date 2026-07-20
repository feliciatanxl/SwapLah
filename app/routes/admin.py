from flask import Blueprint, request, jsonify, render_template
from app.auth import admin_required
from app.db import admin_delete_reported_listing, get_report_by_id, get_all_reports

admin_bp = Blueprint("admin", __name__)

@admin_bp.route('/admin/reports')
@admin_required
def admin_reports():
    """Render admin page with reports data."""
    reports = get_all_reports()
    return render_template('admin.html', reports=reports)

@admin_bp.route('/api/admin/reports')
@admin_required
def api_admin_reports():
    """Return all reports as JSON."""
    reports = get_all_reports()
    return jsonify({"reports": reports}), 200

@admin_bp.route('/admin/reports/<int:report_id>/delete-listing', methods=['POST'])
@admin_required
def delete_reported_listing(report_id):
    """Admin endpoint to soft-delete a listing from a report."""
    success, error_code = admin_delete_reported_listing(report_id)
    
    if not success:
        if error_code == "not_found":
            return jsonify({
                "success": False,
                "error": "Report or listing not found or already processed"
            }), 404
        else:
            return jsonify({
                "success": False,
                "error": "Database error"
            }), 500
    
    # Get updated report data for response
    report = get_report_by_id(report_id)
    
    return jsonify({
        "success": True,
        "message": "Listing soft-deleted successfully",
        "report": report
    }), 200