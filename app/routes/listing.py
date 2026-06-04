from flask import Blueprint, request, jsonify, session
from app.db import create_listing
import re
from decimal import Decimal, InvalidOperation
listings_bp = Blueprint("listings", __name__)


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