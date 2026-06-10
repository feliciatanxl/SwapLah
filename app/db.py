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
    conn.execute("""
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
            FOREIGN KEY (seller_id) REFERENCES users (id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER NOT NULL,
            buyer_id INTEGER NOT NULL,
            offer_type TEXT NOT NULL CHECK(offer_type IN ('cash', 'swap')),
            proposed_price REAL,
            swap_listing_id INTEGER,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (listing_id) REFERENCES listings (id),
            FOREIGN KEY (buyer_id) REFERENCES users (id),
            FOREIGN KEY (swap_listing_id) REFERENCES listings (id)
        )
    """)

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


def create_listing(seller_id, title, description, price, category, condition, image_url):
    """Insert a new listing and return it as a dict."""
    conn = get_db_connection()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor = conn.execute(
        """
        INSERT INTO listings (
            seller_id,
            title,
            description,
            price,
            category,
            item_condition,
            image_url,
            listing_date,
            last_modified_timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            seller_id,
            title,
            description,
            price,
            category,
            condition,
            image_url,
            now,
            now
        )
    )

    conn.commit()

    listing_id = cursor.lastrowid

    listing = conn.execute(
        """
        SELECT *
        FROM listings
        WHERE id = ?
        """,
        (listing_id,)
    ).fetchone()

    conn.close()

    return dict(listing)


def get_all_listings():
    """Return all listings with seller display name, newest first."""
    conn = get_db_connection()

    rows = conn.execute(
        """
        SELECT
            listings.id,
            listings.title,
            listings.description,
            listings.price,
            listings.category,
            listings.item_condition AS condition,
            listings.image_url AS image,
            listings.listing_date,
            users.display_name AS seller
        FROM listings
        LEFT JOIN users ON listings.seller_id = users.id
        ORDER BY listings.listing_date DESC
        """
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


## feature/view-listing-details
def get_listing_by_id(listing_id):
    """Return full listing detail by ID, or None if not found."""
    conn = get_db_connection()

    listing = conn.execute(
        """
        SELECT
            listings.id,
            listings.title,
            listings.description,
            listings.price,
            listings.category,
            listings.item_condition AS condition,
            listings.image_url,
            listings.listing_date,
            listings.last_modified_timestamp,
            users.display_name AS seller_display_name,
            users.email AS seller_email,
            users.contact_number AS seller_contact_number
        FROM listings
        LEFT JOIN users ON listings.seller_id = users.id
        WHERE listings.id = ?
        """,
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


## feature/update-account-details
def get_user_by_id(user_id):
    """Retrieve one user by ID using a parameterized query."""
    conn = get_db_connection()
    user = conn.execute(
        "SELECT id, student_id, first_name, last_name, display_name, email, contact_number, role, status, created_at FROM users WHERE id = :user_id",
        {"user_id": user_id},
    ).fetchone()
    conn.close()

    if user is None:
        return None

    return dict(user)


def update_user_account(user_id, first_name, last_name, display_name, contact_number, password_hash=None):
    """Update editable account details only. Email and Student ID remain locked."""
    conn = get_db_connection()

    if password_hash:
        conn.execute(
            """
            UPDATE users
            SET first_name = :first_name,
                last_name = :last_name,
                display_name = :display_name,
                contact_number = :contact_number,
                password_hash = :password_hash
            WHERE id = :user_id
            """,
            {
                "first_name": first_name,
                "last_name": last_name,
                "display_name": display_name,
                "contact_number": contact_number,
                "password_hash": password_hash,
                "user_id": user_id,
            },
        )
    else:
        conn.execute(
            """
            UPDATE users
            SET first_name = :first_name,
                last_name = :last_name,
                display_name = :display_name,
                contact_number = :contact_number
            WHERE id = :user_id
            """,
            {
                "first_name": first_name,
                "last_name": last_name,
                "display_name": display_name,
                "contact_number": contact_number,
                "user_id": user_id,
            },
        )

    conn.commit()
    conn.close()


## feature/submit-offer
def get_listing_owner(listing_id):
    """Return the seller_id for a given listing, or None if listing doesn't exist."""
    conn = get_db_connection()
    row = conn.execute(
        "SELECT seller_id FROM listings WHERE id = ?",
        (listing_id,)
    ).fetchone()
    conn.close()
    return row["seller_id"] if row else None


def get_active_listing_by_buyer(listing_id, buyer_id):
    """
    Return the listing if it exists and belongs to buyer_id, else None.
    (All listings are currently considered active; extend with a status column as needed.)
    """
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM listings WHERE id = ? AND seller_id = ?",
        (listing_id, buyer_id)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def create_offer(listing_id, buyer_id, offer_type, proposed_price=None, swap_listing_id=None):
    """Insert a new offer and return it as a dict."""
    conn = get_db_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.execute(
        """
        INSERT INTO offers (listing_id, buyer_id, offer_type, proposed_price, swap_listing_id, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'Pending', ?)
        """,
        (listing_id, buyer_id, offer_type, proposed_price, swap_listing_id, now)
    )
    conn.commit()
    offer_id = cursor.lastrowid
    offer = conn.execute("SELECT * FROM offers WHERE id = ?", (offer_id,)).fetchone()
    conn.close()
    return dict(offer)

## feature/manage-received-offers

def get_offers_for_seller(seller_id):
    """Return all offers grouped by listing for a given seller."""
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT
            o.id,
            o.listing_id,
            o.buyer_id,
            o.offer_type,
            o.proposed_price,
            o.swap_listing_id,
            o.status,
            o.created_at,
            l.title        AS listing_title,
            l.category     AS listing_category,
            l.price        AS listing_price,
            u.display_name AS buyer_display_name,
            sl.title       AS swap_listing_title
        FROM offers o
        JOIN listings l  ON o.listing_id      = l.id
        JOIN users    u  ON o.buyer_id         = u.id
        LEFT JOIN listings sl ON o.swap_listing_id = sl.id
        WHERE l.seller_id = :seller_id
        ORDER BY o.created_at DESC
        """,
        {"seller_id": seller_id},
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_offer_by_id(offer_id):
    """Return a single offer row as a dict, or None."""
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM offers WHERE id = ?", (offer_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def accept_offer(offer_id):
    """
    Accept one offer and reject all other Pending offers for the same listing.
    Also creates a transaction record.
    Returns the updated offer dict, or None if the offer was not found.
    """
    conn = get_db_connection()

    offer = conn.execute(
        "SELECT * FROM offers WHERE id = ?", (offer_id,)
    ).fetchone()

    if offer is None:
        conn.close()
        return None

    listing_id = offer["listing_id"]

    # Accept the chosen offer
    conn.execute(
        "UPDATE offers SET status = 'Accepted' WHERE id = ?", (offer_id,)
    )

    # Reject every other Pending offer for the same listing
    conn.execute(
        """
        UPDATE offers
        SET status = 'Rejected'
        WHERE listing_id = ? AND id != ? AND status = 'Pending'
        """,
        (listing_id, offer_id),
    )

    # Create transaction record
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            offer_id   INTEGER NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (offer_id) REFERENCES offers (id)
        )
        """
    )
    conn.execute(
        "INSERT INTO transactions (offer_id) VALUES (?)", (offer_id,)
    )

    conn.commit()
    updated = conn.execute(
        "SELECT * FROM offers WHERE id = ?", (offer_id,)
    ).fetchone()
    conn.close()
    return dict(updated)


