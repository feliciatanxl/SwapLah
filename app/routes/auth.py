"""Authentication routes: register, login, logout."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from ..models import db, User

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle student registration."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        return _handle_register(request.form)

    return render_template('register.html')


def _handle_register(form):
    """Process registration form data and create user."""
    email = form.get('email', '').strip().lower()
    student_id = form.get('student_id', '').strip()

    error = _validate_registration(form, email, student_id)
    if error:
        flash(error, 'danger')
        return render_template('register.html')

    password_hash = bcrypt.generate_password_hash(
        form['password']
    ).decode('utf-8')

    user = User(
        student_id=student_id,
        first_name=form['first_name'].strip(),
        last_name=form['last_name'].strip(),
        display_name=form['display_name'].strip(),
        email=email,
        contact_number=form['contact_number'].strip(),
        password_hash=password_hash
    )
    db.session.add(user)
    db.session.commit()
    flash('Account created! Please log in.', 'success')
    return redirect(url_for('auth.login'))


def _validate_registration(form, email, student_id):
    """Validate registration fields. Return error string or None."""
    required = ['student_id', 'first_name', 'last_name',
                'display_name', 'email', 'contact_number', 'password']
    for field in required:
        if not form.get(field, '').strip():
            return f'{field.replace("_", " ").title()} is required.'

    if not email.endswith('@nyp.edu.sg'):
        return 'Only NYP email addresses (@nyp.edu.sg) are accepted.'

    if User.query.filter_by(email=email).first():
        return 'An account with this email already exists.'

    if User.query.filter_by(student_id=student_id).first():
        return 'An account with this Student ID already exists.'

    return None


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        return _handle_login(request.form)

    return render_template('login.html')


def _handle_login(form):
    """Process login form and authenticate user."""
    email = form.get('email', '').strip().lower()
    password = form.get('password', '')

    user = User.query.filter_by(email=email).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        flash('Invalid email or password.', 'danger')
        return render_template('login.html')

    if user.is_suspended():
        flash('Your account has been suspended. Please contact admin.', 'danger')
        return render_template('login.html')

    login_user(user)
    session.permanent = True
    next_page = request.args.get('next')
    return redirect(next_page or url_for('index'))


@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
