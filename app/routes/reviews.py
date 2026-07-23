"""Routes for retrieving and submitting user reviews."""

from flask import Blueprint, jsonify, request, session

import app.db as db_module

reviews_bp = Blueprint("reviews", __name__)


@reviews_bp.route("/api/users/<int:user_id>/reviews", methods=["GET"])
def get_user_reviews(user_id):
    """Return public reviews for one existing user as JSON."""
    if db_module.get_user_by_id(user_id) is None:
        return jsonify({"error": "User not found."}), 404

    return jsonify({"reviews": db_module.get_reviews_for_user(user_id)}), 200


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_review(review):
    """Serialise a review row dict to a JSON-safe dict."""
    return {
        "id": review["id"],
        "transactionId": review["transaction_id"],
        "reviewerId": review["reviewer_id"],
        "reviewedUserId": review["reviewed_user_id"],
        "rating": review["rating"],
        "comment": review["comment"],
        "createdAt": review["created_at"],
    }


def _check_seller_review_access(transaction_id):
    """
    Shared validation for the seller-review endpoint: auth, existence, ownership.

    Returns a Flask (body, status) response tuple on failure, or the
    transaction dict when the caller may proceed.
    """
    if not session.get("user_id"):
        return None, (jsonify({"error": "You must be logged in to submit a review."}), 401)

    transaction = db_module.get_transaction_by_id(transaction_id)
    if transaction is None:
        return None, (jsonify({"error": "Transaction not found or not completed."}), 404)

    if transaction["seller_id"] != session.get("user_id"):
        return None, (
            jsonify({"error": "You were not the seller in this transaction."}), 403
        )

    return transaction, None


def _validate_rating(rating):
    """Return an error (body, status) tuple if rating is not an int from 1 to 5."""
    if rating is None:
        return jsonify({"error": "rating is required."}), 400

    if not isinstance(rating, int) or isinstance(rating, bool):
        return jsonify({"error": "rating must be a whole number from 1 to 5."}), 400

    if rating < 1 or rating > 5:
        return jsonify({"error": "rating must be between 1 and 5."}), 400

    return None


# ---------------------------------------------------------------------------
# POST /api/transactions/<id>/review  —  seller reviews the buyer
# ---------------------------------------------------------------------------

@reviews_bp.route("/api/transactions/<int:transaction_id>/review", methods=["POST"])
def submit_seller_review(transaction_id):
    """
    Accepts JSON:
      rating   (int)  required, 1 to 5
      comment  (str)  optional

    Only the seller of the given completed transaction may submit this
    review, and only once the transaction exists (a transaction row is only
    ever created once an offer has been accepted). Saves a review linked to
    the transaction and to the buyer's profile.

    Returns 201 with the created review on success.
    """
    transaction, error = _check_seller_review_access(transaction_id)
    if error:
        return error

    data = request.get_json(silent=True) or {}
    rating = data.get("rating")

    rating_error = _validate_rating(rating)
    if rating_error:
        return rating_error

    comment = data.get("comment") or ""

    review = db_module.create_review(
        transaction_id=transaction_id,
        reviewer_id=transaction["seller_id"],
        reviewed_user_id=transaction["buyer_id"],
        rating=rating,
        comment=comment,
    )

    return jsonify({
        "message": "Review submitted successfully.",
        "review": _format_review(review),
    }), 201
