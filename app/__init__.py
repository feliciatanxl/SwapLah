"""SwapLah application factory."""
import os
from datetime import timedelta
from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from app.db import (
    get_all_listings,
    get_db_connection,
    get_listing_by_id,
    get_user_by_email,
    get_user_by_id,
    init_db,
    update_user_account,
)
from app.routes.listing import listings_bp
from app.routes.admin import admin_bp
from app.routes.offers import offers_bp

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

    init_db()

    @app.before_request
    def make_session_permanent():
        session.permanent = True

    @app.route('/')
    def index():
        listings = get_all_listings()
        return render_template('index.html', listings=listings)

    @app.route('/listing/<int:listing_id>')
    def listing_detail(listing_id):
        listing = get_listing_by_id(listing_id)
        if listing is None:
            return render_template(
                'listing_detail.html',
                listing=None,
                error_message='This listing does not exist or is no longer available.'
            ), 404
        return render_template(
            'listing_detail.html', listing=listing, error_message=None
        )

    @app.route('/offers')
    def offers():
        return render_template('offers.html')

    @app.route('/history')
    def history():
        return render_template('history.html')

    @app.route('/profile')
    def profile():
        if 'user_id' not in session:
            flash('Please log in to access your profile.', 'danger')
            return redirect(url_for('login'))
        user = get_user_by_id(session['user_id'])
        if user is None:
            session.clear()
            flash('Your session has expired. Please log in again.', 'danger')
            return redirect(url_for('login'))
        return render_template('profile.html', user=user)

    @app.route('/profile/edit', methods=['GET', 'POST'])
    def edit_profile():
        if 'user_id' not in session:
            flash('Please log in to update your profile.', 'danger')
            return redirect(url_for('login'))
        user = get_user_by_id(session['user_id'])
        if user is None:
            session.clear()
            flash('Your session has expired. Please log in again.', 'danger')
            return redirect(url_for('login'))
        if request.method == 'GET':
            return render_template('edit_profile.html', user=user)
        return _handle_edit_profile(user)

    def _handle_edit_profile(user):
        """Process profile edit form submission."""
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        display_name = request.form.get('display_name', '').strip()
        contact_number = request.form.get('contact_number', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        user.update({
            'first_name': first_name, 'last_name': last_name,
            'display_name': display_name, 'contact_number': contact_number,
        })

        if not all([first_name, last_name, display_name, contact_number]):
            flash('Please fill in all required profile fields.', 'danger')
            return render_template('edit_profile.html', user=user)

        if not contact_number.isdigit() or not 8 <= len(contact_number) <= 15:
            flash('Please enter a valid contact number using digits only.', 'danger')
            return render_template('edit_profile.html', user=user)

        password_hash = None
        if password or confirm_password:
            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return render_template('edit_profile.html', user=user)
            if len(password) < 8:
                flash('Password must be at least 8 characters long.', 'danger')
                return render_template('edit_profile.html', user=user)
            password_hash = generate_password_hash(password)

        update_user_account(
            session['user_id'], first_name, last_name,
            display_name, contact_number, password_hash
        )
        session['display_name'] = display_name
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('profile'))

    @app.route('/sell')
    def sell():
        return render_template('sell.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'GET':
            return render_template('login.html')
        return _handle_login()

    def _handle_login():
        """Process login form submission."""
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
            flash('Your account has been suspended. Please contact an administrator.',
                  'danger')
            return render_template('login.html')
        session['user_id'] = user['id']
        session['email'] = user['email']
        session['display_name'] = user['display_name']
        session['role'] = user['role']
        flash('Logged in successfully.', 'success')
        return redirect(url_for('profile'))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'GET':
            return render_template('register.html')
        return _handle_register()

    def _handle_register():
        """Process registration form submission."""
        student_id = request.form.get('student_id', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        display_name = request.form.get('display_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        contact_number = request.form.get('contact_number', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not all([student_id, first_name, last_name, display_name,
                    email, contact_number, password, confirm_password]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('register.html')

        if not email.endswith('@mymail.nyp.edu.sg'):
            flash('Please use a valid NYP email ending with @mymail.nyp.edu.sg.',
                  'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        try:
            conn = get_db_connection()
            conn.execute(
                """INSERT INTO users (student_id, first_name, last_name,
                   display_name, email, contact_number, password_hash)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (student_id, first_name, last_name, display_name,
                 email, contact_number, generate_password_hash(password))
            )
            conn.commit()
            conn.close()
        except Exception:
            flash('Email or Student ID already exists.', 'danger')
            return render_template('register.html')

        flash('Account created successfully. Please log in.', 'success')
        return redirect(url_for('login'))

    @app.route('/forgot-password')
    def forgot_password():
        return render_template('forgot_password.html')

    @app.route('/logout')
    def logout():
        session.clear()
        flash('You have been logged out.', 'success')
        return redirect(url_for('login'))

    app.register_blueprint(listings_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(offers_bp)

    return app
