"""Flask application factory."""

import math
import os
import re
import time

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import (
    get_active_listings_by_seller,
    search_active_listings,
    get_listing_category_summary,
    get_db_connection,
    get_listing_by_id,
    get_listings_by_seller,
    get_user_by_email,
    get_user_by_id,
    get_user_profile_stats,
    init_db,
    update_user_account,
)
from app.routes.listing import listings_bp
from app.routes.offers import offers_bp

SESSION_TIMEOUT_SECONDS = 30 * 60
# SESSION_TIMEOUT_SECONDS = 10
SESSION_TIMEOUT_MESSAGE = "Session expired due to inactivity. Please log in again."

PUBLIC_ENDPOINTS = {
    "index",
    "listing_detail",
    "login",
    "register",
    "forgot_password",
    "logout",
    "static",
    "listings.api_get_active_listings",
    "listings.api_get_listing_detail",
}

def _is_suspended_user(user):
    """Return True if the user account is suspended."""
    return user["status"] == "Suspended"

def _handle_login():
    """Process POST login form and return a redirect or re-rendered login page."""
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        flash("Please enter your email and password.", "danger")
        return render_template("login.html")

    user = get_user_by_email(email)

    if user is None or not check_password_hash(user["password_hash"], password):
        flash("Invalid email or password.", "danger")
        return render_template("login.html")

    if _is_suspended_user(user):
        flash("Your account has been suspended. Please contact an administrator.", "danger")
        return render_template("login.html")

    session["user_id"] = user["id"]
    session["email"] = user["email"]
    session["display_name"] = user["display_name"]
    session["role"] = user["role"]
    session["last_activity"] = time.time()

    flash("Logged in successfully.", "success")
    return redirect(url_for("profile"))


def _handle_register():
    """Process POST register form and return a redirect or re-rendered register page."""
    form_data = _get_registration_form_data()

    if not all(form_data.values()):
        flash("Please fill in all required fields.", "danger")
        return render_template("register.html")

    if not form_data["email"].endswith("@mymail.nyp.edu.sg"):
        flash("Please use a valid NYP email ending with @mymail.nyp.edu.sg.", "danger")
        return render_template("register.html")

    if form_data["password"] != form_data["confirm_password"]:
        flash("Passwords do not match.", "danger")
        return render_template("register.html")

    return _create_user_account(form_data)


def _get_registration_form_data():
    """Return cleaned registration form data."""
    return {
        "student_id": request.form.get("student_id", "").strip(),
        "first_name": request.form.get("first_name", "").strip(),
        "last_name": request.form.get("last_name", "").strip(),
        "display_name": request.form.get("display_name", "").strip(),
        "email": request.form.get("email", "").strip().lower(),
        "contact_number": request.form.get("contact_number", "").strip(),
        "password": request.form.get("password", ""),
        "confirm_password": request.form.get("confirm_password", ""),
    }


def _create_user_account(form_data):
    """Create a user account from validated registration form data."""
    password_hash = generate_password_hash(form_data["password"])

    try:
        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO users (
                student_id, first_name, last_name, display_name,
                email, contact_number, password_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                form_data["student_id"],
                form_data["first_name"],
                form_data["last_name"],
                form_data["display_name"],
                form_data["email"],
                form_data["contact_number"],
                password_hash,
            ),
        )
        conn.commit()
        conn.close()
    except Exception:  # noqa: BLE001
        flash("Email or Student ID already exists.", "danger")
        return render_template("register.html")

    flash("Account created successfully. Please log in.", "success")
    return redirect(url_for("login"))


def _paginate_listings(page, search="", category="", condition="", price_type="", per_page=10):
    """Return paginated listings and page metadata."""
    page = max(page, 1)
    all_listings = search_active_listings(search, category, condition, price_type)
    total_listings = len(all_listings)
    total_pages = math.ceil(total_listings / per_page) if total_listings > 0 else 1
    page = min(page, total_pages)

    start = (page - 1) * per_page
    end = start + per_page

    return {
        "listings": all_listings[start:end],
        "page": page,
        "total_pages": total_pages,
        "total_listings": total_listings,
    }


