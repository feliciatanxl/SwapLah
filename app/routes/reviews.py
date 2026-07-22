"""Routes for retrieving user reviews."""

from flask import Blueprint, jsonify

import app.db as db_module

reviews_bp = Blueprint("reviews", __name__)


@reviews_bp.route("/api/users/<int:user_id>/reviews", methods=["GET"])
def get_user_reviews(user_id):
    """Return public reviews for one existing user as JSON."""
    if db_module.get_user_by_id(user_id) is None:
        return jsonify({"error": "User not found."}), 404

    return jsonify({"reviews": db_module.get_reviews_for_user(user_id)}), 200
