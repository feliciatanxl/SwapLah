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


# ---------------------------------------------------------------------------
# GET /api/transactions  —  view completed transaction history
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