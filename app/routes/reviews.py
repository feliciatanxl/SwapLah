"""Routes for creating buyer reviews for completed transactions."""
from flask import Blueprint, jsonify, request, session

import app.db as db_module

reviews_bp = Blueprint("reviews", __name__)


def _rating_error(rating):
    """Return a validation error tuple for invalid ratings, otherwise None."""
    if rating is None:
        return {"error": "Rating is required"}, 400

    if not isinstance(rating, int) or isinstance(rating, bool):
        return {"error": "Rating must be a whole number from 1 to 5"}, 400

    if rating < 1 or rating > 5:
        return {"error": "Rating must be between 1 and 5"}, 400

    return None


def _review_target_error(offer, reviewee_id):
    """Return a validation error if the review target does not match the seller."""
    seller_id = db_module.get_listing_owner(offer["listing_id"])

    if seller_id is None:
        return None, ({"error": "Listing not found"}, 404)

    if reviewee_id is not None and reviewee_id != seller_id:
        return None, ({"error": "Review must be for the seller of this transaction"}, 400)

    return seller_id, None


def _completed_buyer_offer_error(offer):
    """Return a validation error when the offer is not reviewable by this buyer."""
    if offer is None:
        return {"error": "Offer not found"}, 404

    if offer["status"] != "Accepted":
        return {"error": "Transaction not completed"}, 400

    if offer["buyer_id"] != session["user_id"]:
        return {"error": "Only the buyer of this transaction can leave a review"}, 403

    return None


@reviews_bp.route("/api/reviews", methods=["POST"])
def submit_review():
    """Create a seller review from the buyer of an accepted offer."""
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401

    data = request.get_json(silent=True) or {}
    rating = data.get("rating")
    rating_error = _rating_error(rating)

    if rating_error:
        return jsonify(rating_error[0]), rating_error[1]

    offer = db_module.get_offer_by_id(data.get("offer_id"))
    offer_error = _completed_buyer_offer_error(offer)

    if offer_error:
        return jsonify(offer_error[0]), offer_error[1]

    reviewed_user_id, target_error = _review_target_error(offer, data.get("reviewee_id"))

    if target_error:
        return jsonify(target_error[0]), target_error[1]

    review = db_module.create_review(
        reviewer_id=session["user_id"],
        reviewed_user_id=reviewed_user_id,
        rating=rating,
        comment=data.get("comment", ""),
    )
    stats = db_module.get_user_rating_stats(reviewed_user_id)

    return jsonify({
        "message": "Review submitted successfully",
        "review": review,
        "average_rating": stats["average_rating"],
        "review_count": stats["review_count"],
    }), 201
