"""
API integration tests for:
  GET  /api/offers/received
  PATCH /api/offers/<id>/accept
  PATCH /api/offers/<id>/reject
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
    test_db = tmp_path / "test_manage_offers.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client, test_db


def seed_db(test_db):
    """Insert two users, two listings, and three offers for testing."""
    conn = sqlite3.connect(test_db)
    now = "2026-06-09 10:00:00"

    # user 1 = seller
    conn.execute(
        "INSERT INTO users (student_id,first_name,last_name,display_name,email,contact_number,password_hash,role,status) VALUES (?,?,?,?,?,?,?,?,?)",
        ("S11111111","Alice","Seller","AliceSeller","alice@mymail.nyp.edu.sg","91111111",generate_password_hash("Password1"),"user","Active"),
    )
    # user 2 = buyer A
    conn.execute(
        "INSERT INTO users (student_id,first_name,last_name,display_name,email,contact_number,password_hash,role,status) VALUES (?,?,?,?,?,?,?,?,?)",
        ("S22222222","Bob","Buyer","BobBuyer","bob@mymail.nyp.edu.sg","92222222",generate_password_hash("Password2"),"user","Active"),
    )
    # user 3 = buyer B
    conn.execute(
        "INSERT INTO users (student_id,first_name,last_name,display_name,email,contact_number,password_hash,role,status) VALUES (?,?,?,?,?,?,?,?,?)",
        ("S33333333","Carol","Buyer","CarolBuyer","carol@mymail.nyp.edu.sg","93333333",generate_password_hash("Password3"),"user","Active"),
    )

    # listing 1 owned by seller (id=1)
    conn.execute(
        "INSERT INTO listings (seller_id,title,description,price,category,item_condition,image_url,listing_date,last_modified_timestamp) VALUES (?,?,?,?,?,?,?,?,?)",
        (1,"Seller Item","A nice item","50.00","Electronics","Good",'["https://example.com/img.jpg"]',now,now),
    )
    # listing 2 owned by buyer A (id=2) — used as swap item
    conn.execute(
        "INSERT INTO listings (seller_id,title,description,price,category,item_condition,image_url,listing_date,last_modified_timestamp) VALUES (?,?,?,?,?,?,?,?,?)",
        (2,"Buyer Swap Item","My swap item","30.00","Books","Fair",'["https://example.com/swap.jpg"]',now,now),
    )

    # offer 1: Bob cash offer on listing 1
    conn.execute(
        "INSERT INTO offers (listing_id,buyer_id,offer_type,proposed_price,status,created_at) VALUES (?,?,?,?,?,?)",
        (1,2,"cash",40.0,"Pending",now),
    )
    # offer 2: Carol swap offer on listing 1
    conn.execute(
        "INSERT INTO offers (listing_id,buyer_id,offer_type,swap_listing_id,status,created_at) VALUES (?,?,?,?,?,?)",
        (1,3,"swap",2,"Pending",now),
    )
    # offer 3: Bob cash offer on listing 1 (already rejected)
    conn.execute(
        "INSERT INTO offers (listing_id,buyer_id,offer_type,proposed_price,status,created_at) VALUES (?,?,?,?,?,?)",
        (1,2,"cash",20.0,"Rejected",now),
    )

    conn.commit()
    conn.close()


def login_as_seller(test_client):
    with test_client.session_transaction() as sess:
        sess["user_id"] = 1


def login_as_buyer(test_client):
    with test_client.session_transaction() as sess:
        sess["user_id"] = 2


# ===========================================================================
# GET /api/offers/received
# ===========================================================================

def test_seller_can_view_received_offers(client):
    """AC1 (view): seller sees all offers for their listing."""
    test_client, test_db = client
    seed_db(test_db)
    login_as_seller(test_client)

    response = test_client.get("/api/offers/received")

    assert response.status_code == 200
    data = response.get_json()
    assert "offers" in data
    assert len(data["offers"]) == 3  # all offers for listing 1


def test_view_offers_unauthenticated(client):
    """AC2 (view): unauthenticated user cannot view received offers."""
    test_client, test_db = client
    seed_db(test_db)

    response = test_client.get("/api/offers/received")

    assert response.status_code == 401
    assert "error" in response.get_json()


def test_seller_sees_empty_list_when_no_offers(client):
    """AC3 (view): seller with listings but no offers gets empty list."""
    test_client, test_db = client
    seed_db(test_db)
    # Log in as buyer B who has no listings and therefore no received offers
    with test_client.session_transaction() as sess:
        sess["user_id"] = 3

    response = test_client.get("/api/offers/received")

    assert response.status_code == 200
    assert response.get_json()["offers"] == []


def test_buyer_does_not_see_seller_offers(client):
    """AC2 (view): a different user only sees offers on their own listings."""
    test_client, test_db = client
    seed_db(test_db)
    login_as_buyer(test_client)

    response = test_client.get("/api/offers/received")

    assert response.status_code == 200
    # Buyer (id=2) owns listing 2, which has no offers
    assert response.get_json()["offers"] == []


def test_received_offers_include_listing_details(client):
    """Offer objects carry listing title, category, and price."""
    test_client, test_db = client
    seed_db(test_db)
    login_as_seller(test_client)

    data = test_client.get("/api/offers/received").get_json()
    offer = data["offers"][0]

    assert "listingTitle" in offer
    assert "listingCategory" in offer
    assert "listingPrice" in offer
    assert "buyerDisplayName" in offer


# ===========================================================================
# PATCH /api/offers/<id>/accept
# ===========================================================================

def test_seller_can_accept_pending_offer(client):
    """AC1 (accept): seller accepts a pending offer → status becomes Accepted."""
    test_client, test_db = client
    seed_db(test_db)
    login_as_seller(test_client)

    response = test_client.patch("/api/offers/1/accept")

    assert response.status_code == 200
    data = response.get_json()
    assert data["offer"]["status"] == "Accepted"


def test_accept_offer_non_owner_forbidden(client):
    """AC2 (accept): non-owner cannot accept an offer."""
    test_client, test_db = client
    seed_db(test_db)
    login_as_buyer(test_client)

    response = test_client.patch("/api/offers/1/accept")

    assert response.status_code == 403
    assert "error" in response.get_json()


def test_accept_offer_auto_rejects_other_pending_offers(client):
    """AC5 (accept): accepting offer 1 auto-rejects offer 2 for the same listing."""
    test_client, test_db = client
    seed_db(test_db)
    login_as_seller(test_client)

    test_client.patch("/api/offers/1/accept")

    # Offer 2 (Carol's swap offer on same listing) should now be Rejected
    offers_resp = test_client.get("/api/offers/received").get_json()
    offer_2 = next(o for o in offers_resp["offers"] if o["id"] == 2)
    assert offer_2["status"] == "Rejected"


def test_accept_offer_only_one_accepted_per_listing(client):
    """AC2 (auto-reject): only one offer ends up Accepted for a listing."""
    test_client, test_db = client
    seed_db(test_db)
    login_as_seller(test_client)

    test_client.patch("/api/offers/1/accept")

    offers_resp = test_client.get("/api/offers/received").get_json()
    accepted = [o for o in offers_resp["offers"] if o["status"] == "Accepted"]
    assert len(accepted) == 1


def test_accept_offer_not_found(client):
    """Accepting a non-existent offer returns 404."""
    test_client, test_db = client
    seed_db(test_db)
    login_as_seller(test_client)

    response = test_client.patch("/api/offers/999/accept")

    assert response.status_code == 404


def test_accept_offer_unauthenticated(client):
    """Unauthenticated accept returns 401."""
    test_client, test_db = client
    seed_db(test_db)

    response = test_client.patch("/api/offers/1/accept")

    assert response.status_code == 401


def test_accept_already_rejected_offer_returns_conflict(client):
    """Cannot accept an already-rejected offer."""
    test_client, test_db = client
    seed_db(test_db)
    login_as_seller(test_client)

    # offer 3 is already Rejected
    response = test_client.patch("/api/offers/3/accept")

    assert response.status_code == 409


# ===========================================================================
# PATCH /api/offers/<id>/reject
# ===========================================================================

def test_seller_can_reject_pending_offer(client):
    """AC1 (reject): seller rejects a pending offer → status becomes Rejected."""
    test_client, test_db = client
    seed_db(test_db)
    login_as_seller(test_client)

    response = test_client.patch("/api/offers/1/reject")

    assert response.status_code == 200
    assert response.get_json()["offer"]["status"] == "Rejected"


def test_reject_offer_non_owner_forbidden(client):
    """AC2 (reject): non-owner cannot reject an offer."""
    test_client, test_db = client
    seed_db(test_db)
    login_as_buyer(test_client)

    response = test_client.patch("/api/offers/1/reject")

    assert response.status_code == 403
    assert "error" in response.get_json()


def test_reject_offer_does_not_affect_other_pending_offers(client):
    """AC3 (reject): rejecting offer 1 leaves offer 2 as Pending."""
    test_client, test_db = client
    seed_db(test_db)
    login_as_seller(test_client)

    test_client.patch("/api/offers/1/reject")

    offers_resp = test_client.get("/api/offers/received").get_json()
    offer_2 = next(o for o in offers_resp["offers"] if o["id"] == 2)
    assert offer_2["status"] == "Pending"


def test_reject_offer_not_found(client):
    """Rejecting a non-existent offer returns 404."""
    test_client, test_db = client
    seed_db(test_db)
    login_as_seller(test_client)

    response = test_client.patch("/api/offers/999/reject")

    assert response.status_code == 404


def test_reject_offer_unauthenticated(client):
    """Unauthenticated reject returns 401."""
    test_client, test_db = client
    seed_db(test_db)

    response = test_client.patch("/api/offers/1/reject")

    assert response.status_code == 401


def test_reject_already_rejected_offer_returns_conflict(client):
    """Cannot reject an already-rejected offer."""
    test_client, test_db = client
    seed_db(test_db)
    login_as_seller(test_client)

    response = test_client.patch("/api/offers/3/reject")

    assert response.status_code == 409