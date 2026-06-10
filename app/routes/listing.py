"""Listing routes: browse, search, filter, detail, report (US3)."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app.db import (
    get_all_listings,
    get_listing_by_id,
    create_listing,
    create_report,
    get_report_by_id,
    REPORT_REASONS,
)

listings_bp = Blueprint('listings', __name__)

CATEGORIES = ['Textbooks', 'Electronics', 'Lab Equipment',
              'Clothing', 'Stationery', 'Others']
CONDITIONS = ['New', 'Like New', 'Good', 'Fair']
ITEMS_PER_PAGE = 10


# ── API endpoints ─────────────────────────────────────────────────────────────

@listings_bp.route('/api/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})


@listings_bp.route('/api/listings', methods=['GET'])
def api_get_listings():
    """Return all active listings as JSON. Supports ?category= and ?search=."""
    listings = get_all_listings()
    category = request.args.get('category', '').strip()
    search = request.args.get('search', '').strip().lower()

    if category:
        listings = [l for l in listings if l.get('category') == category]
    if search:
        listings = [l for l in listings if
                    search in l.get('title', '').lower() or
                    search in l.get('description', '').lower()]

    return jsonify(listings)


# app/routes/listing.py

@listings_bp.route('/api/listings/<int:listing_id>', methods=['GET'])
def api_get_listing(listing_id):
    listing = get_listing_by_id(listing_id)
    if not listing or listing.get('is_deleted'):
        return jsonify({'error': 'Listing not found or unavailable.'}), 404  # fix 1: message changed
    return jsonify({                                                           # fix 2: wrap in 'listing' key
        'listing': {
            'id': listing['id'],
            'title': listing['title'],
            'description': listing['description'],
            'price': listing['price'],
            'category': listing['category'],
            'condition': listing.get('item_condition') or listing.get('condition'),
            'images': listing.get('images'),
            'image': listing.get('image'),
            'listingDate': listing['listing_date'],
            'lastModifiedTimestamp': listing['last_modified_timestamp'],
            'seller': {
                'displayName': listing.get('seller_display_name'),
                'email': listing.get('seller_email'),
                'contactNumber': listing.get('seller_contact_number'),
            }
        }
    })


@listings_bp.route('/api/listings', methods=['POST'])
def api_create_listing():
    """Create a new listing."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json(silent=True, force=True)
    if not data:
        return jsonify({'error': 'Invalid request body'}), 400

    error = _validate_listing(data)
    if error:
        return jsonify({'error': error}), 400

    listing = create_listing(
        seller_id=session['user_id'],
        title=data['title'].strip(),
        description=data['description'].strip(),
        price=data['price'].strip(),
        category=data['category'],
        condition=data['condition'],
        image_url=data.get('imageUrl', '')
    )

    return jsonify({
        'message': 'Listing created successfully.',
        'listing': {
            'id': listing['id'],
            'sellerId': listing['seller_id'],
            'title': listing['title'],
            'description': listing['description'],
            'price': listing['price'],
            'category': listing['category'],
            'condition': listing['item_condition'],
            'listingDate': listing['listing_date'],
            'lastModifiedTimestamp': listing['last_modified_timestamp'],
        }
    }), 201


@listings_bp.route('/api/listings/<int:listing_id>', methods=['PUT'])
def api_update_listing(listing_id):
    """Update a listing. Owner only."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    listing = get_listing_by_id(listing_id)
    if not listing or listing.get('is_deleted'):
        return jsonify({'error': 'Listing not found'}), 404

    if listing.get('seller_id') != session['user_id']:
        return jsonify({'error': 'Forbidden'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request body'}), 400

    _update_listing_in_db(listing_id, data)
    return jsonify({'message': 'Listing updated successfully.'})


@listings_bp.route('/api/listings/<int:listing_id>', methods=['DELETE'])
def api_delete_listing(listing_id):
    """Soft-delete a listing. Owner only."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    listing = get_listing_by_id(listing_id)
    if not listing or listing.get('is_deleted'):
        return jsonify({'error': 'Listing not found'}), 404

    if listing.get('seller_id') != session['user_id']:
        return jsonify({'error': 'Forbidden'}), 403

    from app.db import soft_delete_listing
    soft_delete_listing(listing_id)
    return jsonify({'message': 'Listing deleted.'})


