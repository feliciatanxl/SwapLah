from flask import Blueprint, jsonify, request, session

from app.db import (
    create_review,
    get_listing_owner,
    get_offer_by_id
)

reviews_bp = Blueprint("reviews", __name__)

@reviews_bp.route("/api/reviews", methods=["POST"])
def submit_review():

    if "user_id" not in session:
        return jsonify({
            "error": "Login required"
        }), 401

    data = request.get_json(silent=True) or {}

    offer_id = data.get("offer_id")
    reviewee_id = data.get("reviewee_id")
    rating = data.get("rating")
    comment = data.get("comment", "")

    if rating is None:
        return jsonify({
            "error": "Rating is required"
        }), 400

    if not isinstance(rating, int) or isinstance(rating, bool):
        return jsonify({
            "error": "Rating must be a whole number from 1 to 5"
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

    seller_id = get_listing_owner(offer["listing_id"])
    buyer_id = offer["buyer_id"]
    current_user_id = session["user_id"]

    if current_user_id == buyer_id:
        counterparty_id = seller_id
    elif current_user_id == seller_id:
        counterparty_id = buyer_id
    else:
        return jsonify({
            "error": "Only participants of this transaction can leave a review"
        }), 403

    if reviewee_id is None:
        reviewee_id = counterparty_id
    elif reviewee_id != counterparty_id:
        return jsonify({
            "error": "Review must be for the other party of this transaction"
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