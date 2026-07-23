"""
API integration tests for POST /api/reviews.

Uses a real temporary SQLite database with seeded users, listings, and
offers, exercising the actual accept_offer() -> submit_review() path.
"""
import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "test_submit_review.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client, test_db


def create_user(test_db, student_id, display_name):
    conn = sqlite3.connect(test_db)
    cursor = conn.execute(
        """
        INSERT INTO users (student_id, first_name, last_name, display_name,
                           email, contact_number, password_hash, role, status)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (student_id, display_name, "Test", display_name,
         f"{student_id.lower()}@mymail.nyp.edu.sg", "91234567",
         generate_password_hash("Password1"), "user", "Active"),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def create_listing(test_db, seller_id, title):
    conn = sqlite3.connect(test_db)
    now = "2026-06-09 10:00:00"
    cursor = conn.execute(
        """
        INSERT INTO listings (seller_id, title, description, price, category,
                              item_condition, image_url, listing_date, last_modified_timestamp)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (seller_id, title, "A nice item", "20.00", "Textbooks",
         "Good", '["https://example.com/img.jpg"]', now, now),
    )
    conn.commit()
    listing_id = cursor.lastrowid
    conn.close()
    return listing_id


def create_offer(test_db, listing_id, buyer_id, status="Pending"):
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


def seed_accepted_offer(test_db, seller_name="Seller1", buyer_name="Buyer1"):
    """Seed a seller, buyer, listing, and an Accepted offer. Returns ids."""
    seller_id = create_user(test_db, "S3000001", seller_name)
    buyer_id = create_user(test_db, "S3000002", buyer_name)
    listing_id = create_listing(test_db, seller_id, "Intro to Algorithms 3E")
    offer_id = create_offer(test_db, listing_id, buyer_id, status="Accepted")
    return seller_id, buyer_id, offer_id


def login_as(test_client, user_id):
    with test_client.session_transaction() as sess:
        sess["user_id"] = user_id


# ===========================================================================
# AC1: buyer submits a valid 1-5 rating with optional comment for the seller
# ===========================================================================

def test_buyer_can_submit_review_with_comment(client):
    """A buyer leaves a rating + comment for the seller of an Accepted offer."""
    test_client, test_db = client
    seller_id, buyer_id, offer_id = seed_accepted_offer(test_db)
    login_as(test_client, buyer_id)

    resp = test_client.post(
        "/api/reviews",
        json={"offer_id": offer_id, "rating": 5, "comment": "Prompt payment, smooth handover."},
    )

    assert resp.status_code == 201
    data = resp.get_json()
    assert data["review"]["rating"] == 5
    assert data["review"]["comment"] == "Prompt payment, smooth handover."
    assert data["review"]["reviewed_user_id"] == seller_id
    assert data["review"]["reviewer_id"] == buyer_id
    assert data["average_rating"] == 5.0
    assert data["review_count"] == 1


def test_buyer_can_submit_review_without_comment(client):
    """Comment is optional — omitting it still saves the rating."""
    test_client, test_db = client
    _seller_id, buyer_id, offer_id = seed_accepted_offer(test_db)
    login_as(test_client, buyer_id)

    resp = test_client.post("/api/reviews", json={"offer_id": offer_id, "rating": 4})

    assert resp.status_code == 201
    assert resp.get_json()["review"]["comment"] == ""


# ===========================================================================
# AC2: transaction is not completed
# ===========================================================================

def test_review_rejected_for_pending_offer(client):
    """A still-Pending offer is not a completed transaction -> 400."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S3000003", "Seller")
    buyer_id = create_user(test_db, "S3000004", "Buyer")
    listing_id = create_listing(test_db, seller_id, "Uncompleted Deal Item")
    offer_id = create_offer(test_db, listing_id, buyer_id, status="Pending")

    login_as(test_client, buyer_id)
    resp = test_client.post("/api/reviews", json={"offer_id": offer_id, "rating": 5})

    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_review_rejected_for_rejected_offer(client):
    """A Rejected offer is not a completed transaction -> 400."""
    test_client, test_db = client
    seller_id = create_user(test_db, "S3000005", "Seller")
    buyer_id = create_user(test_db, "S3000006", "Buyer")
    listing_id = create_listing(test_db, seller_id, "Rejected Deal Item")
    offer_id = create_offer(test_db, listing_id, buyer_id, status="Rejected")

    login_as(test_client, buyer_id)
    resp = test_client.post("/api/reviews", json={"offer_id": offer_id, "rating": 5})

    assert resp.status_code == 400


def test_review_rejected_for_nonexistent_offer(client):
    """An entirely unknown offer id is rejected."""
    test_client, test_db = client
    _seller_id, buyer_id, _offer_id = seed_accepted_offer(test_db)
    login_as(test_client, buyer_id)

    resp = test_client.post("/api/reviews", json={"offer_id": 999999, "rating": 5})

    assert resp.status_code == 404


# ===========================================================================
# AC3: review is linked to the seller and their profile
# ===========================================================================

def test_review_is_linked_to_seller_profile(client):
    """The saved review is retrievable from the seller's public review list."""
    test_client, test_db = client
    seller_id, buyer_id, offer_id = seed_accepted_offer(test_db)
    login_as(test_client, buyer_id)

    test_client.post(
        "/api/reviews",
        json={"offer_id": offer_id, "rating": 5, "comment": "Great seller."},
    )

    resp = test_client.get(f"/api/users/{seller_id}/reviews")

    assert resp.status_code == 200
    reviews = resp.get_json()["reviews"]
    assert len(reviews) == 1
    assert reviews[0]["reviewed_user_id"] == seller_id
    assert reviews[0]["reviewer_id"] == buyer_id
    assert reviews[0]["rating"] == 5


