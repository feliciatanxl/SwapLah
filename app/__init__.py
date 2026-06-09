from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
import math
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
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key' 
    init_db()

    @app.route('/')
    def index():
        page = request.args.get('page', 1, type=int)
        per_page = 10

        if page < 1:
            page = 1

        all_listings = get_all_listings()
        total_listings = len(all_listings)
        total_pages = math.ceil(total_listings / per_page) if total_listings > 0 else 1

        if page > total_pages:
            page = total_pages

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
        listing = get_listing_by_id(listing_id)

        if listing is None:
            return render_template(
                'listing_detail.html',
                listing=None,
                error_message='This listing does not exist or is no longer available.'
            ), 404

        return render_template(
            'listing_detail.html',
            listing=listing,
            error_message=None
        )
    
    @app.route('/listing/<int:listing_id>/edit')
    def edit_listing(listing_id):
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

        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        display_name = request.form.get('display_name', '').strip()
        contact_number = request.form.get('contact_number', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        user.update({
            'first_name': first_name,
            'last_name': last_name,
            'display_name': display_name,
            'contact_number': contact_number,
        })

        if not first_name or not last_name or not display_name or not contact_number:
            flash('Please fill in all required profile fields.', 'danger')
            return render_template('edit_profile.html', user=user)

        if not contact_number.isdigit() or len(contact_number) < 8 or len(contact_number) > 15:
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
            session['user_id'],
            first_name,
            last_name,
            display_name,
            contact_number,
            password_hash,
        )

        session['display_name'] = display_name

        flash('Profile updated successfully.', 'success')
        return redirect(url_for('profile'))

    @app.route('/sell')
    def sell():
        return render_template('sell.html')

    @app.route('/admin')
    def admin():
        return render_template('admin.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'GET':
            return render_template('login.html')

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

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'GET':
            return render_template('register.html')

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
            email, contact_number, password, confirm_password
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
                (
                    student_id, first_name, last_name, display_name,
                    email, contact_number, password_hash
                )
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

    ## Blueprints
    app.register_blueprint(listings_bp)
    
    return app
