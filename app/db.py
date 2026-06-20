import json
import sqlite3
from datetime import datetime
from pathlib import Path

DATABASE = Path(__file__).resolve().parent.parent / "swaplah.db"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

CREATE_USERS_TABLE_SQL = """
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

CREATE_LISTINGS_TABLE_SQL = """
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
    status TEXT NOT NULL DEFAULT 'Active',
    FOREIGN KEY (seller_id) REFERENCES users (id)
)
"""

CREATE_OFFERS_TABLE_SQL = """
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
"""

INSERT_LISTING_SQL = """
INSERT INTO listings (
    seller_id, title, description, price, category, item_condition,
    image_url, listing_date, last_modified_timestamp
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

ACTIVE_LISTINGS_SQL = """
SELECT
    listings.id,
    listings.title,
    listings.description,
    listings.price,
    listings.category,
    listings.item_condition AS condition,
    listings.image_url,
    listings.listing_date,
    users.display_name AS seller
FROM listings
LEFT JOIN users ON listings.seller_id = users.id
WHERE listings.status = 'Active'
ORDER BY listings.listing_date DESC
"""

LISTING_DETAIL_SQL = """
SELECT
    listings.id,
    listings.seller_id,
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
AND listings.status = 'Active'
"""

UPDATE_LISTING_SQL = """
UPDATE listings
SET title = ?,
    description = ?,
    price = ?,
    category = ?,
    item_condition = ?,
    image_url = ?,
    last_modified_timestamp = ?
WHERE id = ?
AND seller_id = ?
AND status = 'Active'
"""

SOFT_DELETE_LISTING_SQL = """
UPDATE listings
SET status = 'Deleted',
    last_modified_timestamp = ?
WHERE id = ?
AND seller_id = ?
AND status = 'Active'
"""

GET_USER_BY_ID_SQL = """
SELECT
    id,
    student_id,
    first_name,
    last_name,
    display_name,
    email,
    contact_number,
    role,
    status,
    created_at
FROM users
WHERE id = :user_id
"""

UPDATE_USER_WITH_PASSWORD_SQL = """
UPDATE users
SET first_name = :first_name,
    last_name = :last_name,
    display_name = :display_name,
    contact_number = :contact_number,
    password_hash = :password_hash
WHERE id = :user_id
"""

UPDATE_USER_SQL = """
UPDATE users
SET first_name = :first_name,
    last_name = :last_name,
    display_name = :display_name,
    contact_number = :contact_number
WHERE id = :user_id
"""


def get_db_connection():
    """Return a SQLite database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def _now():
    """Return the current timestamp string used by listing records."""
    return datetime.now().strftime(DATETIME_FORMAT)


def init_db():
    """Create database tables if they do not exist."""
    conn = get_db_connection()
    conn.execute(CREATE_USERS_TABLE_SQL)
    conn.execute(CREATE_LISTINGS_TABLE_SQL)
    ensure_listing_status_column(conn)
    conn.execute(CREATE_OFFERS_TABLE_SQL)
    conn.commit()
    conn.close()


def get_user_by_email(email):
    """Retrieve one user by email using a parameterized query."""
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = :email", {"email": email}).fetchone()
    conn.close()
    return user


def _fetch_listing(conn, listing_id):
    """Return a raw listing row by ID."""
    return conn.execute("SELECT * FROM listings WHERE id = ?", (listing_id,)).fetchone()


def _decode_images(raw_image):
    """Return a list of images from a JSON image string or a plain URL."""
    try:
        images = json.loads(raw_image)
        if isinstance(images, list) and images:
            return images
    except Exception:
        pass
    return [raw_image]


def _attach_images(listing):
    """Add image and images keys to a listing dictionary."""
    images = _decode_images(listing["image_url"])
    listing["images"] = images
    listing["image"] = images[0]
    return listing


def create_listing(  # pylint: disable=too-many-positional-arguments
    seller_id,
    title,
    description,
    price,
    category,
    condition,
    image_url,
):
    """Insert a new listing and return it as a dict."""
    conn = get_db_connection()
    now = _now()
    values = (seller_id, title, description, price, category, condition, image_url, now, now)
    cursor = conn.execute(INSERT_LISTING_SQL, values)
    conn.commit()
    listing = _fetch_listing(conn, cursor.lastrowid)
    conn.close()
    return dict(listing)


def get_all_listings():
    """Return all listings with seller display name, newest first."""
    conn = get_db_connection()
    rows = conn.execute(ACTIVE_LISTINGS_SQL).fetchall()
    conn.close()
    return [_attach_images(dict(row)) for row in rows]


def get_listing_by_id(listing_id):
    """Return full listing detail by ID, or None if not found."""
    conn = get_db_connection()
    listing = conn.execute(LISTING_DETAIL_SQL, (listing_id,)).fetchone()
    conn.close()

    if listing is None:
        return None

    return _attach_images(dict(listing))


def ensure_listing_status_column(conn):
    """Add the listing status column if it does not already exist."""
    columns = conn.execute("PRAGMA table_info(listings)").fetchall()
    column_names = [column["name"] for column in columns]

    if "status" not in column_names:
        conn.execute("ALTER TABLE listings ADD COLUMN status TEXT NOT NULL DEFAULT 'Active'")


def _get_active_listing(conn, listing_id):
    """Return an active listing row by ID."""
    return conn.execute(
        "SELECT * FROM listings WHERE id = ? AND status = 'Active'",
        (listing_id,),
    ).fetchone()


def _listing_update_values(listing_id, seller_id, fields):
    """Return ordered SQL values for updating a listing."""
    return (
        fields["title"],
        fields["description"],
        fields["price"],
        fields["category"],
        fields["condition"],
        fields["image_url"],
        _now(),
        listing_id,
        seller_id,
    )


def update_listing(  # pylint: disable=too-many-positional-arguments
    listing_id,
    seller_id,
    title,
    description,
    price,
    category,
    condition,
    image_url,
):
    """Update an active listing owned by the seller."""
    conn = get_db_connection()
    existing_listing = _get_active_listing(conn, listing_id)

    if existing_listing is None:
        conn.close()
        return None, "not_found"

    if existing_listing["seller_id"] != seller_id:
        conn.close()
        return None, "forbidden"

    fields = {
        "title": title,
        "description": description,
        "price": price,
        "category": category,
        "condition": condition,
        "image_url": image_url,
    }
    conn.execute(UPDATE_LISTING_SQL, _listing_update_values(listing_id, seller_id, fields))
    conn.commit()
    updated_listing = _fetch_listing(conn, listing_id)
    conn.close()
    return dict(updated_listing), None

def soft_delete_listing(listing_id, seller_id):
    """Soft-delete an active listing owned by the seller."""
    conn = get_db_connection()
    existing_listing = _fetch_listing(conn, listing_id)

    if existing_listing is None:
        conn.close()
        return None, "not_found"

    if existing_listing["status"] == "Deleted":
        conn.close()
        return None, "not_found"

    if existing_listing["seller_id"] != seller_id:
        conn.close()
        return None, "forbidden"

    conn.execute(SOFT_DELETE_LISTING_SQL, (_now(), listing_id, seller_id))
    conn.commit()
    deleted_listing = _fetch_listing(conn, listing_id)
    conn.close()

    return dict(deleted_listing), None

def search_active_listings(keyword=""):
    """Return active listings matching keyword in title or description."""
    conn = get_db_connection()
    search = keyword.strip()

    if search:
        pattern = f"%{search}%"
        rows = conn.execute(
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
                users.display_name AS seller
            FROM listings
            LEFT JOIN users ON listings.seller_id = users.id
            WHERE listings.status = 'Active'
            AND (
                LOWER(listings.title) LIKE LOWER(?)
                OR LOWER(listings.description) LIKE LOWER(?)
            )
            ORDER BY listings.listing_date DESC
            """,
            (pattern, pattern),
        ).fetchall()
    else:
        rows = conn.execute(ACTIVE_LISTINGS_SQL).fetchall()

    conn.close()
    return [_attach_images(dict(row)) for row in rows]

