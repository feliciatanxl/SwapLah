"""API tests proving one review per reviewer per accepted offer."""

# pylint: disable=redefined-outer-name

import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app
from app.db import DuplicateReviewError, create_review


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a Flask test client backed by an isolated temporary database."""
    test_db = tmp_path / "test_review_duplicate.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client, test_db


def create_user(test_db, student_id, display_name):
    """Insert a user and return its ID."""
    conn = sqlite3.connect(test_db)
    cursor = conn.execute(
        """
        INSERT INTO users (student_id, first_name, last_name, display_name,
                           email, contact_number, password_hash, role, status)
        VALUES (?, ?, 'Test', ?, ?, '91234567', ?, 'user', 'Active')
        """,
        (student_id, display_name, display_name,
         f"{student_id.lower()}@mymail.nyp.edu.sg", generate_password_hash("Password1")),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def create_listing(test_db, seller_id, title="Item"):
    """Insert a listing and return its ID."""
    conn = sqlite3.connect(test_db)
    cursor = conn.execute(
        """
        INSERT INTO listings (seller_id, title, description, price, category,
                              item_condition, image_url, listing_date, last_modified_timestamp)
        VALUES (?, ?, 'desc', '20.00', 'Textbooks', 'Good', '[]',
                '2026-06-09 10:00:00', '2026-06-09 10:00:00')
        """,
        (seller_id, title),
    )
    conn.commit()
    listing_id = cursor.lastrowid
    conn.close()
    return listing_id


def create_accepted_offer(test_db, listing_id, buyer_id):
    """Insert an already-accepted offer and return its ID."""
    conn = sqlite3.connect(test_db)
    cursor = conn.execute(
        """
        INSERT INTO offers (listing_id, buyer_id, offer_type, proposed_price,
                            swap_listing_id, status, created_at)
        VALUES (?, ?, 'cash', 20.0, NULL, 'Accepted', '2026-06-09 10:00:00')
        """,
        (listing_id, buyer_id),
    )
    conn.commit()
    offer_id = cursor.lastrowid
    conn.close()
    return offer_id


def create_offer_with_status(test_db, listing_id, buyer_id, status):
    """Insert an offer with a specific status and return its ID."""
    conn = sqlite3.connect(test_db)
    cursor = conn.execute(
        """
        INSERT INTO offers (listing_id, buyer_id, offer_type, proposed_price,
                            swap_listing_id, status, created_at)
        VALUES (?, ?, 'cash', 20.0, NULL, ?, '2026-06-09 10:00:00')
        """,
        (listing_id, buyer_id, status),
    )
    conn.commit()
    offer_id = cursor.lastrowid
    conn.close()
    return offer_id


def seed_deal(test_db):
    """Seed a seller, buyer, listing and accepted offer; return their IDs."""
    seller_id = create_user(test_db, "S3100001", "Seller")
    buyer_id = create_user(test_db, "S3100002", "Buyer")
    listing_id = create_listing(test_db, seller_id, "Algorithms")
    offer_id = create_accepted_offer(test_db, listing_id, buyer_id)
    return seller_id, buyer_id, offer_id


def login_as(test_client, user_id):
    """Log a user into the test session."""
    with test_client.session_transaction() as sess:
        sess["user_id"] = user_id


def post_review(test_client, offer_id, rating=5, comment="ok"):
    """Post a review for an offer."""
    return test_client.post(
        "/api/reviews", json={"offer_id": offer_id, "rating": rating, "comment": comment}
    )


def test_buyer_can_review_seller_then_blocked_on_second(client):
    """A buyer reviews the seller once; a second attempt returns 409."""
    test_client, test_db = client
    _seller_id, buyer_id, offer_id = seed_deal(test_db)
    login_as(test_client, buyer_id)

    first = post_review(test_client, offer_id)
    assert first.status_code == 201

    second = post_review(test_client, offer_id, rating=3)
    assert second.status_code == 409
    assert second.get_json()["error"] == "You have already reviewed this transaction"


def test_seller_can_review_buyer_independently_of_buyer(client):
    """After the buyer reviews, the seller may still review the same offer once."""
    test_client, test_db = client
    seller_id, buyer_id, offer_id = seed_deal(test_db)

    login_as(test_client, buyer_id)
    assert post_review(test_client, offer_id).status_code == 201

    login_as(test_client, seller_id)
    assert post_review(test_client, offer_id).status_code == 201
    # Seller's own second attempt is blocked.
    assert post_review(test_client, offer_id).status_code == 409


def test_same_reviewer_can_review_a_different_accepted_offer(client):
    """A reviewer blocked on one offer may review a different accepted offer."""
    test_client, test_db = client
    seller_id, buyer_id, offer_id = seed_deal(test_db)
    second_listing = create_listing(test_db, seller_id, "Second Book")
    second_offer = create_accepted_offer(test_db, second_listing, buyer_id)

    login_as(test_client, buyer_id)
    assert post_review(test_client, offer_id).status_code == 201
    assert post_review(test_client, offer_id).status_code == 409
    assert post_review(test_client, second_offer).status_code == 201


@pytest.mark.parametrize("status", ["Pending", "Rejected"])
def test_non_accepted_offers_cannot_be_reviewed(client, status):
    """Only accepted offers can be reviewed."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S3100003", "Seller")
    buyer_id = create_user(test_db, "S3100004", "Buyer")
    listing_id = create_listing(test_db, seller_id)
    offer_id = create_offer_with_status(test_db, listing_id, buyer_id, status)

    login_as(test_client, buyer_id)
    assert post_review(test_client, offer_id).status_code == 400


def test_unrelated_user_cannot_review(client):
    """A user who is neither buyer nor seller cannot review."""
    test_client, test_db = client
    _seller_id, _buyer_id, offer_id = seed_deal(test_db)
    outsider = create_user(test_db, "S3100005", "Outsider")

    login_as(test_client, outsider)
    assert post_review(test_client, offer_id).status_code == 403


def test_direct_database_duplicate_is_rejected(client):
    """The database layer rejects a duplicate (offer, reviewer) pair."""
    test_client, test_db = client  # noqa: F841 - fixture builds the schema/db
    seller_id, buyer_id, offer_id = seed_deal(test_db)

    create_review(offer_id=offer_id, reviewer_id=buyer_id,
                  reviewed_user_id=seller_id, rating=5, comment="a")
    with pytest.raises(DuplicateReviewError):
        create_review(offer_id=offer_id, reviewer_id=buyer_id,
                      reviewed_user_id=seller_id, rating=4, comment="b")


def test_legacy_null_offer_reviews_survive_and_do_not_block(client):
    """A legacy review with NULL offer_id is preserved and not treated as a duplicate."""
    test_client, test_db = client
    seller_id, buyer_id, offer_id = seed_deal(test_db)

    conn = sqlite3.connect(test_db)
    conn.execute(
        "INSERT INTO reviews (offer_id, reviewed_user_id, reviewer_id, rating, comment) "
        "VALUES (NULL, ?, ?, 5, 'legacy')",
        (seller_id, buyer_id),
    )
    conn.commit()
    conn.close()

    login_as(test_client, buyer_id)
    assert post_review(test_client, offer_id).status_code == 201

    conn = sqlite3.connect(test_db)
    total = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    conn.close()
    assert total == 2
