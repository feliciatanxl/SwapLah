from flask import Blueprint, request, jsonify, session
from app.db import create_listing, get_listing_by_id, get_db_connection, update_listing
import math
import re
from decimal import Decimal, InvalidOperation
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

@listings_bp.route("/api/listings", methods=["POST"])
def api_create_listing():
    # AC5: user must be logged in
    seller_id = session.get("user_id")

    if not seller_id:
        return jsonify({
            "error": "You must be logged in to create a listing."
        }), 401

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Invalid request body."
        }), 400

    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    price = str(data.get("price", "")).strip()
    category = data.get("category", "").strip()
    condition = data.get("condition", "").strip()
    image_url = data.get("imageUrl") or data.get("image_url") or ""
    image_url = image_url.strip()

    # AC4: required fields validation
    if not title or not description or not price or not category or not condition or not image_url:
        return jsonify({
            "error": "All fields are required."
        }), 400

    # AC2: price validation
    if not is_valid_price(price):
        return jsonify({
            "error": "Price must be a number, Free, or Swap Only."
        }), 400

    price = normalise_price(price)

    # AC1 + AC3 + AC6: create listing in database
    listing = create_listing(
        seller_id=seller_id,
        title=title,
        description=description,
        price=price,
        category=category,
        condition=condition,
        image_url=image_url
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
            "lastModifiedTimestamp": listing["last_modified_timestamp"]
        }
    }), 201

@listings_bp.route("/api/listings/<int:listing_id>", methods=["PUT"])
def api_update_listing(listing_id):
    seller_id = session.get("user_id")

    if not seller_id:
        return jsonify({
            "error": "You must be logged in to edit a listing."
        }), 401

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Invalid request body."
        }), 400

    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    price = str(data.get("price", "")).strip()
    category = data.get("category", "").strip()
    condition = data.get("condition", "").strip()
    image_url = data.get("imageUrl") or data.get("image_url") or ""
    image_url = image_url.strip()

    if not title or not description or not price or not category or not condition or not image_url:
        return jsonify({
            "error": "All fields are required."
        }), 400

    if not is_valid_price(price):
        return jsonify({
            "error": "Price must be a number, Free, or Swap Only."
        }), 400

    price = normalise_price(price)

    updated_listing, error = update_listing(
        listing_id=listing_id,
        seller_id=seller_id,
        title=title,
        description=description,
        price=price,
        category=category,
        condition=condition,
        image_url=image_url
    )

    if error == "not_found":
        return jsonify({
            "error": "Listing not found or has already been deleted."
        }), 404

    if error == "forbidden":
        return jsonify({
            "error": "You are not allowed to edit this listing."
        }), 403

    return jsonify({
        "message": "Listing updated successfully.",
        "listing": {
            "id": updated_listing["id"],
            "sellerId": updated_listing["seller_id"],
            "title": updated_listing["title"],
            "description": updated_listing["description"],
            "price": updated_listing["price"],
            "category": updated_listing["category"],
            "condition": updated_listing["item_condition"],
            "imageUrl": updated_listing["image_url"],
            "listingDate": updated_listing["listing_date"],
            "lastModifiedTimestamp": updated_listing["last_modified_timestamp"],
            "status": updated_listing["status"]
        }
    }), 200

def is_valid_price(price):
    price_lower = price.lower()

    if price_lower == "free" or price_lower == "swap only":
        return True

    # Only allow whole numbers or max 2 decimal places
    if not re.fullmatch(r"\d+(\.\d{1,2})?", price):
        return False

    try:
        numeric_price = Decimal(price)
        return numeric_price >= 0
    except InvalidOperation:
        return False


def normalise_price(price):
    price_lower = price.lower()

    if price_lower == "free":
        return "Free"

    if price_lower == "swap only":
        return "Swap Only"

    return str(Decimal(price).quantize(Decimal("0.01")))


## feature/view-listing-details
@listings_bp.route("/api/listings/<int:listing_id>", methods=["GET"])
def api_get_listing_detail(listing_id):
    listing = get_listing_by_id(listing_id)

    if listing is None:
        return jsonify({
            "error": "Listing not found or unavailable."
        }), 404

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
                "contactNumber": listing["seller_contact_number"]
            }
        }
    }), 200




