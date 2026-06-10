from flask import Blueprint, request, jsonify, session
from app.db import create_listing, get_listing_by_id, get_db_connection
import math
"""Routes for listing creation and retrieval."""
import re
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request, session

from app.db import create_listing, get_listing_by_id

listings_bp = Blueprint("listings", __name__)


@listings_bp.route("/api/listings", methods=["GET"])
def api_get_active_listings():
    db = get_db_connection()

    page = request.args.get("page", 1, type=int)
    per_page = 10

    if page < 1:
        page = 1

    offset = (page - 1) * per_page

    total_listings = db.execute("""
        SELECT COUNT(*) AS count
        FROM listings
        WHERE status = 'Active'
    """).fetchone()["count"]

    rows = db.execute("""
        SELECT 
            id,
            seller_id,
            title,
            description,
            price,
            category,
            item_condition AS condition,
            image_url,
            listing_date,
            last_modified_timestamp,
            status
        FROM listings
        WHERE status = 'Active'
        ORDER BY listing_date DESC
        LIMIT ? OFFSET ?
    """, (per_page, offset)).fetchall()

    listings = []

    for row in rows:
        listings.append({
            "id": row["id"],
            "sellerId": row["seller_id"],
            "title": row["title"],
            "description": row["description"],
            "price": row["price"],
            "category": row["category"],
            "condition": row["condition"],
            "imageUrl": row["image_url"],
            "listingDate": row["listing_date"],
            "lastModifiedTimestamp": row["last_modified_timestamp"],
            "status": row["status"]
        })

    total_pages = math.ceil(total_listings / per_page) if total_listings > 0 else 1

    db.close()
    return jsonify({
        "listings": listings,
        "page": page,
        "perPage": per_page,
        "totalListings": total_listings,
        "totalPages": total_pages
    }), 200
_PRICE_RE = re.compile(r"^\d+(\.\d{1,2})?$")
_REQUIRED_FIELDS = ("title", "description", "price", "category", "condition")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_valid_price(price):
    """Return True if price is a valid non-negative number, 'Free', or 'Swap Only'."""
    price_lower = price.lower()

    if price_lower in ("free", "swap only"):
        return True

    if not _PRICE_RE.fullmatch(price):
        return False

    try:
        return Decimal(price) >= 0
    except InvalidOperation:
        return False


def normalise_price(price):
    """Normalise a validated price string to a canonical form."""
    price_lower = price.lower()

    if price_lower == "free":
        return "Free"

    if price_lower == "swap only":
        return "Swap Only"

    return str(Decimal(price).quantize(Decimal("0.01")))


def _extract_fields(data):
    """Extract and strip all listing fields from the request payload."""
    image_url = (data.get("imageUrl") or data.get("image_url") or "").strip()
    return {
        "title": data.get("title", "").strip(),
        "description": data.get("description", "").strip(),
        "price": str(data.get("price", "")).strip(),
        "category": data.get("category", "").strip(),
        "condition": data.get("condition", "").strip(),
        "image_url": image_url,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@listings_bp.route("/api/listings", methods=["POST"])
def api_create_listing():
    """
    Create a new listing for the logged-in seller.

    Accepts JSON with: title, description, price, category, condition, imageUrl.
    Returns 201 with the created listing on success.
    """
    seller_id = session.get("user_id")
    if not seller_id:
        return jsonify({"error": "You must be logged in to create a listing."}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid request body."}), 400

    fields = _extract_fields(data)

    missing = any(not fields[f] for f in _REQUIRED_FIELDS) or not fields["image_url"]
    if missing:
        return jsonify({"error": "All fields are required."}), 400

    if not is_valid_price(fields["price"]):
        return jsonify({"error": "Price must be a number, Free, or Swap Only."}), 400

    fields["price"] = normalise_price(fields["price"])

    listing = create_listing(
        seller_id=seller_id,
        title=fields["title"],
        description=fields["description"],
        price=fields["price"],
        category=fields["category"],
        condition=fields["condition"],
        image_url=fields["image_url"],
    )

    return jsonify({
        "message": "Listing created successfully.",
        "listing": {
            "id": listing["id"],
            "sellerId": listing["seller_id"],
            "title": listing["title"],
            "description": listing["description"],
            "price": listing["price"],
            "category": listing["category"],
            "condition": listing["item_condition"],
            "imageUrl": listing["image_url"],
            "listingDate": listing["listing_date"],
            "lastModifiedTimestamp": listing["last_modified_timestamp"],
        },
    }), 201


## feature/view-listing-details
@listings_bp.route("/api/listings/<int:listing_id>", methods=["GET"])
def api_get_listing_detail(listing_id):
    """Return full detail for a single listing by ID."""
    listing = get_listing_by_id(listing_id)

    if listing is None:
        return jsonify({"error": "Listing not found or unavailable."}), 404

    return jsonify({
        "listing": {
            "id": listing["id"],
            "title": listing["title"],
            "description": listing["description"],
            "price": listing["price"],
            "category": listing["category"],
            "condition": listing["condition"],
            "imageUrl": listing["image_url"],
            "images": listing.get("images", []),
            "listingDate": listing["listing_date"],
            "lastModifiedTimestamp": listing["last_modified_timestamp"],
            "seller": {
                "displayName": listing["seller_display_name"],
                "email": listing["seller_email"],
                "contactNumber": listing["seller_contact_number"],
            },
        }
    }), 200