def _get_logged_in_user_or_redirect(message):
    """Return the logged-in user or a redirect response if unavailable."""
    if "user_id" not in session:
        flash(message, "danger")
        return None, redirect(url_for("login"))

    user = get_user_by_id(session["user_id"])

    if user is None:
        session.clear()
        flash("Session expired. Please log in again.", "danger")
        return None, redirect(url_for("login"))

    return user, None

def _redirect_logged_out_user(message):
    """Redirect logged-out users to the login page."""
    if "user_id" not in session:
        flash(message, "danger")
        return redirect(url_for("login"))

    return None

def _is_public_endpoint(endpoint):
    """Return True if the endpoint can be accessed without login."""
    return endpoint is None or endpoint in PUBLIC_ENDPOINTS


def _has_session_expired(now):
    """Return True if the logged-in session has been inactive for too long."""
    last_activity = session.get("last_activity")

    if last_activity is None:
        return False

    return now - float(last_activity) > SESSION_TIMEOUT_SECONDS


def _check_session_timeout():
    """Expire inactive sessions and redirect protected requests to login."""
    if "user_id" not in session:
        return None

    now = time.time()

    if _has_session_expired(now):
        session.clear()
        flash(SESSION_TIMEOUT_MESSAGE, "danger")

        if not _is_public_endpoint(request.endpoint):
            return redirect(url_for("login"))

        return None

    session["last_activity"] = now
    return None


def _register_session_timeout(app):
    """Register session inactivity timeout check before each request."""

    @app.before_request
    def enforce_session_timeout():
        return _check_session_timeout()


def _get_profile_form_data():
    """Return cleaned edit profile form data."""
    return {
        "first_name": request.form.get("first_name", "").strip(),
        "last_name": request.form.get("last_name", "").strip(),
        "display_name": request.form.get("display_name", "").strip(),
        "contact_number": request.form.get("contact_number", "").strip(),
        "password": request.form.get("password", ""),
        "confirm_password": request.form.get("confirm_password", ""),
    }


def _validate_profile_form(form_data, user):
    """Validate edit profile form data and return an error response if invalid."""
    required_fields = [
        form_data["first_name"],
        form_data["last_name"],
        form_data["display_name"],
        form_data["contact_number"],
    ]

    if not all(required_fields):
        flash("Please fill in all required profile fields.", "danger")
        return render_template("edit_profile.html", user=user)

    if not re.fullmatch(r"\d{8}", form_data["contact_number"]):
        flash("Please enter a valid contact number (8 digits).", "danger")
        return render_template("edit_profile.html", user=user)

    if form_data["password"] and form_data["password"] != form_data["confirm_password"]:
        flash("Passwords do not match.", "danger")
        return render_template("edit_profile.html", user=user)

    return None


def _save_profile_update(form_data):
    """Save profile updates for the logged-in user."""
    new_hash = generate_password_hash(form_data["password"]) if form_data["password"] else None

    update_user_account(
        session["user_id"],
        form_data["first_name"],
        form_data["last_name"],
        form_data["display_name"],
        form_data["contact_number"],
        new_hash,
    )

    session["display_name"] = form_data["display_name"]
    flash("Profile updated successfully.", "success")
    return redirect(url_for("profile"))


def _register_main_routes(app):
    """Register homepage and simple listing page routes."""

    @app.route("/")
    def index():
        """Render homepage with paginated listings."""
        page = request.args.get("page", 1, type=int)
        search = request.args.get("search", "").strip()
        category = request.args.get("category", "").strip()
        condition = request.args.get("condition", "").strip()
        price_type = request.args.get("price_type", "").strip()

        pagination = _paginate_listings(page, search, category, condition, price_type)

        return render_template(
            "index.html",
            listings=pagination["listings"],
            page=pagination["page"],
            total_pages=pagination["total_pages"],
            total_listings=pagination["total_listings"],
            category_summary=get_listing_category_summary(),
            search=search,
            category=category,
            condition=condition,
            price_type=price_type,
        )

    @app.route("/listing/<int:listing_id>")
    def listing_detail(listing_id):
        """Render listing detail page."""
        listing = get_listing_by_id(listing_id)

        if listing is None:
            return render_template(
                "listing_detail.html",
                listing=None,
                error_message="This listing does not exist or is no longer available.",
            ), 404

        return render_template(
            "listing_detail.html",
            listing=listing,
            listing_id=listing_id,
            error_message=None,
        )


