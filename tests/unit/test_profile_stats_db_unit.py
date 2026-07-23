# pylint: disable=missing-module-docstring,missing-function-docstring,redefined-outer-name,duplicate-code
import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    db_path = tmp_path / "profile_stats_db_unit.db"
    monkeypatch.setattr(db_module, "DATABASE", db_path)
    db_module.init_db()
    return db_path


def create_user(test_db, student_id, display_name):
    conn = sqlite3.connect(test_db)
    cursor = conn.execute(
        """
        INSERT INTO users (
            student_id, first_name, last_name, display_name,
            email, contact_number, password_hash, role, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            student_id,
            display_name,
            "Test",
            display_name,
            f"{student_id.lower()}@mymail.nyp.edu.sg",
            "91234567",
            generate_password_hash("Password123"),
            "user",
            "Active",
        ),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def create_listing(test_db, seller_id, title, status="Active"):
    conn = sqlite3.connect(test_db)
    now = "2026-07-01 10:00:00"
    cursor = conn.execute(
        """
        INSERT INTO listings (
            seller_id, title, description, price, category, item_condition,
            image_url, listing_date, last_modified_timestamp, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (seller_id, title, "A nice item", "20.00", "Textbooks", "Good",
         '["https://example.com/img.jpg"]', now, now, status),
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
        VALUES (?, ?, 'cash', 15.0, NULL, ?, '2026-07-01 10:00:00')
        """,
        (listing_id, buyer_id, status),
    )
    conn.commit()
    offer_id = cursor.lastrowid
    conn.close()
    return offer_id


def create_review(test_db, transaction_id, reviewed_user_id, reviewer_id, rating):
    conn = sqlite3.connect(test_db)
    conn.execute(
        """
        INSERT INTO reviews (transaction_id, reviewed_user_id, reviewer_id, rating, comment)
        VALUES (?, ?, ?, ?, '')
        """,
        (transaction_id, reviewed_user_id, reviewer_id, rating),
    )
    conn.commit()
    conn.close()


def create_transaction(test_db, offer_id, listing_id, seller_id, buyer_id):
    conn = sqlite3.connect(test_db)
    cursor = conn.execute(
        """
        INSERT INTO transactions (offer_id, listing_id, seller_id, buyer_id,
                                  transaction_type, amount)
        VALUES (?, ?, ?, ?, 'cash', 15.0)
        """,
        (offer_id, listing_id, seller_id, buyer_id),
    )
    conn.commit()
    transaction_id = cursor.lastrowid
    conn.close()
    return transaction_id


# ===========================================================================
# get_active_listings_by_seller()
# ===========================================================================

def test_active_listings_returns_only_active_listings(test_db):
    seller_id = create_user(test_db, "S1000001", "Seller")
    create_listing(test_db, seller_id, "Active Item", status="Active")
    create_listing(test_db, seller_id, "Deleted Item", status="Deleted")

    listings = db_module.get_active_listings_by_seller(seller_id)

    assert len(listings) == 1
    assert listings[0]["title"] == "Active Item"


def test_active_listings_empty_for_seller_with_no_listings(test_db):
    seller_id = create_user(test_db, "S1000002", "NoListingsSeller")

    listings = db_module.get_active_listings_by_seller(seller_id)

    assert listings == []


# ===========================================================================
# get_sold_listings_by_seller()
# ===========================================================================

def test_sold_listings_returns_only_accepted_offers(test_db):
    seller_id = create_user(test_db, "S1000003", "Seller")
    buyer_id = create_user(test_db, "S1000004", "Buyer")
    listing_id = create_listing(test_db, seller_id, "Sold Item", status="Sold")
    create_offer(test_db, listing_id, buyer_id, status="Accepted")

    other_listing_id = create_listing(test_db, seller_id, "Still Pending Item")
    create_offer(test_db, other_listing_id, buyer_id, status="Pending")

    sold = db_module.get_sold_listings_by_seller(seller_id)

    assert len(sold) == 1
    assert sold[0]["title"] == "Sold Item"
    assert sold[0]["buyer"] == "Buyer"


# ===========================================================================
# get_user_profile_stats() — aggregate correctness
# ===========================================================================

def test_profile_stats_counts_active_and_sold_listings(test_db):
    seller_id = create_user(test_db, "S1000005", "Seller")
    buyer_id = create_user(test_db, "S1000006", "Buyer")
    create_listing(test_db, seller_id, "Active One", status="Active")
    create_listing(test_db, seller_id, "Active Two", status="Active")
    sold_listing_id = create_listing(test_db, seller_id, "Sold One", status="Sold")
    create_offer(test_db, sold_listing_id, buyer_id, status="Accepted")

    stats = db_module.get_user_profile_stats(seller_id)

    assert stats["active_count"] == 2
    assert stats["total_sales"] == 1
    assert stats["sold_count"] == 1


def test_profile_stats_average_rating_and_review_count(test_db):
    seller_id = create_user(test_db, "S1000007", "Seller")
    buyer_id = create_user(test_db, "S1000008", "Buyer")
    listing_id = create_listing(test_db, seller_id, "Item", status="Sold")
    offer_id = create_offer(test_db, listing_id, buyer_id, status="Accepted")
    transaction_id = create_transaction(test_db, offer_id, listing_id, seller_id, buyer_id)
    create_review(test_db, transaction_id, seller_id, buyer_id, rating=4)
    create_review(test_db, transaction_id, seller_id, buyer_id, rating=5)

    stats = db_module.get_user_profile_stats(seller_id)

    assert stats["review_count"] == 2
    assert stats["average_rating"] == 4.5


def test_profile_stats_average_rating_none_with_no_reviews(test_db):
    seller_id = create_user(test_db, "S1000009", "SellerNoReviews")

    stats = db_module.get_user_profile_stats(seller_id)

    assert stats["review_count"] == 0
    assert stats["average_rating"] is None


# ===========================================================================
# _trust_badge() tiers, exercised through get_user_profile_stats()
# ===========================================================================

def _seed_accepted_sales(test_db, seller_id, buyer_id, count):
    for i in range(count):
        listing_id = create_listing(test_db, seller_id, f"Item {i}", status="Sold")
        create_offer(test_db, listing_id, buyer_id, status="Accepted")


def test_trust_badge_new_seller_with_no_sales_or_listings(test_db):
    seller_id = create_user(test_db, "S1000010", "NewSeller")

    stats = db_module.get_user_profile_stats(seller_id)

    assert stats["trust_badge"] == "New Seller"


def test_trust_badge_active_seller_with_listing_but_no_sales(test_db):
    seller_id = create_user(test_db, "S1000011", "ActiveSeller")
    create_listing(test_db, seller_id, "Item", status="Active")

    stats = db_module.get_user_profile_stats(seller_id)

    assert stats["trust_badge"] == "Active Seller"


def test_trust_badge_trusted_seller_at_five_sales(test_db):
    seller_id = create_user(test_db, "S1000012", "TrustedSeller")
    buyer_id = create_user(test_db, "S1000013", "Buyer")
    _seed_accepted_sales(test_db, seller_id, buyer_id, count=5)

    stats = db_module.get_user_profile_stats(seller_id)

    assert stats["total_sales"] == 5
    assert stats["trust_badge"] == "Trusted Seller"


def test_trust_badge_top_seller_at_twenty_sales(test_db):
    seller_id = create_user(test_db, "S1000014", "TopSeller")
    buyer_id = create_user(test_db, "S1000015", "Buyer")
    _seed_accepted_sales(test_db, seller_id, buyer_id, count=20)

    stats = db_module.get_user_profile_stats(seller_id)

    assert stats["total_sales"] == 20
    assert stats["trust_badge"] == "Top Seller"


def test_trust_badge_just_below_trusted_threshold(test_db):
    """4 sales alone (no currently-active listing) is not yet 'Active Seller'."""
    seller_id = create_user(test_db, "S1000016", "AlmostTrusted")
    buyer_id = create_user(test_db, "S1000017", "Buyer")
    _seed_accepted_sales(test_db, seller_id, buyer_id, count=4)

    stats = db_module.get_user_profile_stats(seller_id)

    assert stats["total_sales"] == 4
    assert stats["trust_badge"] == "New Seller"


def test_trust_badge_active_seller_with_active_listing_and_some_sales(test_db):
    """An active listing plus fewer than 5 sales still qualifies as 'Active Seller'."""
    seller_id = create_user(test_db, "S1000023", "AlmostTrusted")
    buyer_id = create_user(test_db, "S1000024", "Buyer")
    _seed_accepted_sales(test_db, seller_id, buyer_id, count=4)
    create_listing(test_db, seller_id, "Still Listed Item", status="Active")

    stats = db_module.get_user_profile_stats(seller_id)

    assert stats["total_sales"] == 4
    assert stats["trust_badge"] == "Active Seller"


# ===========================================================================
# _response_rate(), exercised through get_user_profile_stats()
# ===========================================================================

def test_response_rate_calculated_correctly(test_db):
    seller_id = create_user(test_db, "S1000018", "Seller")
    buyer_id = create_user(test_db, "S1000019", "Buyer")
    listing_id = create_listing(test_db, seller_id, "Item")

    create_offer(test_db, listing_id, buyer_id, status="Accepted")
    create_offer(test_db, listing_id, buyer_id, status="Rejected")
    create_offer(test_db, listing_id, buyer_id, status="Rejected")
    create_offer(test_db, listing_id, buyer_id, status="Pending")

    stats = db_module.get_user_profile_stats(seller_id)

    assert stats["response_rate"] == 75


def test_response_rate_none_with_no_offers(test_db):
    seller_id = create_user(test_db, "S1000020", "SellerNoOffers")
    create_listing(test_db, seller_id, "Item")

    stats = db_module.get_user_profile_stats(seller_id)

    assert stats["response_rate"] is None


def test_response_rate_full_when_all_offers_responded(test_db):
    seller_id = create_user(test_db, "S1000021", "Seller")
    buyer_id = create_user(test_db, "S1000022", "Buyer")
    listing_id = create_listing(test_db, seller_id, "Item")

    create_offer(test_db, listing_id, buyer_id, status="Accepted")
    create_offer(test_db, listing_id, buyer_id, status="Rejected")

    stats = db_module.get_user_profile_stats(seller_id)

    assert stats["response_rate"] == 100
