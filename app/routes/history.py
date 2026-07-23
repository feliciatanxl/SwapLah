"""History routes blueprint."""

from flask import Blueprint, jsonify, request, session

import app.db as db_module

history_bp = Blueprint("history", __name__)

VALID_ROLES = ("buyer", "seller")


def _serialise_transaction(row):
    """Serialise a transaction row to a JSON-safe dict for the history page."""
    return {
        "id": row["id"],
        "offerId": row["offer_id"],
        "transactionType": row["transaction_type"],
        "amount": row["amount"],
        "createdAt": row["created_at"],
        "listingTitle": row["listing_title"],
        "listingCategory": row["listing_category"],
        "counterpartyDisplayName": row["counterparty_display_name"],
    }


@history_bp.route("/api/transactions", methods=["GET"])
def api_transactions():
    """Return the logged-in user's completed transactions for one role."""
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401

    role = request.args.get("role", "buyer")

    if role not in VALID_ROLES:
        return jsonify({"error": "role must be 'buyer' or 'seller'"}), 400

    transactions = db_module.get_transactions_for_user(session["user_id"], role)

    return jsonify(
        {"transactions": [_serialise_transaction(row) for row in transactions]}
    ), 200
