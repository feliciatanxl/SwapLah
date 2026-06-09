"""SwapLah application factory."""
import os
from datetime import timedelta
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager
from dotenv import load_dotenv
from .models import db, User

load_dotenv()

login_manager = LoginManager()


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-dev-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 'sqlite:///swaplah.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    from .routes.auth import auth_bp
    from .routes.listing import listing_bp
    from .routes.offers import offers_bp
    from .routes.history import history_bp
    from .routes.profile import profile_bp
    from .routes.profile_edit import profile_edit_bp
    from .routes.sell import sell_bp
    from .routes.admin import admin_bp
    from .routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(listing_bp)
    app.register_blueprint(offers_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(profile_edit_bp)
    app.register_blueprint(sell_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.route('/')
    def index():
        return render_template('index.html')

    with app.app_context():
        db.create_all()
        _seed_admin()

    return app


def _seed_admin():
    """Create a default admin account if none exists."""
    from .models import User
    from flask_bcrypt import Bcrypt
    bcrypt = Bcrypt()
    if not User.query.filter_by(is_admin=True).first():
        admin = User(
            student_id='ADMIN001',
            first_name='Admin',
            last_name='User',
            display_name='Admin',
            email='admin@nyp.edu.sg',
            contact_number='00000000',
            password_hash=bcrypt.generate_password_hash(
                os.environ.get('ADMIN_PASSWORD', 'Admin@123')
            ).decode('utf-8'),
            is_admin=True,
            status='Active'
        )
        db.session.add(admin)
        db.session.commit()

from .models import db 