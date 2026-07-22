"""
API integration tests for:
  PATCH /api/offers/<id>/accept  (auto-reject of other pending offers)
  PATCH /api/offers/<id>/reject

Uses a real temporary SQLite database with seeded users, listings, and offers
so the actual SQL in accept_offer()/reject_offer() is exercised end to end,
not just monkeypatched.
"""
import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "test_accept_reject.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client, test_db


def seed_listing_with_offers(test_db, offer_count=2):
    """
    Seed one seller, one listing owned by the seller, and `offer_count`
    pending cash offers on that listing from distinct buyers.

    Returns the list of created offer ids in insertion order.
    """
    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row

    conn.execute(
        """
        INSERT INTO users (student_id, first_name, last_name, display_name,
                           email, contact_number, password_hash, role, status)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        ("S11111111", "Alice", "Seller", "AliceSeller",
         "alice@mymail.nyp.edu.sg", "91111111",
         generate_password_hash("Password1"), "user", "Active"),
    )

    now = "2026-06-09 10:00:00"
    conn.execute(
        """
        INSERT INTO listings (seller_id, title, description, price, category,
                              item_condition, image_url, listing_date, last_modified_timestamp)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (1, "Seller Item", "A nice item", "50.00", "Electronics",
         "Good", '["https://example.com/img.jpg"]', now, now),
    )
    listing_id = conn.execute("SELECT id FROM listings WHERE seller_id = 1").fetchone()["id"]

    offer_ids = []
    for i in range(offer_count):
        buyer_student_id = f"S2000000{i}"
        conn.execute(
            """
            INSERT INTO users (student_id, first_name, last_name, display_name,
                               email, contact_number, password_hash, role, status)
            VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (buyer_student_id, "Buyer", str(i), f"Buyer{i}",
             f"buyer{i}@mymail.nyp.edu.sg", f"9200000{i}",
             generate_password_hash("Password2"), "user", "Active"),
        )
        buyer_id = conn.execute(
            "SELECT id FROM users WHERE student_id = ?", (buyer_student_id,)
        ).fetchone()["id"]

        cursor = conn.execute(
            """
            INSERT INTO offers (listing_id, buyer_id, offer_type, proposed_price,
                                swap_listing_id, status, created_at)
            VALUES (?, ?, 'cash', ?, NULL, 'Pending', ?)
            """,
            (listing_id, buyer_id, 40.0 + i, now),
        )
        offer_ids.append(cursor.lastrowid)

    conn.commit()
    conn.close()
    return listing_id, offer_ids


def login_as_seller(test_client):
    """Authenticate the test client as the seeded seller (user id=1)."""
    with test_client.session_transaction() as sess:
        sess["user_id"] = 1


def get_offer_status(test_db, offer_id):
    """Return the status column of an offer row directly from the database."""
    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT status FROM offers WHERE id = ?", (offer_id,)).fetchone()
    conn.close()
    return row["status"]


def get_listing_status(test_db, listing_id):
    """Return the status column of a listing row directly from the database."""
    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT status FROM listings WHERE id = ?", (listing_id,)).fetchone()
    conn.close()
    return row["status"]


def get_transaction_count(test_db, offer_id):
    """Return how many transaction rows reference a given offer id."""
    conn = sqlite3.connect(test_db)
    row = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE offer_id = ?", (offer_id,)
    ).fetchone()
    conn.close()
    return row[0]


# ===========================================================================
# Auto-reject on accept — multiple pending offers
# ===========================================================================

def test_accept_offer_auto_rejects_other_pending_offers(client):
    """AC1 (auto-reject): accepting one offer rejects all other pending offers."""
    test_client, test_db = client
    listing_id, offer_ids = seed_listing_with_offers(test_db, offer_count=3)
    login_as_seller(test_client)

    accepted_id, other_id_1, other_id_2 = offer_ids

    response = test_client.patch(f"/api/offers/{accepted_id}/accept")

    assert response.status_code == 200
    assert get_offer_status(test_db, accepted_id) == "Accepted"
    assert get_offer_status(test_db, other_id_1) == "Rejected"
    assert get_offer_status(test_db, other_id_2) == "Rejected"


def test_accept_offer_only_one_accepted_for_listing(client):
    """AC2 (auto-reject): only one offer ends up Accepted for the listing."""
    test_client, test_db = client
    _, offer_ids = seed_listing_with_offers(test_db, offer_count=3)
    login_as_seller(test_client)

    test_client.patch(f"/api/offers/{offer_ids[0]}/accept")

    conn = sqlite3.connect(test_db)
    accepted_count = conn.execute(
        "SELECT COUNT(*) FROM offers WHERE status = 'Accepted'"
    ).fetchone()[0]
    conn.close()

    assert accepted_count == 1


def test_accept_only_pending_offer_touches_nothing_else(client):
    """AC3 (auto-reject): a single pending offer accepted doesn't alter other records."""
    test_client, test_db = client
    listing_id, offer_ids = seed_listing_with_offers(test_db, offer_count=1)
    login_as_seller(test_client)

    response = test_client.patch(f"/api/offers/{offer_ids[0]}/accept")

    assert response.status_code == 200
    assert get_offer_status(test_db, offer_ids[0]) == "Accepted"
    # Listing correctly marked unavailable, transaction recorded — nothing else changed.
    assert get_listing_status(test_db, listing_id) == "Sold"
    assert get_transaction_count(test_db, offer_ids[0]) == 1


# ===========================================================================
# Reject — single offer, real database
# ===========================================================================

def test_reject_offer_marks_only_target_offer(client):
    """AC1 (reject): rejecting one offer marks only that offer as Rejected."""
    test_client, test_db = client
    _, offer_ids = seed_listing_with_offers(test_db, offer_count=2)
    login_as_seller(test_client)

    target_id, other_id = offer_ids

    response = test_client.patch(f"/api/offers/{target_id}/reject")

    assert response.status_code == 200
    assert get_offer_status(test_db, target_id) == "Rejected"


def test_reject_offer_does_not_affect_other_pending_offers(client):
    """AC3 (reject): other pending offers for the listing remain unchanged."""
    test_client, test_db = client
    _, offer_ids = seed_listing_with_offers(test_db, offer_count=2)
    login_as_seller(test_client)

    target_id, other_id = offer_ids

    test_client.patch(f"/api/offers/{target_id}/reject")

    assert get_offer_status(test_db, other_id) == "Pending"


def test_reject_offer_non_owner_forbidden(client):
    """AC2 (reject): a user who does not own the listing cannot reject its offers."""
    test_client, test_db = client
    _, offer_ids = seed_listing_with_offers(test_db, offer_count=1)

    # Log in as a different user who isn't the seller.
    with test_client.session_transaction() as sess:
        sess["user_id"] = 999

    response = test_client.patch(f"/api/offers/{offer_ids[0]}/reject")

    assert response.status_code == 403
    assert get_offer_status(test_db, offer_ids[0]) == "Pending"