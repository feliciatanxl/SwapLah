"""Routes for creating and managing cash and swap offers."""
from flask import Blueprint, jsonify, request, session

from app.db import (
    accept_offer,
    create_offer,
    get_active_listing_by_buyer,
    get_listing_owner,
    get_offer_by_id,
    get_offers_for_seller,
    get_transactions_for_user,
    reject_offer,
)

offers_bp = Blueprint("offers", __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _common_error(data):
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


def _format_received_offer(offer):
    return {
        "id": offer["id"],
        "listingId": offer["listing_id"],
        "buyerId": offer["buyer_id"],
        "offerType": offer["offer_type"],
        "proposedPrice": offer["proposed_price"],
        "swapListingId": offer["swap_listing_id"],
        "status": offer["status"],
        "createdAt": offer["created_at"],
        "listingTitle": offer["listing_title"],
        "listingCategory": offer["listing_category"],
        "listingPrice": offer["listing_price"],
        "buyerDisplayName": offer["buyer_display_name"],
        "swapListingTitle": offer["swap_listing_title"],
    }


# ---------------------------------------------------------------------------
# Routes — submit offer
# ---------------------------------------------------------------------------

@offers_bp.route("/api/offers", methods=["GET", "POST"])
def api_create_offer():
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
    swap_listing_id = data.get("swapListingId")
    if not swap_listing_id:
        return jsonify({"error": "swapListingId is required for a swap offer."}), 400
    if not get_active_listing_by_buyer(swap_listing_id, buyer_id):
        return jsonify({
            "error": "The selected swap item was not found in your active listings."
        }), 403
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


# ---------------------------------------------------------------------------
# Routes — manage received offers
# ---------------------------------------------------------------------------

@offers_bp.route("/api/offers/received", methods=["GET"])
def api_get_received_offers():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "You must be logged in to view offers."}), 401
    offers = get_offers_for_seller(user_id)
    return jsonify({"offers": [_format_received_offer(o) for o in offers]}), 200


@offers_bp.route("/api/offers/<int:offer_id>/accept", methods=["PATCH"])
def api_accept_offer(offer_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "You must be logged in."}), 401
    offer = get_offer_by_id(offer_id)
    if offer is None:
        return jsonify({"error": "Offer not found."}), 404
    if get_listing_owner(offer["listing_id"]) != user_id:
        return jsonify({"error": "You do not own this listing."}), 403
    if offer["status"] != "Pending":
        return jsonify({"error": f"Offer is already {offer['status']}."}), 409
    updated = accept_offer(offer_id)
    return jsonify({
        "message": "Offer accepted. All other pending offers for this listing have been rejected.",
        "offer": _format_offer(updated),
    }), 200


@offers_bp.route("/api/offers/<int:offer_id>/reject", methods=["PATCH"])
def api_reject_offer(offer_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "You must be logged in."}), 401
    offer = get_offer_by_id(offer_id)
    if offer is None:
        return jsonify({"error": "Offer not found."}), 404
    if get_listing_owner(offer["listing_id"]) != user_id:
        return jsonify({"error": "You do not own this listing."}), 403
    if offer["status"] != "Pending":
        return jsonify({"error": f"Offer is already {offer['status']}."}), 409
    updated = reject_offer(offer_id)
    return jsonify({
        "message": "Offer rejected.",
        "offer": _format_offer(updated),
    }), 200


# ---------------------------------------------------------------------------
# Routes — transaction history
# ---------------------------------------------------------------------------

@offers_bp.route("/api/transactions", methods=["GET"])
def api_get_transactions():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "You must be logged in to view transactions."}), 401
    transactions = get_transactions_for_user(user_id)
    return jsonify({"transactions": transactions}), 200