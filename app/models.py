"""Database models for SwapLah application."""
import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def generate_uuid():
    """Generate a UUID string for use as primary key."""
    return str(uuid.uuid4())


class User(db.Model):
    """Represents a registered student user."""
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    display_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    status = db.Column(db.String(10), default='Active', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    listings = db.relationship('Listing', backref='seller', lazy=True,
                               foreign_keys='Listing.seller_id')
    reports = db.relationship('Report', backref='reporter', lazy=True)
    reviews_given = db.relationship('Review', backref='reviewer', lazy=True,
                                    foreign_keys='Review.reviewer_id')
    reviews_received = db.relationship('Review', backref='reviewee', lazy=True,
                                       foreign_keys='Review.reviewee_id')

    def is_active_account(self):
        """Return True if account is active."""
        return self.status == 'Active'

    def is_suspended(self):
        """Return True if account is suspended."""
        return self.status == 'Suspended'

    def get_average_rating(self):
        """Calculate and return average star rating from all reviews received."""
        if not self.reviews_received:
            return None
        total = sum(r.star_rating for r in self.reviews_received)
        return round(total / len(self.reviews_received), 1)

    def to_dict(self):
        """Serialize user to dictionary (excludes sensitive fields)."""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'display_name': self.display_name,
            'email': self.email,
            'contact_number': self.contact_number,
            'is_admin': self.is_admin,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'average_rating': self.get_average_rating()
        }


class Listing(db.Model):
    """Represents an item listed for sale or swap."""
    __tablename__ = 'listings'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    seller_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    condition = db.Column(db.String(20), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    listing_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)

    offers = db.relationship('Offer', backref='listing', lazy=True, foreign_keys='Offer.listing_id')
    reports = db.relationship('Report', backref='listing', lazy=True)

    CATEGORIES = ['Textbooks', 'Electronics', 'Lab Equipment',
                  'Clothing', 'Stationery', 'Others']
    CONDITIONS = ['New', 'Like New', 'Good', 'Fair']

    def to_dict(self):
        """Serialize listing to dictionary."""
        return {
            'id': self.id,
            'seller_id': self.seller_id,
            'seller_display_name': self.seller.display_name if self.seller else None,
            'seller_email': self.seller.email if self.seller else None,
            'seller_contact': self.seller.contact_number if self.seller else None,
            'title': self.title,
            'description': self.description,
            'price': self.price,
            'category': self.category,
            'condition': self.condition,
            'image_url': self.image_url,
            'is_deleted': self.is_deleted,
            'listing_date': self.listing_date.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Offer(db.Model):
    """Represents a buyer's offer on a listing."""
    __tablename__ = 'offers'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    listing_id = db.Column(db.String(36), db.ForeignKey('listings.id'), nullable=False)
    buyer_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    offer_type = db.Column(db.String(10), nullable=False)
    proposed_price = db.Column(db.String(50), nullable=True)
    swap_listing_id = db.Column(db.String(36), db.ForeignKey('listings.id'), nullable=True)
    status = db.Column(db.String(10), default='Pending', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    buyer = db.relationship('User', backref='offers', foreign_keys=[buyer_id])
    swap_listing = db.relationship('Listing', foreign_keys=[swap_listing_id])

    STATUSES = ['Pending', 'Accepted', 'Rejected']

    def to_dict(self):
        """Serialize offer to dictionary."""
        return {
            'id': self.id,
            'listing_id': self.listing_id,
            'buyer_id': self.buyer_id,
            'buyer_display_name': self.buyer.display_name if self.buyer else None,
            'offer_type': self.offer_type,
            'proposed_price': self.proposed_price,
            'swap_listing_id': self.swap_listing_id,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }


class Transaction(db.Model):
    """Represents a completed deal between buyer and seller."""
    __tablename__ = 'transactions'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    offer_id = db.Column(db.String(36), db.ForeignKey('offers.id'), nullable=False)
    listing_id = db.Column(db.String(36), db.ForeignKey('listings.id'), nullable=False)
    buyer_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    seller_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

    offer = db.relationship('Offer', backref='transaction')
    listing = db.relationship('Listing', backref='transaction')
    buyer = db.relationship('User', foreign_keys=[buyer_id], backref='purchases')
    seller = db.relationship('User', foreign_keys=[seller_id], backref='sales')
    reviews = db.relationship('Review', backref='transaction', lazy=True)

    def to_dict(self):
        """Serialize transaction to dictionary."""
        return {
            'id': self.id,
            'offer_id': self.offer_id,
            'listing_id': self.listing_id,
            'listing_title': self.listing.title if self.listing else None,
            'buyer_id': self.buyer_id,
            'seller_id': self.seller_id,
            'completed_at': self.completed_at.isoformat()
        }


class Review(db.Model):
    """Represents a post-transaction review left by buyer or seller."""
    __tablename__ = 'reviews'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    transaction_id = db.Column(db.String(36), db.ForeignKey('transactions.id'), nullable=False)
    reviewer_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    reviewee_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    star_rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Serialize review to dictionary."""
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'reviewer_id': self.reviewer_id,
            'reviewer_display_name': self.reviewer.display_name if self.reviewer else None,
            'reviewee_id': self.reviewee_id,
            'star_rating': self.star_rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat()
        }


class Report(db.Model):
    """Represents a user report against an inappropriate listing."""
    __tablename__ = 'reports'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    listing_id = db.Column(db.String(36), db.ForeignKey('listings.id'), nullable=False)
    reporter_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(10), default='Pending', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    REASONS = [
        'Prohibited Item',
        'Misleading Description',
        'Spam or Duplicate',
        'Inappropriate Content',
        'Suspected Scam',
        'Other'
    ]
    STATUSES = ['Pending', 'Dismissed', 'Actioned']

    def to_dict(self):
        """Serialize report to dictionary."""
        return {
            'id': self.id,
            'listing_id': self.listing_id,
            'listing_title': self.listing.title if self.listing else None,
            'reporter_id': self.reporter_id,
            'reporter_display_name': self.reporter.display_name if self.reporter else None,
            'reason': self.reason,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }
