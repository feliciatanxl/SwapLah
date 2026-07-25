"""Routes for creating and managing marketplace offers."""
from flask import Blueprint, jsonify, request, session

import app.db as db_module
from app.timezones import to_singapore_iso

offers_bp = Blueprint("offers", __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _common_error(data):
    """Validate fields shared by both offer types."""
    if not session.get("user_id"):
        return {"error": "You must be logged in to submit an offer."}, 401

    if not data or not data.get("listingId"):
        return {"error": "listingId is required or request body is missing."}, 400

    offer_type = data.get("offerType", "").strip().lower()
    if offer_type not in ("cash", "swap"):
        return {"error": "offerType must be 'cash' or 'swap'."}, 400

    seller_id = db_module.get_listing_owner(data["listingId"])
    if seller_id is None:
        return {"error": "Listing not found."}, 404

    if seller_id == session.get("user_id"):
        return {"error": "You cannot submit an offer on your own listing."}, 403

    return None


def _validate_cash_price(raw_price):
    """Validate and convert a proposed cash price."""
    if raw_price is None or str(raw_price).strip() == "":
        return None, ({"error": "proposedPrice is required for a cash offer."}, 400)

    try:
        price = float(raw_price)
        if price < 0:
            raise ValueError
    except (ValueError, TypeError):
        return None, ({"error": "proposedPrice must be a non-negative number."}, 400)

    return price, None


def _format_offer(offer):
    """Serialise an offer row dict to JSON."""
    return {
        "id": offer["id"],
        "listingId": offer["listing_id"],
        "buyerId": offer["buyer_id"],
        "offerType": offer["offer_type"],
        "proposedPrice": offer["proposed_price"],
        "swapListingId": offer["swap_listing_id"],
        "status": offer["status"],
        "createdAt": to_singapore_iso(offer["created_at"]),
    }


def _format_received_offer(offer):
    """Serialise a received offer row to JSON for seller dashboards."""
    return {
        **_format_offer(offer),
        "listingTitle": offer["listing_title"],
        "listingCategory": offer["listing_category"],
        "listingPrice": offer["listing_price"],
        "sellerId": offer["seller_id"],
        "buyerDisplayName": offer["buyer_display_name"],
        "sellerDisplayName": offer.get("seller_display_name"),
        "swapListingTitle": offer["swap_listing_title"],
    }


def _require_login():
    """Return an auth error tuple when the current request is logged out."""
    if not session.get("user_id"):
        return jsonify({"error": "You must be logged in."}), 401
    return None


def _is_active_admin(user_id):
    """Return True when the current user is an active admin in the database."""
    if session.get("role") != "admin":
        return False

    user = db_module.get_user_by_id(user_id)
    return user is not None and user["role"] == "admin" and user["status"] == "Active"


def _get_owned_pending_offer_or_response(offer_id):
    """Return offer if the logged-in user owns its listing and it is pending."""
    login_error = _require_login()
    if login_error:
        return None, login_error

    offer = db_module.get_offer_by_id(offer_id)
    if offer is None:
        return None, (jsonify({"error": "Offer not found."}), 404)

    owner_id = db_module.get_listing_owner(offer["listing_id"])
    if owner_id != session["user_id"]:
        return None, (jsonify({"error": "You can only manage offers on your own listings."}), 403)

    if offer["status"] != "Pending":
        return None, (jsonify({"error": "Only pending offers can be updated."}), 409)

    return offer, None


def _cash_offer_payload(data, base_offer_data):
    """Return create_offer payload and message for a cash offer."""
    price, err = _validate_cash_price(data.get("proposedPrice"))
    if err:
        return None, None, (jsonify(err[0]), err[1])

    return {
        **base_offer_data,
        "proposed_price": price,
    }, "Cash offer submitted successfully.", None


def _swap_offer_payload(data, base_offer_data, buyer_id):
    """Return create_offer payload and message for a swap offer."""
    swap_listing_id = data.get("swapListingId")
    if not swap_listing_id:
        return None, None, (jsonify({
            "error": "swapListingId is required for a swap offer."
        }), 400)

    if not db_module.get_active_listing_by_buyer(swap_listing_id, buyer_id):
        return None, None, (jsonify({
            "error": "The selected swap item was not found in your active listings."
        }), 403)

    return {
        **base_offer_data,
        "swap_listing_id": swap_listing_id,
    }, "Swap offer submitted successfully.", None


def _offer_payload(data, buyer_id):
    """Return create_offer payload, success message, and optional error."""
    base_offer_data = {
        "listing_id": data["listingId"],
        "buyer_id": buyer_id,
        "offer_type": data["offerType"].strip().lower(),
    }

    if base_offer_data["offer_type"] == "cash":
        return _cash_offer_payload(data, base_offer_data)

    return _swap_offer_payload(data, base_offer_data, buyer_id)


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@offers_bp.route("/api/offers", methods=["GET", "POST"])
def api_create_offer():
    """Create a cash or swap offer."""
    if request.method == "GET":
        return jsonify({"error": "This endpoint only accepts POST requests."}), 405

    data = request.get_json(silent=True)

    err = _common_error(data)
    if err:
        return jsonify(err[0]), err[1]

    offer_data, success_msg, error_response = _offer_payload(data, session["user_id"])
    if error_response:
        return error_response

    offer = db_module.create_offer(**offer_data)

    return jsonify({
        "message": success_msg,
        "offer": _format_offer(offer),
    }), 201


@offers_bp.route("/api/offers/received", methods=["GET"])
def api_received_offers():
    """Return received offers, or all offers for active admins."""
    login_error = _require_login()
    if login_error:
        return login_error

    if _is_active_admin(session["user_id"]):
        offers = db_module.get_all_offers()
    else:
        offers = db_module.get_offers_for_seller(session["user_id"])

    return jsonify({"offers": [_format_received_offer(offer) for offer in offers]}), 200


@offers_bp.route("/api/offers/<int:offer_id>/accept", methods=["PATCH"])
def api_accept_offer(offer_id):
    """Accept a pending offer for a listing owned by the logged-in user."""
    _offer, error_response = _get_owned_pending_offer_or_response(offer_id)
    if error_response:
        return error_response

    updated = db_module.accept_offer(offer_id)
    return jsonify({
        "message": "Offer accepted successfully.",
        "offer": _format_offer(updated),
    }), 200


@offers_bp.route("/api/offers/<int:offer_id>/reject", methods=["PATCH"])
def api_reject_offer(offer_id):
    """Reject a pending offer for a listing owned by the logged-in user."""
    _offer, error_response = _get_owned_pending_offer_or_response(offer_id)
    if error_response:
        return error_response

    updated = db_module.reject_offer(offer_id)
    return jsonify({
        "message": "Offer rejected successfully.",
        "offer": _format_offer(updated),
    }), 200
