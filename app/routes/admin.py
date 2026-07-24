"""Admin routes for reviewing and resolving listing reports."""
from flask import Blueprint, jsonify, render_template, request

from app.auth import admin_required
from app.db import (
    admin_delete_reported_listing,
    dismiss_report,
    get_all_reports,
    get_listing_category_summary,
    get_report_by_id,
)
from app.user_admin import get_all_users, update_user_status

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("")
@admin_required
def admin_dashboard():
    """Render the admin moderation dashboard with all reports and users."""
    reports = get_all_reports()
    users = get_all_users()
    active_listings_count = get_listing_category_summary()["total"]
    return render_template(
        "admin.html",
        reports=reports,
        users=users,
        active_listings_count=active_listings_count,
    )


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


@admin_bp.route("/users")
@admin_required
def api_admin_users():
    """Return all users as JSON."""
    users = get_all_users()
    return jsonify({"users": users}), 200


@admin_bp.route("/users/<int:user_id>/status", methods=["POST"])
@admin_required
def update_user_status_route(user_id):
    """
    Admin endpoint to toggle a user's status between Active and Suspended.
    Expects JSON body: {"status": "Active"} or {"status": "Suspended"}.
    """
    data = request.get_json(silent=True)
    if not data or not data.get("status"):
        return jsonify({"success": False, "error": "status is required"}), 400

    status = data["status"]
    if status not in ("Active", "Suspended"):
        return jsonify({"success": False, "error": "status must be Active or Suspended"}), 400

    user = update_user_status(user_id, status)
    if user is None:
        return jsonify({"success": False, "error": "User not found"}), 404

    return jsonify({"success": True, "user": user}), 200