"""Admin routes: reports management and user management."""
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from ..models import db, Report, User, Listing

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(func):
    """Decorator: restrict route to admin users only (server-side check)."""
    @wraps(func)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash('Access denied. Admins only.', 'danger')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return decorated


# ── Reports ──────────────────────────────────────────────────────────────────

@admin_bp.route('/reports')
@login_required
@admin_required
def view_reports():
    """US#2 – Admin views all submitted listing reports."""
    reports = Report.query.order_by(Report.created_at.desc()).all()
    return render_template('admin/reports.html', reports=reports)


@admin_bp.route('/reports/<string:report_id>/delete-listing', methods=['POST'])
@login_required
@admin_required
def delete_reported_listing(report_id):
    """US#1 – Admin soft-deletes the listing tied to a report."""
    report = Report.query.get(report_id)
    if not report:
        flash('Report not found.', 'danger')
        return redirect(url_for('admin.view_reports'))

    listing = Listing.query.get(report.listing_id)
    if not listing or listing.is_deleted:
        flash('Listing not found or already deleted.', 'warning')
        return redirect(url_for('admin.view_reports'))

    listing.is_deleted = True
    report.status = 'Actioned'
    db.session.commit()
    flash('Listing has been removed from the marketplace.', 'success')
    return redirect(url_for('admin.view_reports'))


@admin_bp.route('/reports/<string:report_id>/dismiss', methods=['POST'])
@login_required
@admin_required
def dismiss_report(report_id):
    """US#4 – Admin dismisses a report without deleting the listing."""
    report = Report.query.get(report_id)
    if not report:
        flash('Report not found.', 'danger')
        return redirect(url_for('admin.view_reports'))

    report.status = 'Dismissed'
    db.session.commit()
    flash('Report has been dismissed.', 'success')
    return redirect(url_for('admin.view_reports'))


# ── Users ─────────────────────────────────────────────────────────────────────

@admin_bp.route('/users')
@login_required
@admin_required
def view_users():
    """US#5 – Admin views all registered user accounts."""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/<string:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """US#6 – Admin toggles a user's status between Active and Suspended."""
    user = User.query.get(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.view_users'))

    if user.is_admin:
        flash('Cannot suspend another admin account.', 'warning')
        return redirect(url_for('admin.view_users'))

    user.status = 'Suspended' if user.status == 'Active' else 'Active'
    db.session.commit()
    flash(f'{user.display_name} is now {user.status}.', 'success')
    return redirect(url_for('admin.view_users'))


# ── Admin API (JSON responses for AJAX) ──────────────────────────────────────

@admin_bp.route('/api/reports', methods=['GET'])
@login_required
@admin_required
def api_reports():
    """Return all reports as JSON."""
    reports = Report.query.order_by(Report.created_at.desc()).all()
    return jsonify([r.to_dict() for r in reports])


@admin_bp.route('/api/users', methods=['GET'])
@login_required
@admin_required
def api_users():
    """Return all users as JSON."""
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([u.to_dict() for u in users])
