"""Listing routes: browse, search, filter, detail, report."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from ..models import db, Listing, Report

listing_bp = Blueprint('listing', __name__)

ITEMS_PER_PAGE = 10


@listing_bp.route('/listings')
@login_required
def browse():
    """Browse all non-deleted listings with search, filter and pagination."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()
    condition = request.args.get('condition', '').strip()

    query = Listing.query.filter_by(is_deleted=False)
    query = _apply_filters(query, search, category, condition)
    query = query.order_by(Listing.listing_date.desc())

    pagination = query.paginate(page=page, per_page=ITEMS_PER_PAGE, error_out=False)
    return render_template(
        'listings.html',
        listings=pagination.items,
        pagination=pagination,
        search=search,
        category=category,
        condition=condition,
        categories=Listing.CATEGORIES,
        conditions=Listing.CONDITIONS
    )


def _apply_filters(query, search, category, condition):
    """Apply search and filter parameters to the query."""
    if search:
        like = f'%{search}%'
        query = query.filter(
            db.or_(
                Listing.title.ilike(like),
                Listing.description.ilike(like)
            )
        )
    if category:
        query = query.filter_by(category=category)
    if condition:
        query = query.filter_by(condition=condition)
    return query


@listing_bp.route('/listing/<string:listing_id>')
@login_required
def listing_detail(listing_id):
    """Show the detail page for a single listing."""
    listing = Listing.query.get(listing_id)
    if not listing or listing.is_deleted:
        flash('Listing not found.', 'danger')
        return redirect(url_for('listing.browse'))
    return render_template('listing_detail.html', listing=listing,
                           report_reasons=Report.REASONS)


@listing_bp.route('/listing/<string:listing_id>/report', methods=['POST'])
@login_required
def report_listing(listing_id):
    """US#3 – Logged-in user reports a listing as inappropriate."""
    listing = Listing.query.get(listing_id)

    if not listing or listing.is_deleted:
        flash('Listing not found or has been removed.', 'danger')
        return redirect(url_for('listing.browse'))

    reason = request.form.get('reason', '').strip()
    description = request.form.get('description', '').strip()

    error = _validate_report(reason, description)
    if error:
        flash(error, 'danger')
        return redirect(url_for('listing.listing_detail', listing_id=listing_id))

    report = Report(
        listing_id=listing_id,
        reporter_id=current_user.id,
        reason=reason,
        description=description
    )
    db.session.add(report)
    db.session.commit()
    flash('Report submitted. Our team will review it shortly.', 'success')
    return redirect(url_for('listing.listing_detail', listing_id=listing_id))


def _validate_report(reason, description):
    """Validate report form fields. Return error string or None."""
    if not reason:
        return 'Please select a reason for your report.'
    if reason not in Report.REASONS:
        return 'Invalid reason selected.'
    if not description:
        return 'Please provide a description for your report.'
    return None
