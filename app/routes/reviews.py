from flask import Blueprint, jsonify, request, session

from app.db import (
    create_review,
    get_offer_by_id,
    get_reviews_for_user,
    get_user_by_id,
    get_user_rating_stats
)

reviews_bp = Blueprint("reviews", __name__)

@reviews_bp.route("/api/users/<int:user_id>/reviews", methods=["GET"])
def get_user_reviews(user_id):

    user = get_user_by_id(user_id)

    if user is None:
        return jsonify({
            "error": "User not found"
        }), 404

    reviews = get_reviews_for_user(user_id)
    stats = get_user_rating_stats(user_id)

    response = {
        "average_rating": stats["average_rating"],
        "review_count": stats["review_count"],
        "reviews": reviews
    }

    if stats["review_count"] == 0:
        response["message"] = "No reviews yet"

    return jsonify(response), 200

@reviews_bp.route("/api/reviews", methods=["POST"])
def submit_review():

    if "user_id" not in session:
        return jsonify({
            "error": "Login required"
        }), 401

    data = request.get_json()

    offer_id = data.get("offer_id")
    reviewee_id = data.get("reviewee_id")
    rating = data.get("rating")
    comment = data.get("comment", "")

    if rating is None:
        return jsonify({
            "error": "Rating is required"
        }), 400

    if rating < 1 or rating > 5:
        return jsonify({
            "error": "Rating must be between 1 and 5"
        }), 400

    offer = get_offer_by_id(offer_id)

    if offer is None:
        return jsonify({
            "error": "Offer not found"
        }), 404

    if offer["status"] != "Accepted":
        return jsonify({
            "error": "Transaction not completed"
        }), 400

    review = create_review(
        offer_id=offer_id,
        reviewer_id=session["user_id"],
        reviewee_id=reviewee_id,
        rating=rating,
        comment=comment
    )

    stats = get_user_rating_stats(reviewee_id)

    return jsonify({
        "message": "Review submitted successfully",
        "review": review,
        "average_rating": stats["average_rating"],
        "review_count": stats["review_count"]
    }), 201