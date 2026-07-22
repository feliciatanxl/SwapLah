"""Flask application factory."""
import math
import re
import sqlite3

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import (
    get_all_listings,
    get_db_connection,
    get_listing_by_id,
    get_listings_by_seller,
    get_reviews_for_user,
    get_user_by_email,
    get_user_by_id,
    get_user_rating_stats,
    init_db,
    update_user_account,
)
from app.routes.listing import listings_bp
from app.routes.offers import offers_bp
from app.routes.reviews import reviews_bp


def _handle_login():
    """Process POST login form and return a redirect or re-rendered login page."""
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    if not email or not password:
        flash('Please enter your email and password.', 'danger')
        return render_template('login.html')

    user = get_user_by_email(email)

    if user is None or not check_password_hash(user['password_hash'], password):
        flash('Invalid email or password.', 'danger')
        return render_template('login.html')

    if user['status'] == 'Suspended':
        flash('Your account has been suspended. Please contact an administrator.', 'danger')
        return render_template('login.html')

    session['user_id'] = user['id']
    session['email'] = user['email']
    session['display_name'] = user['display_name']
    session['role'] = user['role']

    flash('Logged in successfully.', 'success')
    return redirect(url_for('profile'))


def _handle_register():
    """Process POST register form and return a redirect or re-rendered register page."""
    student_id = request.form.get('student_id', '').strip()
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    display_name = request.form.get('display_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    contact_number = request.form.get('contact_number', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    required_fields = [
        student_id, first_name, last_name, display_name,
        email, contact_number, password, confirm_password,
    ]

    if not all(required_fields):
        flash('Please fill in all required fields.', 'danger')
        return render_template('register.html')

    if not email.endswith('@mymail.nyp.edu.sg'):
        flash('Please use a valid NYP email ending with @mymail.nyp.edu.sg.', 'danger')
        return render_template('register.html')

    if password != confirm_password:
        flash('Passwords do not match.', 'danger')
        return render_template('register.html')

    password_hash = generate_password_hash(password)

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
            (student_id, first_name, last_name, display_name,
             email, contact_number, password_hash),
        )
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        flash('Email or Student ID already exists.', 'danger')
        return render_template('register.html')

    flash('Account created successfully. Please log in.', 'success')
    return redirect(url_for('login'))


def _validate_profile_form(form_data, user):
    """Validate edit profile form data and return an error response if invalid."""
    required_fields = [
        form_data['first_name'],
        form_data['last_name'],
        form_data['display_name'],
        form_data['contact_number'],
    ]

    if not all(required_fields):
        flash('Please fill in all required profile fields.', 'danger')
        return render_template('edit_profile.html', user=user)

    if not re.fullmatch(r'\d{8}', form_data['contact_number']):
        flash('Please enter a valid contact number (8 digits).', 'danger')
        return render_template('edit_profile.html', user=user)

    if form_data['password'] and form_data['password'] != form_data['confirm_password']:
        flash('Passwords do not match.', 'danger')
        return render_template('edit_profile.html', user=user)

    return None


def _register_main_routes(app):
    """Register the homepage and listing detail routes."""

    @app.route('/')
    def index():
        page = request.args.get('page', 1, type=int)
        per_page = 10
        page = max(page, 1)

        all_listings = get_all_listings()
        total_listings = len(all_listings)
        total_pages = math.ceil(total_listings / per_page) if total_listings > 0 else 1
        page = min(page, total_pages)

        start = (page - 1) * per_page
        end = start + per_page
        listings = all_listings[start:end]

        return render_template(
            'index.html',
            listings=listings,
            page=page,
            total_pages=total_pages,
            total_listings=total_listings
        )

    @app.route('/listing/<int:listing_id>')
    def listing_detail(listing_id):
        """Render listing detail page."""
        listing = get_listing_by_id(listing_id)
        if listing is None:
            return render_template(
                'listing_detail.html',
                listing=None,
                error_message='This listing does not exist or is no longer available.'
            ), 404

        seller_rating = get_user_rating_stats(listing['seller_id'])

        return render_template(
            'listing_detail.html',
            listing=listing,
            listing_id=listing_id,
            seller_rating=seller_rating,
            error_message=None
        )


