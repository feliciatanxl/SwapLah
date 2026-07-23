"""Routes for creating cash and swap offers (POST /api/offers)."""
from flask import Blueprint, jsonify, request, session

from app.db import (
    create_offer,
    get_active_listing_by_buyer,
    get_listing_owner,
)

offers_bp = Blueprint("offers", __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _common_error(data):
    """
    Validate fields shared by both offer types.

    Returns (error_body_dict, http_status) on failure, or None when valid.
    """
    if not session.get("user_id"):
        return {"error": "You must be logged in to submit an offer."}, 401
    if not data or not data.get("listingId"):
        return {"error": "listingId is required or request body is missing."}, 400
    if data.get("offerType", "").strip().lower() not in ("cash", "swap"):
        return {"error": "offerType must be 'cash' or 'swap'."}, 400

    seller_id = get_listing_owner(data["listingId"])
    if seller_id is None:
        return {"error": "Listing not found."}, 404
    if seller_id == session.get("user_id"):
        return {"error": "You cannot submit an offer on your own listing."}, 403
    return None


def _validate_cash_price(raw_price):
    """
    Validate and convert a proposed cash price.

    Returns (float_price, None) on success or (None, (error_dict, status)) on failure.
    """
    if raw_price is None or str(raw_price).strip() == "":
        return None, ({"error": "proposedPrice is required for a cash offer."}, 400)
    try:
        price = float(raw_price)
        if price < 0:
            raise ValueError("negative price")
    except (ValueError, TypeError):
        return None, ({"error": "proposedPrice must be a non-negative number."}, 400)
    return price, None


def _format_offer(offer):
    """Serialise an offer row dict to a JSON-safe dict."""
    return {
        "id": offer["id"],
        "listingId": offer["listing_id"],
        "buyerId": offer["buyer_id"],
        "offerType": offer["offer_type"],
        "proposedPrice": offer["proposed_price"],
        "swapListingId": offer["swap_listing_id"],
        "status": offer["status"],
        "createdAt": offer["created_at"],
    }


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@offers_bp.route("/api/offers", methods=["GET", "POST"])
def api_create_offer():
    """
    Create a cash or swap offer for a listing.

    Accepts JSON:
      listingId      (int)    required
      offerType      (str)    'cash' or 'swap'
      proposedPrice  (float)  required for cash offers
      swapListingId  (int)    required for swap offers

    Returns 201 with the created offer on success.
    """
    if request.method == "GET":
        return jsonify({"error": "This endpoint only accepts POST requests."}), 405

    data = request.get_json(silent=True)
    err = _common_error(data)
    if err:
        return jsonify(err[0]), err[1]

    buyer_id = session.get("user_id")
    listing_id = data["listingId"]
    offer_type = data.get("offerType", "").strip().lower()

    if offer_type == "cash":
        return _handle_cash_offer(data, listing_id, buyer_id)
    return _handle_swap_offer(data, listing_id, buyer_id)


def _handle_cash_offer(data, listing_id, buyer_id):
    """Process and persist a validated cash offer."""
    price, err = _validate_cash_price(data.get("proposedPrice"))
    if err:
        return jsonify(err[0]), err[1]

    offer = create_offer(
        listing_id=listing_id,
        buyer_id=buyer_id,
        offer_type="cash",
        proposed_price=price,
    )
    return jsonify({
        "message": "Cash offer submitted successfully.",
        "offer": _format_offer(offer),
    }), 201


def _handle_swap_offer(data, listing_id, buyer_id):
    """Process and persist a validated swap offer."""
    swap_listing_id = data.get("swapListingId")
    if not swap_listing_id:
        return jsonify({"error": "swapListingId is required for a swap offer."}), 400

    # FIX: buyer must own the swap listing (active and belonging to buyer)
    if not db_module.get_active_listing_by_seller(swap_listing_id, buyer_id):

    if not get_active_listing_by_buyer(swap_listing_id, buyer_id):
        return jsonify({
            "error": "The selected swap item was not found in your active listings."
        }), 403

    # Prevent swapping with the same listing
    if swap_listing_id == listing_id:
        return jsonify({"error": "Cannot swap with the same listing."}), 400

    offer = db_module.create_offer(

    offer = create_offer(
        listing_id=listing_id,
        buyer_id=buyer_id,
        offer_type="swap",
        swap_listing_id=swap_listing_id,
    )
    return jsonify({
        "message": "Swap offer submitted successfully.",
        "offer": _format_offer(offer),
    }), 201