# ── Page routes ───────────────────────────────────────────────────────────────

@listings_bp.route('/listings')
def browse():
    """Browse all non-deleted listings with search, filter and pagination."""
    if 'user_id' not in session:
        flash('Please log in to browse listings.', 'danger')
        return redirect(url_for('login'))

    all_listings = get_all_listings()
    search = request.args.get('search', '').strip().lower()
    category = request.args.get('category', '').strip()
    condition = request.args.get('condition', '').strip()

    filtered = _filter_listings(all_listings, search, category, condition)

    page = request.args.get('page', 1, type=int)
    total = len(filtered)
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    paginated = filtered[start:end]

    return render_template(
        'listings.html',
        listings=paginated,
        page=page,
        total_pages=(total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE,
        search=search,
        category=category,
        condition=condition,
        categories=CATEGORIES,
        conditions=CONDITIONS
    )


@listings_bp.route('/listing/<int:listing_id>/report', methods=['POST'])
def report_listing(listing_id):
    """US3 – Logged-in user reports a listing as inappropriate."""
    if 'user_id' not in session:
        flash('Please log in to report a listing.', 'danger')
        return redirect(url_for('login'))

    listing = get_listing_by_id(listing_id)
    if not listing or listing.get('is_deleted'):
        flash('Listing not found or has been removed.', 'danger')
        return redirect(url_for('listings.browse'))

    reason = request.form.get('reason', '').strip()
    description = request.form.get('description', '').strip()

    error = _validate_report(reason, description)
    if error:
        flash(error, 'danger')
        return redirect(url_for('listing_detail', listing_id=listing_id))

    create_report(
        listing_id=listing_id,
        reporter_id=session['user_id'],
        reason=reason,
        description=description
    )
    flash('Report submitted. Our team will review it shortly.', 'success')
    return redirect(url_for('listing_detail', listing_id=listing_id))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _validate_listing(data):
    """Validate listing data. Return error string or None."""
    required = ['title', 'description', 'price', 'category', 'condition']
    for field in required:
        if not data.get(field, '').strip():
            return f'{field} is required'

    price = data['price'].strip()
    if price not in ('Free', 'Swap Only'):
        try:
            val = float(price)
            if val < 0:
                return 'Price cannot be negative'
            if len(price.split('.')[-1]) > 2 if '.' in price else False:
                return 'Price can have at most 2 decimal places'
        except ValueError:
            return 'Price must be a number, "Free", or "Swap Only"'

    if data['condition'] not in CONDITIONS:
        return f'condition must be one of {CONDITIONS}'
    if data['category'] not in CATEGORIES:
        return f'category must be one of {CATEGORIES}'
    return None


def _validate_report(reason, description):
    """Validate report fields. Return error string or None."""
    if not reason:
        return 'Please select a reason for your report.'
    if reason not in REPORT_REASONS:
        return 'Invalid reason selected.'
    if not description:
        return 'Please provide a description for your report.'
    return None


def _filter_listings(listings, search, category, condition):
    """Filter listings by search, category and condition."""
    result = listings
    if search:
        result = [l for l in result if
                  search in l.get('title', '').lower() or
                  search in l.get('description', '').lower()]
    if category:
        result = [l for l in result if l.get('category') == category]
    if condition:
        result = [l for l in result if l.get('condition') == condition]
    return result


def _update_listing_in_db(listing_id, data):
    """Apply updates to a listing in the database."""
    from app.db import get_db_connection
    from datetime import datetime
    conn = get_db_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fields = []
    values = []
    allowed = {
        'title': 'title', 'description': 'description',
        'price': 'price', 'category': 'category',
        'condition': 'item_condition', 'imageUrl': 'image_url'
    }
    for key, col in allowed.items():
        if key in data:
            fields.append(f"{col} = ?")
            values.append(data[key])
    if fields:
        fields.append("last_modified_timestamp = ?")
        values.append(now)
        values.append(listing_id)
        conn.execute(
            f"UPDATE listings SET {', '.join(fields)} WHERE id = ?", values
        )
        conn.commit()
    conn.close()