def _register_listing_owner_routes(app):
    """Register routes used by a listing's owner."""

    @app.route('/api/my-listings')
    def api_my_listings():
        """Return the current user's listings as JSON (for the swap dropdown)."""
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not logged in.'}), 401
        listings = get_listings_by_seller(user_id)
        return jsonify(listings)

    @app.route('/listing/<int:listing_id>/edit')
    def edit_listing(listing_id):
        """Render the edit listing page for the listing's owner."""
        if 'user_id' not in session:
            flash('Please log in to edit your listing.', 'danger')
            return redirect(url_for('login'))

        listing = get_listing_by_id(listing_id)

        if listing is None:
            flash('This listing does not exist or is no longer available.', 'danger')
            return redirect(url_for('index'))

        if listing['seller_id'] != session['user_id']:
            flash('You are not allowed to edit this listing.', 'danger')
            return redirect(url_for('listing_detail', listing_id=listing_id))

        return render_template('edit_listing.html', listing=listing)


def _register_profile_routes(app):
    """Register profile view and edit routes."""

    @app.route('/profile')
    def profile():
        """Render profile page for logged-in user."""
        if 'user_id' not in session:
            flash('Please log in to access your profile.', 'danger')
            return redirect(url_for('login'))
        user = get_user_by_id(session['user_id'])
        if user is None:
            session.clear()
            flash('Session expired. Please log in again.', 'danger')
            return redirect(url_for('login'))
        rating = get_user_rating_stats(session['user_id'])
        reviews = get_reviews_for_user(session['user_id'])
        return render_template(
            'profile.html', user=user, rating=rating, reviews=reviews, is_own_profile=True
        )

    @app.route('/profile/<int:user_id>')
    def view_profile(user_id):
        """Render another user's public profile page."""
        if session.get('user_id') == user_id:
            return redirect(url_for('profile'))
        user = get_user_by_id(user_id)
        if user is None:
            flash('This user does not exist.', 'danger')
            return redirect(url_for('index'))
        rating = get_user_rating_stats(user_id)
        reviews = get_reviews_for_user(user_id)
        return render_template(
            'profile.html', user=user, rating=rating, reviews=reviews, is_own_profile=False
        )

    @app.route('/profile/edit', methods=['GET', 'POST'])
    def edit_profile():
        """Render and handle edit profile page."""
        if 'user_id' not in session:
            flash('Please log in to edit your profile.', 'danger')
            return redirect(url_for('login'))
        user = get_user_by_id(session['user_id'])
        if user is None:
            session.clear()
            flash('Session expired. Please log in again.', 'danger')
            return redirect(url_for('login'))
        if request.method == 'GET':
            return render_template('edit_profile.html', user=user)

        form_data = {
            'first_name': request.form.get('first_name', '').strip(),
            'last_name': request.form.get('last_name', '').strip(),
            'display_name': request.form.get('display_name', '').strip(),
            'contact_number': request.form.get('contact_number', '').strip(),
            'password': request.form.get('password', ''),
            'confirm_password': request.form.get('confirm_password', ''),
        }

        error_response = _validate_profile_form(form_data, user)
        if error_response:
            return error_response

        new_hash = generate_password_hash(form_data['password']) if form_data['password'] else None
        update_user_account(
            session['user_id'],
            form_data['first_name'],
            form_data['last_name'],
            form_data['display_name'],
            form_data['contact_number'],
            new_hash,
        )
        session['display_name'] = form_data['display_name']
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('profile'))


def _register_simple_page_routes(app):
    """Register static page routes that require no query logic."""

    @app.route('/sell')
    def sell():
        """Render sell page."""
        return render_template('sell.html')

    @app.route('/offers')
    def offers():
        """Render offers page."""
        return render_template('offers.html')

    @app.route('/history')
    def history():
        """Render history page."""
        return render_template('history.html')

    @app.route('/admin')
    def admin():
        """Render admin page."""
        return render_template('admin.html')


def _register_auth_routes(app):
    """Register authentication routes."""

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Render login page or process login form."""
        if request.method == 'GET':
            return render_template('login.html')
        return _handle_login()

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """Render register page or process registration form."""
        if request.method == 'GET':
            return render_template('register.html')
        return _handle_register()

    @app.route('/forgot-password')
    def forgot_password():
        """Render forgot password page."""
        return render_template('forgot_password.html')

    @app.route('/logout')
    def logout():
        """Clear session and redirect to login."""
        session.clear()
        flash('You have been logged out.', 'success')
        return redirect(url_for('login'))


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'
    init_db()

    _register_main_routes(app)
    _register_listing_owner_routes(app)
    _register_profile_routes(app)
    _register_simple_page_routes(app)
    _register_auth_routes(app)

    app.register_blueprint(listings_bp)
    app.register_blueprint(offers_bp)
    app.register_blueprint(reviews_bp)

    return app