def reject_offer(offer_id):
    """
    Reject a single offer.
    Returns the updated offer dict, or None if the offer was not found.
    """
    conn = get_db_connection()

    offer = conn.execute(
        "SELECT * FROM offers WHERE id = ?", (offer_id,)
    ).fetchone()

    if offer is None:
        conn.close()
        return None

    conn.execute(
        "UPDATE offers SET status = 'Rejected' WHERE id = ?", (offer_id,)
    )
    conn.commit()
    updated = conn.execute(
        "SELECT * FROM offers WHERE id = ?", (offer_id,)
    ).fetchone()
    conn.close()
    return dict(updated)

## feature/transaction-history

def get_transactions_for_user(user_id):
    """
    Return all completed transactions where the user was the buyer or seller.
    Each row includes offer and listing details for display.
    """
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT
            t.id              AS transaction_id,
            t.created_at      AS transaction_date,
            o.id              AS offer_id,
            o.offer_type,
            o.proposed_price,
            o.swap_listing_id,
            o.buyer_id,
            o.listing_id,
            l.title           AS listing_title,
            l.category        AS listing_category,
            l.price           AS listing_price,
            l.seller_id,
            buyer.display_name  AS buyer_display_name,
            seller.display_name AS seller_display_name,
            sl.title          AS swap_listing_title
        FROM transactions t
        JOIN offers   o   ON t.offer_id        = o.id
        JOIN listings l   ON o.listing_id      = l.id
        JOIN users    buyer  ON o.buyer_id     = buyer.id
        JOIN users    seller ON l.seller_id    = seller.id
        LEFT JOIN listings sl ON o.swap_listing_id = sl.id
        WHERE o.buyer_id = :user_id OR l.seller_id = :user_id
        ORDER BY t.created_at DESC
        """,
        {"user_id": user_id},
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]