def _register_listing_owner_routes(app):
    """Register listing owner page routes."""

    @app.route("/api/my-listings")
    def api_my_listings():
        """Return the current user's listings as JSON for the swap dropdown."""
        user_id = session.get("user_id")

        if not user_id:
            return jsonify({"error": "Not logged in."}), 401

        listings = get_listings_by_seller(user_id)
        return jsonify(listings)

    @app.route("/listing/<int:listing_id>/edit")
    def edit_listing(listing_id):
        """Render edit listing page if the logged-in user owns the listing."""
        if "user_id" not in session:
            flash("Please log in to edit your listing.", "danger")
            return redirect(url_for("login"))

        listing = get_listing_by_id(listing_id)

        if listing is None:
            flash("This listing does not exist or is no longer available.", "danger")
            return redirect(url_for("index"))

        if listing["seller_id"] != session["user_id"]:
            flash("You are not allowed to edit this listing.", "danger")
            return redirect(url_for("listing_detail", listing_id=listing_id))

        return render_template("edit_listing.html", listing=listing)


def _register_profile_routes(app):
    """Register profile view and edit routes."""

    @app.route("/profile")
    def profile():
        """Render profile page for logged-in user."""
        user, redirect_response = _get_logged_in_user_or_redirect(
            "Please log in to access your profile."
        )

        if redirect_response:
            return redirect_response

        return render_template(
            "profile.html",
            user=user,
            active_listings=get_active_listings_by_seller(user["id"]),
            profile_stats=get_user_profile_stats(user["id"]),
        )

    @app.route("/profile/edit", methods=["GET", "POST"])
    def edit_profile():
        """Render and handle edit profile page."""
        user, redirect_response = _get_logged_in_user_or_redirect(
            "Please log in to edit your profile."
        )

        if redirect_response:
            return redirect_response

        if request.method == "GET":
            return render_template("edit_profile.html", user=user)

        form_data = _get_profile_form_data()
        error_response = _validate_profile_form(form_data, user)

        if error_response:
            return error_response

        return _save_profile_update(form_data)


def _register_auth_routes(app):
    """Register authentication routes."""

    @app.route("/login", methods=["GET", "POST"])
    def login():
        """Render login page or process login form."""
        if request.method == "GET":
            return render_template("login.html")

        return _handle_login()

    @app.route("/register", methods=["GET", "POST"])
    def register():
        """Render register page or process registration form."""
        if request.method == "GET":
            return render_template("register.html")

        return _handle_register()

    @app.route("/forgot-password")
    def forgot_password():
        """Render forgot password page."""
        return render_template("forgot_password.html")

    @app.route("/logout")
    def logout():
        """Clear session and redirect to login."""
        session.clear()
        flash("You have been logged out.", "success")
        return redirect(url_for("login"))


def _register_simple_page_routes(app):
    """Register static page routes."""

    @app.route("/offers")
    def offers():
        """Render offers page for logged-in users."""
        redirect_response = _redirect_logged_out_user("Please log in to view your offers.")

        if redirect_response:
            return redirect_response

        return render_template("offers.html")

    @app.route("/history")
    def history():
        """Render history page for logged-in users."""
        redirect_response = _redirect_logged_out_user("Please log in to view your history.")

        if redirect_response:
            return redirect_response

        return render_template("history.html")

    @app.route("/sell")
    def sell():
        """Render sell page for logged-in users."""
        redirect_response = _redirect_logged_out_user("Please log in to create a listing.")

        if redirect_response:
            return redirect_response

        return render_template("sell.html")

    @app.route("/admin")
    def admin():
        """Render admin page."""
        return render_template("admin.html")


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    init_db()

    _register_main_routes(app)
    _register_listing_owner_routes(app)
    _register_profile_routes(app)
    _register_auth_routes(app)
    _register_simple_page_routes(app)
    _register_session_timeout(app)

    app.register_blueprint(listings_bp)
    app.register_blueprint(offers_bp)

    return app
