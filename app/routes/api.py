"""REST API endpoints for SwapLah."""
from flask import Blueprint, jsonify, request, session
from flask_login import login_required, current_user
from ..models import db, Listing, User, Offer, Review, Transaction

api_bp = Blueprint('api', __name__)


@api_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})


@api_bp.route('/listings', methods=['GET'])
def get_listings():
    """Return all active listings. Supports ?category= and ?search= params."""
    query = Listing.query.filter_by(is_deleted=False)

    category = request.args.get('category', '').strip()
    if category:
        query = query.filter_by(category=category)

    search = request.args.get('search', '').strip()
    if search:
        like = f'%{search}%'
        query = query.filter(
            db.or_(
                Listing.title.ilike(like),
                Listing.description.ilike(like)
            )
        )

    listings = query.order_by(Listing.listing_date.desc()).all()
    return jsonify([l.to_dict() for l in listings])


@api_bp.route('/listings/<string:listing_id>', methods=['GET'])
def get_listing(listing_id):
    """Return a single listing by ID."""
    listing = Listing.query.get(listing_id)
    if not listing or listing.is_deleted:
        return jsonify({'error': 'Listing not found'}), 404
    return jsonify(listing.to_dict())


@api_bp.route('/listings', methods=['POST'])
@login_required
def create_listing():
    """Create a new listing."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    error = _validate_listing_data(data)
    if error:
        return jsonify({'error': error}), 400

    listing = Listing(
        seller_id=current_user.id,
        title=data['title'].strip(),
        description=data['description'].strip(),
        price=data['price'].strip(),
        category=data['category'],
        condition=data['condition'],
        image_url=data.get('image_url', '').strip() or None
    )
    db.session.add(listing)
    db.session.commit()
    return jsonify(listing.to_dict()), 201


@api_bp.route('/listings/<string:listing_id>', methods=['PUT'])
@login_required
def update_listing(listing_id):
    """Update a listing. Only the owner may update."""
    listing = Listing.query.get(listing_id)
    if not listing or listing.is_deleted:
        return jsonify({'error': 'Listing not found'}), 404

    if listing.seller_id != current_user.id:
        return jsonify({'error': 'Forbidden'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    _apply_listing_updates(listing, data)
    db.session.commit()
    return jsonify(listing.to_dict())


def _apply_listing_updates(listing, data):
    """Apply allowed field updates to a listing."""
    from datetime import datetime
    allowed = ['title', 'description', 'price', 'category', 'condition', 'image_url']
    for field in allowed:
        if field in data:
            setattr(listing, field, data[field])
    listing.updated_at = datetime.utcnow()


@api_bp.route('/listings/<string:listing_id>', methods=['DELETE'])
@login_required
def delete_listing(listing_id):
    """Soft-delete a listing. Only the owner may delete."""
    listing = Listing.query.get(listing_id)
    if not listing or listing.is_deleted:
        return jsonify({'error': 'Listing not found'}), 404

    if listing.seller_id != current_user.id:
        return jsonify({'error': 'Forbidden'}), 403

    listing.is_deleted = True
    db.session.commit()
    return jsonify({'message': 'Listing deleted'})


@api_bp.route('/users/<string:user_id>/reviews', methods=['GET'])
def get_user_reviews(user_id):
    """Return all reviews for a user."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    reviews = Review.query.filter_by(reviewee_id=user_id).all()
    return jsonify([r.to_dict() for r in reviews])


@api_bp.route('/offers', methods=['POST'])
@login_required
def submit_offer():
    """Submit an offer on a listing."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    error = _validate_offer(data)
    if error:
        return jsonify({'error': error}), 400

    offer = Offer(
        listing_id=data['listing_id'],
        buyer_id=current_user.id,
        offer_type=data['offer_type'],
        proposed_price=data.get('proposed_price'),
        swap_listing_id=data.get('swap_listing_id')
    )
    db.session.add(offer)
    db.session.commit()
    return jsonify(offer.to_dict()), 201


def _validate_listing_data(data):
    """Validate listing creation data. Return error string or None."""
    required = ['title', 'description', 'price', 'category', 'condition']
    for field in required:
        if not data.get(field, '').strip():
            return f'{field} is required'

    if data['condition'] not in Listing.CONDITIONS:
        return f'condition must be one of {Listing.CONDITIONS}'

    if data['category'] not in Listing.CATEGORIES:
        return f'category must be one of {Listing.CATEGORIES}'

    return None


def _validate_offer(data):
    """Validate offer submission data. Return error string or None."""
    if not data.get('listing_id'):
        return 'listing_id is required'

    listing = Listing.query.get(data['listing_id'])
    if not listing or listing.is_deleted:
        return 'Listing not found'

    if listing.seller_id == current_user.id:
        return 'You cannot make an offer on your own listing'

    offer_type = data.get('offer_type')
    if offer_type not in ['price', 'swap']:
        return 'offer_type must be price or swap'

    if offer_type == 'price' and not data.get('proposed_price'):
        return 'proposed_price is required for price offers'

    if offer_type == 'swap':
        swap_id = data.get('swap_listing_id')
        if not swap_id:
            return 'swap_listing_id is required for swap offers'
        swap_listing = Listing.query.get(swap_id)
        if not swap_listing or swap_listing.seller_id != current_user.id:
            return 'Swap item must be one of your own active listings'

    return None
