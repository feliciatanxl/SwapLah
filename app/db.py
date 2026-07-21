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

CREATE_TRANSACTIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    offer_id INTEGER NOT NULL,
    listing_id INTEGER NOT NULL,
    seller_id INTEGER NOT NULL,
    buyer_id INTEGER NOT NULL,
    transaction_type TEXT NOT NULL,
    amount REAL,
    swap_listing_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (offer_id) REFERENCES offers (id),
    FOREIGN KEY (listing_id) REFERENCES listings (id),
    FOREIGN KEY (seller_id) REFERENCES users (id),
    FOREIGN KEY (buyer_id) REFERENCES users (id),
    FOREIGN KEY (swap_listing_id) REFERENCES listings (id)
)
"""

OFFERS_FOR_SELLER_SQL = """
SELECT
    offers.id,
    offers.listing_id,
    offers.buyer_id,
    offers.offer_type,
    offers.proposed_price,
    offers.swap_listing_id,
    offers.status,
    offers.created_at,
    listings.title AS listing_title,
    listings.category AS listing_category,
    listings.price AS listing_price,
    buyer.display_name AS buyer_display_name,
    swap_listing.title AS swap_listing_title
FROM offers
JOIN listings ON offers.listing_id = listings.id
JOIN users AS buyer ON offers.buyer_id = buyer.id
LEFT JOIN listings AS swap_listing ON offers.swap_listing_id = swap_listing.id
WHERE listings.seller_id = ?
ORDER BY offers.created_at DESC
"""

CREATE_REVIEWS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reviewed_user_id INTEGER NOT NULL,
    reviewer_id INTEGER,
    rating INTEGER NOT NULL,
    comment TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reviewed_user_id) REFERENCES users (id),
    FOREIGN KEY (reviewer_id) REFERENCES users (id)
)
"""
CREATE_REPORTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    reporter_id INTEGER NOT NULL,
    reason TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (listing_id) REFERENCES listings (id),
    FOREIGN KEY (reporter_id) REFERENCES users (id)
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
CREATE_REPORT_SQL = """
INSERT INTO reports (listing_id, reporter_id, reason, description)
VALUES (?, ?, ?, ?)
"""

GET_REPORT_BY_ID_SQL = """
SELECT r.*, l.title, l.status as listing_status, l.seller_id
FROM reports r
JOIN listings l ON r.listing_id = l.id
WHERE r.id = ?
"""

ADMIN_DELETE_REPORTED_LISTING_SQL = """
UPDATE listings 
SET status = 'Deleted', 
    last_modified_timestamp = ? 
WHERE id = ? AND status = 'Active'
"""

RESOLVE_REPORT_SQL = """
UPDATE reports SET status = 'Resolved' WHERE id = ?
"""

def get_db_connection():
    """Return a SQLite database connection."""
    conn = sqlite3.connect(DATABASE, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=10000")
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
    conn.execute(CREATE_TRANSACTIONS_TABLE_SQL)
    conn.execute(CREATE_REVIEWS_TABLE_SQL)
    conn.execute(CREATE_REPORTS_TABLE_SQL) 
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

def _active_listing_search_filters(keyword="", category="", condition=""):
    """Return SQL clauses and parameters for active listing filters."""
    clauses = ["listings.status = 'Active'"]
    params = []
    search = keyword.strip()

    if search:
        pattern = f"%{search}%"
        clauses.append(
            """
            (
                LOWER(listings.title) LIKE LOWER(?)
                OR LOWER(listings.description) LIKE LOWER(?)
            )
            """
        )
        params.extend([pattern, pattern])

    if category:
        clauses.append("listings.category = ?")
        params.append(category)

    if condition:
        clauses.append("listings.item_condition = ?")
        params.append(condition)

    return " AND ".join(clauses), params


def _active_listing_search_sql(where_clause):
    """Return the active listing search SQL with the supplied WHERE clause."""
    return f"""
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
    WHERE {where_clause}
    ORDER BY listings.listing_date DESC
    """


def search_active_listings(keyword="", category="", condition=""):
    """Return active listings matching search, category, and condition filters."""
    conn = get_db_connection()
    where_clause, params = _active_listing_search_filters(
        keyword,
        category.strip(),
        condition.strip(),
    )
    rows = conn.execute(
        _active_listing_search_sql(where_clause),
        params,
    ).fetchall()

    conn.close()
    return [_attach_images(dict(row)) for row in rows]


def get_reviews_for_user(user_id):
    """Return public reviews for a user, newest first."""
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT
            reviews.id,
            reviews.reviewed_user_id,
            reviews.reviewer_id,
            reviews.rating,
            reviews.comment,
            reviews.created_at,
            users.display_name AS reviewer_display_name
        FROM reviews
        LEFT JOIN users ON reviews.reviewer_id = users.id
        WHERE reviews.reviewed_user_id = ?
        ORDER BY reviews.created_at DESC, reviews.id DESC
        """,
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]

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
    """Return active listings belonging to seller_id for swap dropdown."""
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT id, title
        FROM listings
        WHERE seller_id = ?
        AND status = 'Active'
        """,
        (seller_id,),
    ).fetchall()
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


