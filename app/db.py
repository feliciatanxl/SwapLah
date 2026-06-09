import sqlite3
import json
from pathlib import Path
from datetime import datetime

DATABASE = Path(__file__).resolve().parent.parent / "swaplah.db"


def get_db_connection():
    """Return a SQLite database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create database tables if they do not exist."""
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL UNIQUE,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            display_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            contact_number TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            status TEXT NOT NULL DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            price TEXT NOT NULL,
            category TEXT NOT NULL,
            item_condition TEXT NOT NULL,
            image_url TEXT NOT NULL,
            listing_date TEXT NOT NULL,
            last_modified_timestamp TEXT NOT NULL,
            is_deleted INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (seller_id) REFERENCES users (id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER NOT NULL,
            reporter_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (listing_id) REFERENCES listings (id),
            FOREIGN KEY (reporter_id) REFERENCES users (id)
        )
        """
    )
    conn.commit()
    conn.close()


def get_user_by_email(email):
    """Retrieve one user by email using a parameterized query."""
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE email = :email",
        {"email": email},
    ).fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    """Retrieve one user by ID."""
    conn = get_db_connection()
    user = conn.execute(
        """SELECT id, student_id, first_name, last_name, display_name,
           email, contact_number, role, status, created_at
           FROM users WHERE id = :user_id""",
        {"user_id": user_id},
    ).fetchone()
    conn.close()
    return dict(user) if user else None


def update_user_account(user_id, first_name, last_name,
                        display_name, contact_number, password_hash=None):
    """Update editable account details. Email and Student ID remain locked."""
    conn = get_db_connection()
    if password_hash:
        conn.execute(
            """UPDATE users SET first_name=:first_name, last_name=:last_name,
               display_name=:display_name, contact_number=:contact_number,
               password_hash=:password_hash WHERE id=:user_id""",
            {"first_name": first_name, "last_name": last_name,
             "display_name": display_name, "contact_number": contact_number,
             "password_hash": password_hash, "user_id": user_id},
        )
    else:
        conn.execute(
            """UPDATE users SET first_name=:first_name, last_name=:last_name,
               display_name=:display_name, contact_number=:contact_number
               WHERE id=:user_id""",
            {"first_name": first_name, "last_name": last_name,
             "display_name": display_name, "contact_number": contact_number,
             "user_id": user_id},
        )
    conn.commit()
    conn.close()


def create_listing(seller_id, title, description,
                   price, category, condition, image_url):
    """Insert a new listing and return it as a dict."""
    conn = get_db_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.execute(
        """INSERT INTO listings (seller_id, title, description, price,
           category, item_condition, image_url, listing_date,
           last_modified_timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (seller_id, title, description, price,
         category, condition, image_url, now, now)
    )
    conn.commit()
    listing = conn.execute(
        "SELECT * FROM listings WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    conn.close()
    return dict(listing)


def get_all_listings():
    """Return all non-deleted listings with seller info."""
    conn = get_db_connection()
    rows = conn.execute(
        """SELECT listings.id, listings.title, listings.description,
           listings.price, listings.category,
           listings.item_condition AS condition,
           listings.image_url AS image, listings.listing_date,
           users.display_name AS seller
           FROM listings
           LEFT JOIN users ON listings.seller_id = users.id
           WHERE listings.is_deleted = 0
           ORDER BY listings.listing_date DESC"""
    ).fetchall()
    conn.close()
    listings = []
    for row in rows:
        listing = dict(row)
        try:
            images = json.loads(listing["image"])
            if isinstance(images, list) and len(images) > 0:
                listing["images"] = images
                listing["image"] = images[0]
            else:
                listing["images"] = [listing["image"]]
        except Exception:
            listing["images"] = [listing["image"]]
        listings.append(listing)
    return listings


def get_listing_by_id(listing_id):
    """Return a single listing by ID with seller info."""
    conn = get_db_connection()
    listing = conn.execute(
        """SELECT listings.id, listings.title, listings.description,
           listings.price, listings.category,
           listings.item_condition AS condition,
           listings.image_url, listings.listing_date,
           listings.last_modified_timestamp, listings.is_deleted,
           users.display_name AS seller_display_name,
           users.email AS seller_email,
           users.contact_number AS seller_contact_number
           FROM listings
           LEFT JOIN users ON listings.seller_id = users.id
           WHERE listings.id = ?""",
        (listing_id,)
    ).fetchone()
    conn.close()
    if listing is None:
        return None
    listing = dict(listing)
    try:
        images = json.loads(listing["image_url"])
        if isinstance(images, list) and len(images) > 0:
            listing["images"] = images
            listing["image"] = images[0]
        else:
            listing["images"] = [listing["image_url"]]
            listing["image"] = listing["image_url"]
    except Exception:
        listing["images"] = [listing["image_url"]]
        listing["image"] = listing["image_url"]
    return listing


# ── Reporting (US1-US4) ───────────────────────────────────────────────────────

REPORT_REASONS = [
    'Prohibited Item',
    'Misleading Description',
    'Spam or Duplicate',
    'Inappropriate Content',
    'Suspected Scam',
    'Other'
]


def create_report(listing_id, reporter_id, reason, description):
    """Insert a new report into the database."""
    conn = get_db_connection()
    conn.execute(
        """INSERT INTO reports (listing_id, reporter_id, reason, description)
           VALUES (?, ?, ?, ?)""",
        (listing_id, reporter_id, reason, description)
    )
    conn.commit()
    conn.close()


def get_all_reports():
    """Return all reports with listing and reporter info."""
    conn = get_db_connection()
    rows = conn.execute(
        """SELECT reports.id, reports.reason, reports.description,
           reports.status, reports.created_at, reports.listing_id,
           listings.title AS listing_title,
           listings.is_deleted AS listing_is_deleted,
           reports.reporter_id,
           users.display_name AS reporter_name
           FROM reports
           LEFT JOIN listings ON reports.listing_id = listings.id
           LEFT JOIN users ON reports.reporter_id = users.id
           ORDER BY reports.created_at DESC"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_report_by_id(report_id):
    """Return a single report by ID."""
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM reports WHERE id = ?", (report_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def soft_delete_listing(listing_id):
    """Soft-delete a listing and mark its reports as Actioned."""
    conn = get_db_connection()
    conn.execute(
        "UPDATE listings SET is_deleted = 1 WHERE id = ?", (listing_id,)
    )
    conn.execute(
        "UPDATE reports SET status = 'Actioned' WHERE listing_id = ?",
        (listing_id,)
    )
    conn.commit()
    conn.close()


def dismiss_report(report_id):
    """Mark a report as Dismissed."""
    conn = get_db_connection()
    conn.execute(
        "UPDATE reports SET status = 'Dismissed' WHERE id = ?", (report_id,)
    )
    conn.commit()
    conn.close()


# ── User Management (US5-US8) ─────────────────────────────────────────────────

def get_all_users():
    """Return all users for admin management."""
    conn = get_db_connection()
    rows = conn.execute(
        """SELECT id, student_id, first_name, last_name, display_name,
           email, contact_number, role, status, created_at
           FROM users ORDER BY created_at DESC"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def toggle_user_status(user_id):
    """Toggle a user's status between Active and Suspended."""
    conn = get_db_connection()
    user = conn.execute(
        "SELECT status, role FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if user is None:
        conn.close()
        return None
    new_status = 'Suspended' if user['status'] == 'Active' else 'Active'
    conn.execute(
        "UPDATE users SET status = ? WHERE id = ?", (new_status, user_id)
    )
    conn.commit()
    conn.close()
    return new_status
