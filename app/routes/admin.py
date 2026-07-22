"""Admin routes for reviewing and resolving listing reports."""
from flask import Blueprint, jsonify, render_template

from app.auth import admin_required
from app.db import (
    admin_delete_reported_listing,
    dismiss_report,
    get_all_reports,
    get_report_by_id,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("")
@admin_required
def admin_dashboard():
    """Render the admin moderation dashboard with all reports."""
    reports = get_all_reports()
    return render_template("admin.html", reports=reports)


@admin_bp.route("/reports")
@admin_required
def api_admin_reports():
    """Return all reports as JSON."""
    reports = get_all_reports()
    return jsonify({"reports": reports}), 200


@admin_bp.route("/reports/<int:report_id>/delete-listing", methods=["POST"])
@admin_required
def delete_reported_listing(report_id):
    """Admin endpoint to soft-delete a listing from a report."""
    success, error_code = admin_delete_reported_listing(report_id)

    if not success:
        if error_code == "not_found":
            return jsonify({
                "success": False,
                "error": "Report or listing not found or already processed",
            }), 404
        return jsonify({"success": False, "error": "Database error"}), 500

    report = get_report_by_id(report_id)

    return jsonify({
        "success": True,
        "message": "Listing soft-deleted successfully",
        "report": report,
    }), 200


@admin_bp.route("/reports/<int:report_id>/dismiss", methods=["POST"])
@admin_required
def dismiss_report_route(report_id):
    """Dismiss a pending report. Only admins can do this."""
    report, error = dismiss_report(report_id)

    if error == "not_found":
        return jsonify({
            "success": False,
            "message": "Report not found or already processed",
        }), 404

    if error:
        return jsonify({"success": False, "message": "Failed to dismiss report"}), 500

    return jsonify({
        "success": True,
        "message": "Report dismissed successfully",
        "report": report,
    }), 200
