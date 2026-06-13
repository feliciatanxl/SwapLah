"""Routes for listing creation, retrieval, and update."""

import math
import re
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request, session

from app.db import create_listing, get_db_connection, get_listing_by_id, update_listing

listings_bp = Blueprint("listings", __name__)

_PRICE_RE = re.compile(r"^\d+(\.\d{1,2})?$")
_REQUIRED_FIELDS = ("title", "description", "price", "category", "condition")


def _error(message, status_code):
    """Return a JSON error response."""
    return jsonify({"error": message}), status_code


def is_valid_price(price):
    """Return True if price is a valid non-negative number, Free, or Swap Only."""
    price = str(price).strip()
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
    """Normalise a validated price string to a standard format."""
    price = str(price).strip()
    price_lower = price.lower()

    if price_lower == "free":
        return "Free"

    if price_lower == "swap only":
        return "Swap Only"

    return str(Decimal(price).quantize(Decimal("0.01")))


def _extract_fields(data):
    """Extract and strip listing fields from the request payload."""
    image_url = data.get("imageUrl") or data.get("image_url") or ""

    return {
        "title": data.get("title", "").strip(),
        "description": data.get("description", "").strip(),
        "price": str(data.get("price", "")).strip(),
        "category": data.get("category", "").strip(),
        "condition": data.get("condition", "").strip(),
        "image_url": image_url.strip(),
    }


def _has_missing_fields(fields):
    """Return True if any required listing field is missing."""
    return any(not fields[field] for field in _REQUIRED_FIELDS) or not fields["image_url"]


def _validate_listing_fields(fields):
    """Validate listing fields and return an error response if invalid."""
    if _has_missing_fields(fields):
        return _error("All fields are required.", 400)

    if not is_valid_price(fields["price"]):
        return _error("Price must be a number, Free, or Swap Only.", 400)

    return None


def _get_validated_fields():
    """Read and validate listing request body."""
    data = request.get_json(silent=True)

    if not data:
        return None, _error("Invalid request body.", 400)

    fields = _extract_fields(data)
    error_response = _validate_listing_fields(fields)

    if error_response:
        return None, error_response

    fields["price"] = normalise_price(fields["price"])
    return fields, None


def _listing_response(listing):
    """Format a listing row or dictionary for JSON response."""
    return {
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
    }


def _updated_listing_response(listing):
    """Format an updated listing for JSON response."""
    response = _listing_response(listing)
    response["status"] = listing["status"]
    return response


def _handle_update_error(error):
    """Return the correct response for listing update errors."""
    if error == "not_found":
        return _error("Listing not found or has already been deleted.", 404)

    if error == "forbidden":
        return _error("You are not allowed to edit this listing.", 403)

    return None


def _get_page_args():
    """Return sanitized pagination values from the request."""
    page = request.args.get("page", 1, type=int)
    per_page = 10
    page = max(page, 1)
    offset = (page - 1) * per_page
    return page, per_page, offset


def _count_active_listings(db):
    """Return the total number of active listings."""
    row = db.execute("SELECT COUNT(*) AS count FROM listings WHERE status = 'Active'").fetchone()
    return row["count"]


def _fetch_active_listing_rows(db, per_page, offset):
    """Return one page of active listings."""
    return db.execute(
        """
        SELECT id, seller_id, title, description, price, category,
               item_condition AS condition, image_url, listing_date,
               last_modified_timestamp, status
        FROM listings
        WHERE status = 'Active'
        ORDER BY listing_date DESC
        LIMIT ? OFFSET ?
        """,
        (per_page, offset),
    ).fetchall()


def _active_listing_json(row):
    """Convert one active listing row into API JSON format."""
    return {
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
        "status": row["status"],
    }


def _listing_page_payload(rows, page, per_page, total_listings):
    """Build the paginated listings API response payload."""
    total_pages = math.ceil(total_listings / per_page) if total_listings > 0 else 1
    return {
        "listings": [_active_listing_json(row) for row in rows],
        "page": page,
        "perPage": per_page,
        "totalListings": total_listings,
        "totalPages": total_pages,
    }


@listings_bp.route("/api/listings", methods=["GET"])
def api_get_active_listings():
    """Return active listings with pagination."""
    page, per_page, offset = _get_page_args()
    db = get_db_connection()
    total_listings = _count_active_listings(db)
    rows = _fetch_active_listing_rows(db, per_page, offset)
    db.close()
    return jsonify(_listing_page_payload(rows, page, per_page, total_listings)), 200


@listings_bp.route("/api/listings", methods=["POST"])
def api_create_listing():
    """Create a new listing for the logged-in seller."""
    seller_id = session.get("user_id")

    if not seller_id:
        return _error("You must be logged in to create a listing.", 401)

    fields, error_response = _get_validated_fields()

    if error_response:
        return error_response

    listing = create_listing(
        seller_id=seller_id,
        title=fields["title"],
        description=fields["description"],
        price=fields["price"],
        category=fields["category"],
        condition=fields["condition"],
        image_url=fields["image_url"],
    )

    return jsonify(
        {
            "message": "Listing created successfully.",
            "listing": _listing_response(listing),
        }
    ), 201


@listings_bp.route("/api/listings/<int:listing_id>", methods=["PUT"])
def api_update_listing(listing_id):
    """Update an existing listing if the logged-in user is the owner."""
    seller_id = session.get("user_id")

    if not seller_id:
        return _error("You must be logged in to edit a listing.", 401)

    fields, error_response = _get_validated_fields()

    if error_response:
        return error_response

    updated_listing, error = update_listing(
        listing_id=listing_id,
        seller_id=seller_id,
        title=fields["title"],
        description=fields["description"],
        price=fields["price"],
        category=fields["category"],
        condition=fields["condition"],
        image_url=fields["image_url"],
    )

    update_error = _handle_update_error(error)

    if update_error:
        return update_error

    return jsonify(
        {
            "message": "Listing updated successfully.",
            "listing": _updated_listing_response(updated_listing),
        }
    ), 200


@listings_bp.route("/api/listings/<int:listing_id>", methods=["GET"])
def api_get_listing_detail(listing_id):
    """Return full detail for a single listing by ID."""
    listing = get_listing_by_id(listing_id)

    if listing is None:
        return _error("Listing not found or unavailable.", 404)

    return jsonify(
        {
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
        }
    ), 200