def test_review_rejects_mismatched_reviewee_id(client):
    """An explicit reviewee_id that does not match the listing's seller is rejected."""
    test_client, test_db = client
    _seller_id, buyer_id, offer_id = seed_accepted_offer(test_db)
    unrelated_id = create_user(test_db, "S3000007", "Unrelated")

    login_as(test_client, buyer_id)
    resp = test_client.post(
        "/api/reviews", json={"offer_id": offer_id, "rating": 5, "reviewee_id": unrelated_id}
    )

    assert resp.status_code == 400


# ===========================================================================
# AC4: rating outside 1-5 is rejected
# ===========================================================================

@pytest.mark.parametrize("bad_rating", [0, 6, -1, 4.5, "five", True, None])
def test_review_rejects_invalid_rating(client, bad_rating):
    """Ratings outside 1-5, or non-integer, are rejected with an error."""
    test_client, test_db = client
    _seller_id, buyer_id, offer_id = seed_accepted_offer(test_db)
    login_as(test_client, buyer_id)

    resp = test_client.post("/api/reviews", json={"offer_id": offer_id, "rating": bad_rating})

    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_review_rejects_missing_rating(client):
    """A request with no rating field at all is rejected."""
    test_client, test_db = client
    _seller_id, buyer_id, offer_id = seed_accepted_offer(test_db)
    login_as(test_client, buyer_id)

    resp = test_client.post("/api/reviews", json={"offer_id": offer_id})

    assert resp.status_code == 400


# ===========================================================================
# AC5: only the buyer of the completed offer may submit the review
# ===========================================================================

def test_seller_cannot_submit_review_for_own_offer(client):
    """The seller of this offer is not its buyer -> rejected."""
    test_client, test_db = client
    seller_id, _buyer_id, offer_id = seed_accepted_offer(test_db)
    login_as(test_client, seller_id)

    resp = test_client.post("/api/reviews", json={"offer_id": offer_id, "rating": 5})

    assert resp.status_code == 403
    assert "error" in resp.get_json()


def test_unrelated_user_cannot_submit_review(client):
    """A user with no relation to the offer is rejected."""
    test_client, test_db = client
    _seller_id, _buyer_id, offer_id = seed_accepted_offer(test_db)
    unrelated_id = create_user(test_db, "S3000008", "Unrelated")

    login_as(test_client, unrelated_id)
    resp = test_client.post("/api/reviews", json={"offer_id": offer_id, "rating": 5})

    assert resp.status_code == 403


def test_unauthenticated_user_cannot_submit_review(client):
    """Unauthenticated request is rejected before any other check."""
    test_client, test_db = client
    _seller_id, _buyer_id, offer_id = seed_accepted_offer(test_db)

    resp = test_client.post("/api/reviews", json={"offer_id": offer_id, "rating": 5})

    assert resp.status_code == 401


# ===========================================================================
# #36: average rating recalculates as reviews accumulate
# ===========================================================================

def test_average_rating_updates_as_reviews_accumulate(client):
    """Submitting a second review recalculates the average correctly."""
    test_client, test_db = client
    seller_id, buyer_id, offer_id = seed_accepted_offer(test_db)
    other_buyer_id = create_user(test_db, "S3000009", "OtherBuyer")
    listing_id = create_listing(test_db, seller_id, "Second Item")
    second_offer_id = create_offer(test_db, listing_id, other_buyer_id, status="Accepted")

    login_as(test_client, buyer_id)
    first_resp = test_client.post("/api/reviews", json={"offer_id": offer_id, "rating": 4})
    assert first_resp.get_json()["average_rating"] == 4.0

    login_as(test_client, other_buyer_id)
    second_resp = test_client.post("/api/reviews", json={"offer_id": second_offer_id, "rating": 2})

    assert second_resp.get_json()["average_rating"] == 3.0
    assert second_resp.get_json()["review_count"] == 2
