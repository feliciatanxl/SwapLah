from flask import Blueprint, jsonify, request, session

from app.db import (
    create_review,
    get_offer_by_id
)

reviews_bp = Blueprint("reviews", __name__)

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

    return jsonify({
        "message": "Review submitted successfully",
        "review": review
    }), 201