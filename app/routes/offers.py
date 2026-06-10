"""Routes for creating, viewing, and managing offers."""
from flask import Blueprint, jsonify, request, session

import app.db as db_module

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

    seller_id = db_module.get_listing_owner(data["listingId"])
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
# POST /api/offers  —  submit an offer (existing)
# ---------------------------------------------------------------------------

@offers_bp.route("/api/offers", methods=["POST"])
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

    offer = db_module.create_offer(
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

    if not db_module.get_active_listing_by_buyer(swap_listing_id, buyer_id):
        return jsonify({
            "error": "The selected swap item was not found in your active listings."
        }), 403

    offer = db_module.create_offer(
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
# GET /api/offers/received  —  view pending offers as a seller
# ---------------------------------------------------------------------------

@offers_bp.route("/api/offers/received", methods=["GET"])
def api_get_received_offers():
    """
    Return all offers received on the logged-in seller's listings.

    Returns 200 with a list of offer objects grouped by listing.
    AC1, AC2, AC3 — view received offers user story.
    """
    if not session.get("user_id"):
        return jsonify({"error": "You must be logged in to view offers."}), 401

    seller_id = session["user_id"]
    offers = db_module.get_offers_for_seller(seller_id)

    return jsonify({
        "offers": [
            {
                "id": o["id"],
                "listingId": o["listing_id"],
                "listingTitle": o["listing_title"],
                "listingCategory": o["listing_category"],
                "listingPrice": o["listing_price"],
                "buyerId": o["buyer_id"],
                "buyerDisplayName": o["buyer_display_name"],
                "offerType": o["offer_type"],
                "proposedPrice": o["proposed_price"],
                "swapListingId": o["swap_listing_id"],
                "swapListingTitle": o["swap_listing_title"],
                "status": o["status"],
                "createdAt": o["created_at"],
            }
            for o in offers
        ]
    }), 200


# ---------------------------------------------------------------------------
# PATCH /api/offers/<id>/accept  —  seller accepts an offer
# ---------------------------------------------------------------------------

@offers_bp.route("/api/offers/<int:offer_id>/accept", methods=["PATCH"])
def api_accept_offer(offer_id):
    """
    Accept a pending offer and auto-reject all other pending offers
    for the same listing. Creates a transaction record.

    AC1-AC5 — accept offer user story.
    AC1 — accept offer auto-reject user story.
    """
    if not session.get("user_id"):
        return jsonify({"error": "You must be logged in to accept an offer."}), 401

    offer = db_module.get_offer_by_id(offer_id)
    if offer is None:
        return jsonify({"error": "Offer not found."}), 404

    # Only the listing owner may accept
    seller_id = db_module.get_listing_owner(offer["listing_id"])
    if seller_id != session["user_id"]:
        return jsonify({"error": "You are not authorised to accept this offer."}), 403

    if offer["status"] != "Pending":
        return jsonify({"error": "Only pending offers can be accepted."}), 409

    updated = db_module.accept_offer(offer_id)
    return jsonify({
        "message": "Offer accepted. Other pending offers for this listing have been rejected.",
        "offer": _format_offer(updated),
    }), 200


# ---------------------------------------------------------------------------
# PATCH /api/offers/<id>/reject  —  seller rejects an offer
# ---------------------------------------------------------------------------

@offers_bp.route("/api/offers/<int:offer_id>/reject", methods=["PATCH"])
def api_reject_offer(offer_id):
    """
    Reject a single pending offer. Other offers are not affected.

    AC1-AC3 — reject offer user story.
    """
    if not session.get("user_id"):
        return jsonify({"error": "You must be logged in to reject an offer."}), 401

    offer = db_module.get_offer_by_id(offer_id)
    if offer is None:
        return jsonify({"error": "Offer not found."}), 404

    # Only the listing owner may reject
    seller_id = db_module.get_listing_owner(offer["listing_id"])
    if seller_id != session["user_id"]:
        return jsonify({"error": "You are not authorised to reject this offer."}), 403

    if offer["status"] != "Pending":
        return jsonify({"error": "Only pending offers can be rejected."}), 409

    updated = db_module.reject_offer(offer_id)
    return jsonify({
        "message": "Offer rejected.",
        "offer": _format_offer(updated),
    }), 200