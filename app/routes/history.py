"""Routes for viewing a user's transaction history."""
from flask import Blueprint, jsonify, request, session

import app.db as db_module

history_bp = Blueprint("history", __name__)


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


def _is_active_admin(user_id):
    """Return True when the current user is an active admin in the database."""
    if session.get("role") != "admin":
        return False

    user = db_module.get_user_by_id(user_id)
    return user is not None and user["role"] == "admin" and user["status"] == "Active"


def _format_resolved_offer(offer):
    """Serialise an accepted or rejected offer for the transaction history page."""
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
# GET /api/transactions  â€”  view completed transaction history
# ---------------------------------------------------------------------------

@history_bp.route("/api/transactions", methods=["GET"])
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
    transactions = db_module.get_transactions_for_user(user_id, role)

    return jsonify({
        "role": role,
        "transactions": [_format_transaction(t) for t in transactions],
    }), 200


@history_bp.route("/api/transactions/offers", methods=["GET"])
def api_get_resolved_offers():
    """Return accepted and rejected offer outcomes for active admins."""
    if not session.get("user_id"):
        return jsonify({"error": "You must be logged in to view your transaction history."}), 401

    user_id = session["user_id"]
    if not _is_active_admin(user_id):
        return jsonify({"error": "Only administrators can view offer outcomes."}), 403

    offers = db_module.get_all_resolved_offers()
    return jsonify({"offers": [_format_resolved_offer(offer) for offer in offers]}), 200
