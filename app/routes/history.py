"""Routes for viewing a user's transaction and resolved-offer history."""

from flask import Blueprint, jsonify, request, session

import app.db as db_module

history_bp = Blueprint("history", __name__)

VALID_ROLES = ("buyer", "seller")


def _format_transaction(transaction):
    """Serialise a transaction row to the history page's JSON contract."""
    return {
        "id": transaction["id"],
        "offerId": transaction.get("offer_id"),
        "listingTitle": transaction["listing_title"],
        "listingCategory": transaction["listing_category"],
        "counterpartyDisplayName": transaction["counterparty_display_name"],
        "transactionType": transaction["transaction_type"],
        "amount": transaction["amount"],
        "createdAt": transaction["created_at"],
    }


def _is_active_admin(user_id):
    """Return True when the current user is an active admin in the database."""
    if session.get("role") != "admin":
        return False

    user = db_module.get_user_by_id(user_id)
    return user is not None and user["role"] == "admin" and user["status"] == "Active"


def _format_resolved_offer(offer):
    """Serialise an accepted or rejected offer for the history page."""
    return {
        "id": offer["id"],
        "listingId": offer["listing_id"],
        "listingTitle": offer["listing_title"],
        "listingCategory": offer["listing_category"],
        "listingPrice": offer["listing_price"],
        "buyerDisplayName": offer["buyer_display_name"],
        "sellerDisplayName": offer["seller_display_name"],
        "offerType": offer["offer_type"],
        "proposedPrice": offer["proposed_price"],
        "swapListingTitle": offer["swap_listing_title"],
        "status": offer["status"],
        "createdAt": offer["created_at"],
    }


# ---------------------------------------------------------------------------
# GET /api/transactions - view completed transaction history
# ---------------------------------------------------------------------------

@history_bp.route("/api/transactions", methods=["GET"])
def api_get_transactions():
    """Return the logged-in user's completed transactions for one role."""
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401

    role = request.args.get("role", "buyer")
    if role not in VALID_ROLES:
        return jsonify({"error": "role must be 'buyer' or 'seller'"}), 400

    transactions = db_module.get_transactions_for_user(session["user_id"], role)

    return jsonify({
        "role": role,
        "transactions": [_format_transaction(row) for row in transactions],
    }), 200


@history_bp.route("/api/transactions/offers", methods=["GET"])
def api_get_resolved_offers():
    """Return accepted and rejected offer outcomes for active admins."""
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401

    user_id = session["user_id"]
    if not _is_active_admin(user_id):
        return jsonify({"error": "Only administrators can view offer outcomes."}), 403

    offers = db_module.get_all_resolved_offers()
    return jsonify({"offers": [_format_resolved_offer(offer) for offer in offers]}), 200