def get_offers_for_seller(seller_id):
    """Return all offers received on listings owned by seller_id, newest first."""
    conn = get_db_connection()
    rows = conn.execute(OFFERS_FOR_SELLER_SQL, (seller_id,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_offer_by_id(offer_id):
    """Return a single offer by ID as a dict, or None if it doesn't exist."""
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM offers WHERE id = ?", (offer_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


TRANSACTIONS_FOR_BUYER_SQL = """
SELECT
    transactions.id,
    transactions.transaction_type,
    transactions.amount,
    transactions.created_at,
    listings.title AS listing_title,
    listings.category AS listing_category,
    seller.display_name AS counterparty_display_name
FROM transactions
JOIN listings ON transactions.listing_id = listings.id
JOIN users AS seller ON transactions.seller_id = seller.id
WHERE transactions.buyer_id = ?
ORDER BY transactions.created_at DESC
"""

TRANSACTIONS_FOR_SELLER_SQL = """
SELECT
    transactions.id,
    transactions.transaction_type,
    transactions.amount,
    transactions.created_at,
    listings.title AS listing_title,
    listings.category AS listing_category,
    buyer.display_name AS counterparty_display_name
FROM transactions
JOIN listings ON transactions.listing_id = listings.id
JOIN users AS buyer ON transactions.buyer_id = buyer.id
WHERE transactions.seller_id = ?
ORDER BY transactions.created_at DESC
"""


def get_transactions_for_user(user_id, role):
    """
    Return completed transactions for a user.

    role must be either 'buyer' or 'seller'. Each row includes the item,
    category, counterparty display name, transaction type, amount and date.
    """
    if role == "buyer":
        sql = TRANSACTIONS_FOR_BUYER_SQL
    elif role == "seller":
        sql = TRANSACTIONS_FOR_SELLER_SQL
    else:
        raise ValueError("role must be 'buyer' or 'seller'")

    conn = get_db_connection()
    rows = conn.execute(sql, (user_id,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def _create_transaction_for_offer(conn, offer):
    """Insert a transaction record for a just-accepted offer."""
    seller_id = conn.execute(
        "SELECT seller_id FROM listings WHERE id = ?", (offer["listing_id"],)
    ).fetchone()["seller_id"]

    conn.execute(
        """
        INSERT INTO transactions (
            offer_id, listing_id, seller_id, buyer_id,
            transaction_type, amount, swap_listing_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            offer["id"],
            offer["listing_id"],
            seller_id,
            offer["buyer_id"],
            offer["offer_type"],
            offer["proposed_price"],
            offer["swap_listing_id"],
        ),
    )


def reject_offer(offer_id):
    """Mark a single offer as Rejected and return the updated offer."""
    conn = get_db_connection()
    conn.execute("UPDATE offers SET status = 'Rejected' WHERE id = ?", (offer_id,))
    conn.commit()
    offer = conn.execute("SELECT * FROM offers WHERE id = ?", (offer_id,)).fetchone()
    conn.close()
    return dict(offer)


def accept_offer(offer_id):
    """
    Accept a pending offer.

    Marks the offer Accepted, auto-rejects other pending offers on the same
    listing, marks the listing as Sold (no longer available for new offers),
    and records a transaction for the accepted offer.
    """
    conn = get_db_connection()
    offer = conn.execute("SELECT * FROM offers WHERE id = ?", (offer_id,)).fetchone()
    offer = dict(offer)

    conn.execute("UPDATE offers SET status = 'Accepted' WHERE id = ?", (offer_id,))
    conn.execute(
        """
        UPDATE offers
        SET status = 'Rejected'
        WHERE listing_id = ? AND id != ? AND status = 'Pending'
        """,
        (offer["listing_id"], offer_id),
    )
    conn.execute(
        "UPDATE listings SET status = 'Sold' WHERE id = ?",
        (offer["listing_id"],),
    )
    _create_transaction_for_offer(conn, offer)

    conn.commit()
    updated_offer = conn.execute("SELECT * FROM offers WHERE id = ?", (offer_id,)).fetchone()
    conn.close()
    return dict(updated_offer)

def create_report(listing_id, reporter_id, reason, description=None):
    """Create a new report for a listing."""
    try:
        conn = get_db_connection()
        conn.execute(
            CREATE_REPORT_SQL,
            (listing_id, reporter_id, reason, description)
        )
        conn.commit()
        conn.close()
        return True, None
    except sqlite3.IntegrityError:
        return False, "integrity_error"
    except Exception:
        return False, "database_error"


def get_report_by_id(report_id):
    """Get report by ID with its listing details."""
    conn = get_db_connection()
    row = conn.execute(GET_REPORT_BY_ID_SQL, (report_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def admin_delete_reported_listing(report_id):
    """
    Admin soft-deletes the listing linked to a report.
    Marks the report as 'Resolved'.
    Returns (success_bool, error_code_string).
    """
    conn = None
    try:
        conn = get_db_connection()
        
        # Get the report and verify it exists and is pending
        report = conn.execute(
            "SELECT id, listing_id, status FROM reports WHERE id = ?",
            (report_id,)
        ).fetchone()
        
        if not report:
            return False, "not_found"
        
        if report["status"] != "Pending":
            return False, "not_found"
        
        listing_id = report["listing_id"]
        
        # Check if listing exists and is active
        listing = conn.execute(
            "SELECT id, status FROM listings WHERE id = ?",
            (listing_id,)
        ).fetchone()
        
        if not listing or listing["status"] != "Active":
            return False, "not_found"
        
        # Soft delete the listing
        conn.execute(
            ADMIN_DELETE_REPORTED_LISTING_SQL,
            (_now(), listing_id)
        )
        
        # Mark report as Resolved
        conn.execute(
            RESOLVE_REPORT_SQL,
            (report_id,)
        )
        
        conn.commit()
        return True, None
        
    except Exception:
        if conn:
            conn.rollback()
        return False, "database_error"
    finally:
        if conn:
            conn.close()

GET_ALL_REPORTS_SQL = """
SELECT 
    r.id,
    r.listing_id,
    r.reporter_id,
    r.reason,
    r.description,
    r.status,
    r.created_at,
    l.title AS listing_title,
    l.category AS listing_category,
    u.display_name AS reporter_display_name
FROM reports r
JOIN listings l ON r.listing_id = l.id
JOIN users u ON r.reporter_id = u.id
ORDER BY r.created_at DESC
"""


def get_all_reports():
    """Get all reports with listing and reporter details."""
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT 
            r.id,
            r.listing_id,
            r.reporter_id,
            r.reason,
            r.description,
            r.status,
            r.created_at,
            l.title as listing_title,
            l.status as listing_status,
            u.display_name as reporter_name
        FROM reports r
        JOIN listings l ON r.listing_id = l.id
        JOIN users u ON r.reporter_id = u.id
        ORDER BY r.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def dismiss_report(report_id):
    """
    Dismiss a pending report by setting its status to 'Dismissed'.
    
    Args:
        report_id: The ID of the report to dismiss
        
    Returns:
        (report_dict, None) on success
        (None, "not_found") if report doesn't exist or isn't pending
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if report exists and is pending
        cursor.execute(
            "SELECT * FROM reports WHERE id = ? AND status = 'Pending'",
            (report_id,)
        )
        report = cursor.fetchone()
        
        if not report:
            return None, "not_found"
        
        # Update status to Dismissed
        cursor.execute(
            "UPDATE reports SET status = 'Dismissed' WHERE id = ?",
            (report_id,)
        )
        conn.commit()
        
        # Fetch the updated report
        cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
        updated_report = cursor.fetchone()
        
        return dict(updated_report), None
        
    except Exception as e:
        print(f"Error dismissing report: {e}")
        return None, "database_error"
    finally:
        conn.close()