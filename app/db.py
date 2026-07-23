import json
import sqlite3
from datetime import datetime
from pathlib import Path

DATABASE = Path(__file__).resolve().parent.parent / "swaplah.db"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
LISTING_CATEGORIES = (
    {"label": "Textbooks", "icon": "bi-book"},
    {"label": "Electronics", "icon": "bi-laptop"},
    {"label": "Lab Equipment", "icon": "bi-prescription2"},
    {"label": "Stationery", "icon": "bi-pencil"},
    {"label": "Clothing", "icon": "bi-bag"},
)

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
    transaction_id INTEGER NOT NULL,
    reviewed_user_id INTEGER NOT NULL,
    reviewer_id INTEGER,
    rating INTEGER NOT NULL,
    comment TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES transactions (id),
    FOREIGN KEY (reviewed_user_id) REFERENCES users (id),
    FOREIGN KEY (reviewer_id) REFERENCES users (id)
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
    ensure_reviews_schema(conn)
    conn.execute(CREATE_REVIEWS_TABLE_SQL)
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


def get_listing_category_summary():
    """Return active listing counts for the configured listing categories."""
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT category, COUNT(*) AS count
        FROM listings
        WHERE status = 'Active'
        GROUP BY category
        """
    ).fetchall()
    total_row = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM listings
        WHERE status = 'Active'
        """
    ).fetchone()
    conn.close()

    category_counts = {row["category"]: row["count"] for row in rows}
    return {
        "total": total_row["total"] or 0,
        "category_rows": [
            {
                "label": category["label"],
                "icon": category["icon"],
                "count": category_counts.get(category["label"], 0),
            }
            for category in LISTING_CATEGORIES
        ],
    }


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


def ensure_reviews_schema(conn):
    """Rebuild the reviews table if it uses an outdated schema."""
    columns = conn.execute("PRAGMA table_info(reviews)").fetchall()
    column_names = [column["name"] for column in columns]
    is_outdated = column_names and (
        "reviewed_user_id" not in column_names or "transaction_id" not in column_names
    )

    if is_outdated:
        row_count = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        if row_count == 0:
            conn.execute("DROP TABLE reviews")


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


def get_active_listings_by_seller(seller_id):
    """Return active listing cards owned by one seller."""
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT
            id,
            title,
            description,
            price,
            category,
            item_condition AS condition,
            image_url,
            listing_date
        FROM listings
        WHERE seller_id = ?
        AND status = 'Active'
        ORDER BY listing_date DESC
        """,
        (seller_id,),
    ).fetchall()
    conn.close()
    return [_attach_images(dict(row)) for row in rows]


def get_sold_listings_by_seller(seller_id):
    """Return listings sold by one seller based on accepted offers."""
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
            listings.image_url,
            offers.created_at AS sold_at,
            offers.offer_type,
            offers.proposed_price,
            users.display_name AS buyer
        FROM offers
        INNER JOIN listings ON offers.listing_id = listings.id
        LEFT JOIN users ON offers.buyer_id = users.id
        WHERE listings.seller_id = ?
        AND offers.status = 'Accepted'
        ORDER BY offers.created_at DESC
        """,
        (seller_id,),
    ).fetchall()
    conn.close()
    return [_attach_images(dict(row)) for row in rows]


def _profile_stats_sql():
    """Return SQL for profile aggregate statistics."""
    return """
    SELECT
        COUNT(DISTINCT CASE WHEN listings.status = 'Active' THEN listings.id END) AS active_count,
        COUNT(DISTINCT CASE WHEN offers.status = 'Accepted' THEN offers.id END) AS total_sales,
        COUNT(DISTINCT offers.id) AS offer_count,
        COUNT(DISTINCT CASE WHEN offers.status != 'Pending' THEN offers.id END) AS responded_offer_count,
        COUNT(DISTINCT reviews.id) AS review_count,
        AVG(reviews.rating) AS average_rating
    FROM users
    LEFT JOIN listings ON listings.seller_id = users.id
    LEFT JOIN offers ON offers.listing_id = listings.id
    LEFT JOIN reviews ON reviews.reviewed_user_id = users.id
    WHERE users.id = ?
    """


def _get_profile_stats_row(user_id):
    """Return one profile aggregate stats row."""
    conn = get_db_connection()
    row = conn.execute(_profile_stats_sql(), (user_id,)).fetchone()
    conn.close()
    return row


def _trust_badge(total_sales, active_count):
    """Return the seller trust badge from sales and listing activity."""
    if total_sales >= 20:
        return "Top Seller"
    if total_sales >= 5:
        return "Trusted Seller"
    if active_count > 0:
        return "Active Seller"
    return "New Seller"


def _response_rate(row):
    """Return percentage of offers that have received a seller response."""
    offer_count = row["offer_count"] or 0
    if not offer_count:
        return None
    return round(((row["responded_offer_count"] or 0) / offer_count) * 100)


def get_user_profile_stats(user_id):
    """Return profile stats derived from marketplace and review data."""
    row = _get_profile_stats_row(user_id)
    active_count = row["active_count"] or 0
    total_sales = row["total_sales"] or 0

    return {
        "active_count": active_count,
        "review_count": row["review_count"] or 0,
        "average_rating": row["average_rating"],
        "total_sales": total_sales,
        "sold_count": total_sales,
        "trust_badge": _trust_badge(total_sales, active_count),
        "response_rate": _response_rate(row),
    }


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
            users.display_name AS reviewer_display_name,
            users.display_name AS reviewer_name
        FROM reviews
        LEFT JOIN users ON reviews.reviewer_id = users.id
        WHERE reviews.reviewed_user_id = ?
        ORDER BY reviews.created_at DESC, reviews.id DESC
        """,
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_user_rating_stats(user_id):
    """Return the average rating and review count received by a user."""
    conn = get_db_connection()
    row = conn.execute(
        """
        SELECT
            AVG(rating) AS average_rating,
            COUNT(*) AS review_count
        FROM reviews
        WHERE reviewed_user_id = ?
        """,
        (user_id,),
    ).fetchone()
    conn.close()

    review_count = row["review_count"]
    return {
        "average_rating": round(row["average_rating"], 1) if review_count > 0 else None,
        "review_count": review_count,
    }


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


def get_transaction_by_id(transaction_id):
    """Return a single completed transaction by ID, or None if it doesn't exist."""
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_review(transaction_id, reviewer_id, reviewed_user_id, rating, comment):
    """Insert a new review linked to a completed transaction and return it as a dict."""
    conn = get_db_connection()
    cursor = conn.execute(
        """
        INSERT INTO reviews (transaction_id, reviewer_id, reviewed_user_id, rating, comment)
        VALUES (?, ?, ?, ?, ?)
        """,
        (transaction_id, reviewer_id, reviewed_user_id, rating, comment),
    )
    conn.commit()
    review = conn.execute("SELECT * FROM reviews WHERE id = ?", (cursor.lastrowid,)).fetchone()
    conn.close()
    return dict(review)


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