def get_user_by_id(user_id):
    """Retrieve one user by ID using a parameterized query."""
    conn = get_db_connection()
    user = conn.execute(GET_USER_BY_ID_SQL, {"user_id": user_id}).fetchone()
    conn.close()
    return None if user is None else dict(user)


def _account_update_values(profile, password_hash):
    """Return named values for updating editable account details."""
    values = dict(profile)

    if password_hash:
        values["password_hash"] = password_hash

    return values


def update_user_account(  # pylint: disable=too-many-positional-arguments
    user_id,
    first_name,
    last_name,
    display_name,
    contact_number,
    password_hash=None,
):
    """Update editable account details only. Email and Student ID remain locked."""
    conn = get_db_connection()
    query = UPDATE_USER_WITH_PASSWORD_SQL if password_hash else UPDATE_USER_SQL
    profile = {
        "first_name": first_name,
        "last_name": last_name,
        "display_name": display_name,
        "contact_number": contact_number,
        "user_id": user_id,
    }
    conn.execute(query, _account_update_values(profile, password_hash))
    conn.commit()
    conn.close()


def get_listing_owner(listing_id):
    """Return the seller_id for a given listing, or None if listing doesn't exist."""
    conn = get_db_connection()
    row = conn.execute("SELECT seller_id FROM listings WHERE id = ?", (listing_id,)).fetchone()
    conn.close()
    return row["seller_id"] if row else None


def get_listings_by_seller(seller_id):
    """Return all listings belonging to seller_id for swap dropdown."""
    conn = get_db_connection()
    rows = conn.execute("SELECT id, title FROM listings WHERE seller_id = ?", (seller_id,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_active_listing_by_buyer(listing_id, buyer_id):
    """Return the listing if it exists and belongs to buyer_id, else None."""
    conn = get_db_connection()
    row = conn.execute(
    """
    SELECT *
    FROM listings
    WHERE id = ?
    AND seller_id = ?
    AND status = 'Active'
    """,
    (listing_id, buyer_id),
).fetchone() ## prevents deleted listings from being used in swap/offer logic
    conn.close()
    return dict(row) if row else None


def create_offer(listing_id, buyer_id, offer_type, proposed_price=None, swap_listing_id=None):
    """Insert a new offer and return it as a dict."""
    conn = get_db_connection()
    cursor = conn.execute(
        """
        INSERT INTO offers (listing_id, buyer_id, offer_type, proposed_price, swap_listing_id, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'Pending', ?)
        """,
        (listing_id, buyer_id, offer_type, proposed_price, swap_listing_id, _now()),
    )
    conn.commit()
    offer = conn.execute("SELECT * FROM offers WHERE id = ?", (cursor.lastrowid,)).fetchone()
    conn.close()

    return dict(offer)
