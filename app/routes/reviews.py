"""Routes for submitting and retrieving reviews after completed transactions."""

from flask import Blueprint, jsonify, request, session

import app.db as db_module

reviews_bp = Blueprint("reviews", __name__)


def _rating_error(rating):
    """Return a validation error for an invalid rating, otherwise None."""
    if rating is None:
        return "Rating is required"
    if not isinstance(rating, int) or isinstance(rating, bool):
        return "Rating must be a whole number from 1 to 5"
    if rating < 1 or rating > 5:
        return "Rating must be between 1 and 5"
    return None


def _reviewed_user_for_offer(offer, current_user_id):
    """Return the transaction counterparty ID and any authorization error."""
    seller_id = db_module.get_listing_owner(offer["listing_id"])

    if seller_id is None:
        return None, ("Listing not found", 404)
    if current_user_id == offer["buyer_id"]:
        return seller_id, None
    if current_user_id == seller_id:
        return offer["buyer_id"], None
    return None, ("Only participants of this transaction can leave a review", 403)


def _validate_offer(offer_id, current_user_id):
    """Return the reviewed user for an accepted offer or an API error."""
    offer = db_module.get_offer_by_id(offer_id)

    if offer is None:
        return None, ("Offer not found", 404)
    if offer["status"] != "Accepted":
        return None, ("Transaction not completed", 400)
    return _reviewed_user_for_offer(offer, current_user_id)


def _resolve_reviewee(offer_id, current_user_id, requested_reviewee_id):
    """Return the reviewee ID for a review, or an API error."""
    reviewed_user_id, offer_error = _validate_offer(offer_id, current_user_id)

    if offer_error:
        return None, offer_error
    if requested_reviewee_id is not None and requested_reviewee_id != reviewed_user_id:
        return None, ("Review must be for the other party of this transaction", 400)
    return reviewed_user_id, None


@reviews_bp.route("/api/reviews", methods=["POST"])
def submit_review():
    """Create a review from either participant for the other participant."""
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401

    data = request.get_json(silent=True) or {}
    rating = data.get("rating")
    error = _rating_error(rating)

    if error:
        return jsonify({"error": error}), 400

    reviewee_id, review_error = _resolve_reviewee(
        data.get("offer_id"), session["user_id"], data.get("reviewee_id")
    )

    if review_error:
        message, status_code = review_error
        return jsonify({"error": message}), status_code

    review = db_module.create_review(
        reviewer_id=session["user_id"],
        reviewed_user_id=reviewee_id,
        rating=rating,
        comment=data.get("comment", ""),
    )
    stats = db_module.get_user_rating_stats(reviewee_id)

    return jsonify(
        {
            "message": "Review submitted successfully",
            "review": review,
            "average_rating": stats["average_rating"],
            "review_count": stats["review_count"],
        }
    ), 201


@reviews_bp.route("/api/users/<int:user_id>/reviews", methods=["GET"])
def get_user_reviews(user_id):
    """Return public reviews for one existing user as JSON."""
    if db_module.get_user_by_id(user_id) is None:
        return jsonify({"error": "User not found."}), 404

    return jsonify({"reviews": db_module.get_reviews_for_user(user_id)}), 200
