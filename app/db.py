import sqlite3
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

    
    conn.commit()
    conn.close()

   


def create_listing(seller_id, title, description, price, category, condition, image_url):
    conn = get_db_connection()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor = conn.execute("""
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
    """, (
        seller_id,
        title,
        description,
        price,
        category,
        condition,
        image_url,
        now,
        now
    ))

    conn.commit()

    listing_id = cursor.lastrowid

    cursor = conn.execute("""
        SELECT *
        FROM listings
        WHERE id = ?
    """, (listing_id,))

    row = cursor.fetchone()

    listing = dict(row)

    conn.close()

    return listing

def get_all_listings():
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

    return [dict(row) for row in rows]


## API ROUTE for returning the listing, use 
##"condition" : listing["item_condition"]