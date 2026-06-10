"""Admin routes: reports and user management (US1-US8)."""
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from app.db import (
    get_all_reports,
    get_report_by_id,
    soft_delete_listing,
    dismiss_report,
    get_all_users,
    toggle_user_status,
    get_listing_by_id,
)
from flask import session

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

REPORT_REASONS = [
    'Prohibited Item',
    'Misleading Description',
    'Spam or Duplicate',
    'Inappropriate Content',
    'Suspected Scam',
    'Other'
]


def admin_required(func):
    """Decorator: restrict route to admin users only."""
    @wraps(func)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in.', 'danger')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Access denied. Admins only.', 'danger')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return decorated


# ── Reports (US1, US2, US4) ───────────────────────────────────────────────────

@admin_bp.route('/reports')
@admin_required
def view_reports():
    """US2 – Admin views all submitted listing reports."""
    reports = get_all_reports()
    return render_template('admin/reports.html', reports=reports)


@admin_bp.route('/reports/<int:report_id>/delete-listing', methods=['POST'])
@admin_required
def delete_reported_listing(report_id):
    """US1 – Admin soft-deletes the listing tied to a report."""
    report = get_report_by_id(report_id)
    if not report:
        flash('Report not found.', 'danger')
        return redirect(url_for('admin.api_users'))

    listing = get_listing_by_id(report['listing_id'])
    if not listing or listing.get('is_deleted'):
        flash('Listing not found or already deleted.', 'warning')
        return redirect(url_for('admin.api_users'))

    soft_delete_listing(report['listing_id'])
    flash('Listing has been removed from the marketplace.', 'success')
    return redirect(url_for('admin.api_users'))


@admin_bp.route('/reports/<int:report_id>/dismiss', methods=['POST'])
@admin_required
def dismiss_report_route(report_id):
    """US4 – Admin dismisses a report without deleting the listing."""
    report = get_report_by_id(report_id)
    if not report:
        flash('Report not found.', 'danger')
        return redirect(url_for('admin.api_users'))

    dismiss_report(report_id)
    flash('Report has been dismissed.', 'success')
    return redirect(url_for('admin.api_users'))


# ── Users (US5, US6) ──────────────────────────────────────────────────────────

@admin_bp.route('/users')
@admin_required
def view_users():
    """US5 – Admin views all registered user accounts."""
    users = get_all_users()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_status(user_id):
    """US6 – Admin toggles a user's status between Active and Suspended."""
    new_status = toggle_user_status(user_id)
    if new_status is None:
        flash('User not found.', 'danger')
    else:
        flash(f'User status updated to {new_status}.', 'success')
    return redirect(url_for('admin.api_users'))


# ── Admin JSON API ────────────────────────────────────────────────────────────

@admin_bp.route('/api/reports')
@admin_required
def api_reports():
    """Return all reports as JSON."""
    return jsonify(get_all_reports())


@admin_bp.route('/api/users')
@admin_required
def api_users():
    """Return all users as JSON."""
    return jsonify(get_all_users())
