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
    """Serialise an offer row dict to a JSON-safe dict."""
    formatted = {
        "id": offer["id"],
        "listingId": offer["listing_id"],
        "buyerId": offer["buyer_id"],
        "offerType": offer["offer_type"],
        "proposedPrice": offer["proposed_price"],
        "swapListingId": offer["swap_listing_id"],
        "status": offer["status"],
        "createdAt": offer["created_at"],
    }

    if "listing_title" in offer:
        formatted["listingTitle"] = offer["listing_title"]
        formatted["listingCategory"] = offer["listing_category"]
        formatted["listingPrice"] = offer["listing_price"]
        formatted["buyerDisplayName"] = offer["buyer_display_name"]
        formatted["swapListingTitle"] = offer.get("swap_listing_title")

    return formatted


def _format_transaction(transaction):
    """Serialise a transaction row dict to a JSON-safe dict."""
    return {
        "id": transaction["id"],
        "listingTitle": transaction["listing_title"],
        "listingCategory": transaction["listing_category"],
        "counterpartyDisplayName": transaction["counterparty_display_name"],
        "transactionType": transaction["transaction_type"],
        "amount": transaction["amount"],
        "createdAt": transaction["created_at"],
    }


def _check_offer_access(offer_id):
    """
    Shared validation for accept/reject: auth, existence, ownership, status.

    Returns a Flask (body, status) response tuple on failure, or None
    when the caller may proceed.
    """
    if not session.get("user_id"):
        return jsonify({"error": "You must be logged in to manage offers."}), 401

    offer = get_offer_by_id(offer_id)
    if offer is None:
        return jsonify({"error": "Offer not found."}), 404

    seller_id = get_listing_owner(offer["listing_id"])
    if seller_id != session.get("user_id"):
        return jsonify({"error": "You do not have permission to manage this offer."}), 403

    if offer["status"] != "Pending":
        return jsonify({"error": f"Offer has already been {offer['status'].lower()}."}), 409

    return None


# ---------------------------------------------------------------------------
# Routes — submit offer
# ---------------------------------------------------------------------------

@offers_bp.route("/api/offers", methods=["GET", "POST"])
def api_create_offer():
    """
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
# GET /api/offers/received  —  seller views pending offers on their listings
# ---------------------------------------------------------------------------

@offers_bp.route("/api/offers/received", methods=["GET"])
def api_get_received_offers():
    """Return all offers received on listings owned by the logged-in seller."""
    if not session.get("user_id"):
        return jsonify({"error": "You must be logged in to view your offers."}), 401

    seller_id = session["user_id"]
    offers = get_offers_for_seller(seller_id)
    return jsonify({"offers": [_format_offer(offer) for offer in offers]}), 200


# ---------------------------------------------------------------------------
# PATCH /api/offers/<id>/accept  —  seller accepts an offer
# ---------------------------------------------------------------------------

@offers_bp.route("/api/offers/<int:offer_id>/accept", methods=["PATCH"])
def api_accept_offer(offer_id):
    """Accept a pending offer owned by the logged-in seller."""
    error = _check_offer_access(offer_id)
    if error:
        return error

    updated = accept_offer(offer_id)
    return jsonify({
        "message": "Offer accepted successfully.",
        "offer": _format_offer(updated),
    }), 200


# ---------------------------------------------------------------------------
# PATCH /api/offers/<id>/reject  —  seller rejects an offer
# ---------------------------------------------------------------------------

@offers_bp.route("/api/offers/<int:offer_id>/reject", methods=["PATCH"])
def api_reject_offer(offer_id):
    """Reject a pending offer owned by the logged-in seller."""
    error = _check_offer_access(offer_id)
    if error:
        return error

    updated = reject_offer(offer_id)
    return jsonify({
        "message": "Offer rejected successfully.",
        "offer": _format_offer(updated),
    }), 200


# ---------------------------------------------------------------------------
# GET /api/transactions  —  view completed transaction history
# ---------------------------------------------------------------------------

@offers_bp.route("/api/transactions", methods=["GET"])
def api_get_transactions():
    """
    Return the logged-in user's completed transactions.

    Query string `role` selects buyer or seller history (defaults to buyer).
    """
    if not session.get("user_id"):
        return jsonify({"error": "You must be logged in to view your transaction history."}), 401

    role = request.args.get("role", "buyer").lower()
    if role not in ("buyer", "seller"):
        return jsonify({"error": "role must be 'buyer' or 'seller'."}), 400

    user_id = session["user_id"]
    transactions = get_transactions_for_user(user_id, role)

    return jsonify({
        "role": role,
        "transactions": [_format_transaction(t) for t in transactions],
    }), 200