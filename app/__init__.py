"""Flask application factory."""

import math
import os
import re
import time
from functools import wraps

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash
from app.auth import admin_required, _require_admin_response

from app.db import (
    search_active_listings,
    get_reviews_for_user,
    get_db_connection,
    get_listing_by_id,
    get_listings_by_seller,
    get_user_by_email,
    get_user_by_id,
    init_db,
    update_user_account,
    get_all_reports, 
)
import app.db as db_module  # noqa: F401 — exposes db functions for monkeypatching in tests
from app.routes.listing import listings_bp
from app.routes.offers import offers_bp
from app.routes.history import history_bp
from app.routes.admin import admin_bp  

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
    "api_health",
    "api_user_reviews",
}

def _is_suspended_user(user):
    """Return True if the user account is suspended."""
    return user["status"] == "Suspended"


def _load_secret_key():
    """Return the required Flask secret key from the environment."""
    secret_key = os.getenv("SECRET_KEY")

    if not secret_key:
        raise RuntimeError("SECRET_KEY environment variable is required.")

    return secret_key


def _admin_denied_response():
    """Return the standard response for a logged-in non-admin user."""
    return "Forbidden", 403

def _is_admin_path(path):
    """Return True for the admin page and all admin subpaths."""
    return path == "/admin" or path.startswith("/admin/")

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
    conn = None

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
    except Exception:  # noqa: BLE001
        flash("Email or Student ID already exists.", "danger")
        return render_template("register.html")
    finally:
        if conn is not None:
            conn.close()

    flash("Account created successfully. Please log in.", "success")
    return redirect(url_for("login"))


def _paginate_listings(page, search="", category="", condition="", per_page=10):
    """Return paginated listings and page metadata."""
    page = max(page, 1)
    all_listings = search_active_listings(search, category, condition)
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


def _render_index_page(page, search, category, condition):
    """Render homepage with paginated listing data."""
    pagination = _paginate_listings(page, search, category, condition)
    return render_template(
        "index.html",
        listings=pagination["listings"],
        page=pagination["page"],
        total_pages=pagination["total_pages"],
        total_listings=pagination["total_listings"],
        search=search,
        category=category,
        condition=condition,
    )


def _render_listing_detail_page(listing_id):
    """Render the listing detail page or a not-found response."""
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


def _register_admin_path_guard(app):
    """Protect /admin and all /admin/* paths before routing."""

    @app.before_request
    def enforce_admin_path_guard():
        if not _is_admin_path(request.path) or request.endpoint == "admin":
            return None

        return _require_admin_response()


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

    @app.route("/api/health")
    def api_health():
        """Return application health status."""
        return jsonify({"status": "ok"}), 200

    @app.route("/api/users/<int:user_id>/reviews")
    def api_user_reviews(user_id):
        """Return public reviews for one user."""
        if get_user_by_id(user_id) is None:
            return jsonify({"error": "User not found."}), 404

        return jsonify({"reviews": get_reviews_for_user(user_id)}), 200

    @app.route("/")
    def index():
        """Render homepage with paginated listings."""
        page = request.args.get("page", 1, type=int)
        search = request.args.get("search", "").strip()
        category = request.args.get("category", "").strip()
        condition = request.args.get("condition", "").strip()
        return _render_index_page(page, search, category, condition)

    @app.route("/listing/<int:listing_id>")
    def listing_detail(listing_id):
        """Render listing detail page."""
        return _render_listing_detail_page(listing_id)

    # Add API endpoint for reports
    @app.route("/api/admin/reports")
    @admin_required
    def api_admin_reports():
        """Return all reports for the admin dashboard."""
        reports = get_all_reports()
        return jsonify({"reports": reports}), 200


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

        return render_template("profile.html", user=user)

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
    @admin_required
    def admin():
        """Render admin page."""
        return render_template("admin.html")


def create_app():
    """Create and configure the Flask application."""
    load_dotenv()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = _load_secret_key()
    init_db()

    _register_main_routes(app)
    _register_listing_owner_routes(app)
    _register_profile_routes(app)
    _register_auth_routes(app)
    _register_simple_page_routes(app)
    _register_session_timeout(app)
    _register_admin_path_guard(app)

    # Register blueprints
    app.register_blueprint(listings_bp)
    app.register_blueprint(offers_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(admin_bp) 

    return app