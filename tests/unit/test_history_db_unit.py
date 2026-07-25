"""Unit tests for transaction-history database helpers."""

# pylint: disable=redefined-outer-name

import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Point database helpers at an isolated SQLite database."""
    db_path = tmp_path / "history_db_unit.db"
    monkeypatch.setattr(db_module, "DATABASE", db_path)
    db_module.init_db()
    return db_path


def create_user(test_db, student_id, display_name):
    """Insert a user and return its ID."""
    conn = sqlite3.connect(test_db)
    cursor = conn.execute(
        """
        INSERT INTO users (
            student_id, first_name, last_name, display_name,
            email, contact_number, password_hash, role, status
        )
        VALUES (?, ?, 'Test', ?, ?, '91234567', ?, 'user', 'Active')
        """,
        (
            student_id,
            display_name,
            display_name,
            f"{student_id.lower()}@mymail.nyp.edu.sg",
            generate_password_hash("Password123"),
        ),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def create_listing(test_db, seller_id, title, category="Textbooks"):
    """Insert a listing and return its ID."""
    conn = sqlite3.connect(test_db)
    cursor = conn.execute(
        """
        INSERT INTO listings (
            seller_id, title, description, price, category, item_condition,
            image_url, listing_date, last_modified_timestamp
        )
        VALUES (?, ?, 'Test item', 25.0, ?, 'Good', '[]',
                '2026-07-01 10:00:00', '2026-07-01 10:00:00')
        """,
        (seller_id, title, category),
    )
    conn.commit()
    listing_id = cursor.lastrowid
    conn.close()
    return listing_id


def create_offer(test_db, listing_id, buyer_id, offer_type="cash", amount=20.0):
    """Insert a pending offer and return its ID."""
    conn = sqlite3.connect(test_db)
    cursor = conn.execute(
        """
        INSERT INTO offers (
            listing_id, buyer_id, offer_type, proposed_price,
            swap_listing_id, status, created_at
        )
        VALUES (?, ?, ?, ?, NULL, 'Pending', '2026-07-01 10:00:00')
        """,
        (listing_id, buyer_id, offer_type, amount),
    )
    conn.commit()
    offer_id = cursor.lastrowid
    conn.close()
    return offer_id


def seed_completed_deal(
    test_db,
    seller_id,
    buyer_id,
    title="History Item",
    offer_type="cash",
    amount=20.0,
):
    """Accept an offer and return its offer ID."""
    listing_id = create_listing(test_db, seller_id, title)
    offer_id = create_offer(test_db, listing_id, buyer_id, offer_type, amount)
    db_module.accept_offer(offer_id)
    return offer_id


def test_buyer_history_returns_seller_and_listing_details(test_db):
    """Buyer history identifies the seller and purchased item."""
    seller_id = create_user(test_db, "S5100001", "HistorySeller")
    buyer_id = create_user(test_db, "S5100002", "HistoryBuyer")
    offer_id = seed_completed_deal(test_db, seller_id, buyer_id)

    rows = db_module.get_transactions_for_user(buyer_id, "buyer")

    assert len(rows) == 1
    assert rows[0]["offer_id"] == offer_id
    assert rows[0]["transaction_type"] == "cash"
    assert rows[0]["amount"] == 20.0
    assert rows[0]["listing_title"] == "History Item"
    assert rows[0]["listing_category"] == "Textbooks"
    assert rows[0]["counterparty_display_name"] == "HistorySeller"


def test_seller_history_returns_buyer_as_counterparty(test_db):
    """Seller history identifies the buyer rather than the seller."""
    seller_id = create_user(test_db, "S5100003", "HistorySeller")
    buyer_id = create_user(test_db, "S5100004", "HistoryBuyer")
    offer_id = seed_completed_deal(test_db, seller_id, buyer_id)

    rows = db_module.get_transactions_for_user(seller_id, "seller")

    assert len(rows) == 1
    assert rows[0]["offer_id"] == offer_id
    assert rows[0]["counterparty_display_name"] == "HistoryBuyer"


def test_history_is_scoped_to_requested_user_and_role(test_db):
    """Transactions belonging to other users are not leaked."""
    seller_one = create_user(test_db, "S5100005", "SellerOne")
    buyer_one = create_user(test_db, "S5100006", "BuyerOne")
    seller_two = create_user(test_db, "S5100007", "SellerTwo")
    buyer_two = create_user(test_db, "S5100008", "BuyerTwo")
    seed_completed_deal(test_db, seller_one, buyer_one, "First Item")
    seed_completed_deal(test_db, seller_two, buyer_two, "Second Item")

    buyer_rows = db_module.get_transactions_for_user(buyer_one, "buyer")
    seller_rows = db_module.get_transactions_for_user(seller_one, "seller")

    assert [row["listing_title"] for row in buyer_rows] == ["First Item"]
    assert [row["listing_title"] for row in seller_rows] == ["First Item"]
    assert db_module.get_transactions_for_user(seller_one, "buyer") == []
    assert db_module.get_transactions_for_user(buyer_one, "seller") == []


def test_history_returns_newest_transaction_first(test_db):
    """Multiple transactions are ordered by completion time descending."""
    seller_id = create_user(test_db, "S5100009", "HistorySeller")
    buyer_id = create_user(test_db, "S5100010", "HistoryBuyer")
    first_offer = seed_completed_deal(test_db, seller_id, buyer_id, "Older Item")
    second_offer = seed_completed_deal(test_db, seller_id, buyer_id, "Newer Item")

    conn = sqlite3.connect(test_db)
    conn.execute(
        "UPDATE transactions SET created_at = '2026-07-01 10:00:00' WHERE offer_id = ?",
        (first_offer,),
    )
    conn.execute(
        "UPDATE transactions SET created_at = '2026-07-02 10:00:00' WHERE offer_id = ?",
        (second_offer,),
    )
    conn.commit()
    conn.close()

    rows = db_module.get_transactions_for_user(buyer_id, "buyer")

    assert [row["listing_title"] for row in rows] == ["Newer Item", "Older Item"]


def test_history_preserves_swap_type_and_empty_amount(test_db):
    """Swap transactions retain their type and nullable cash amount."""
    seller_id = create_user(test_db, "S5100011", "HistorySeller")
    buyer_id = create_user(test_db, "S5100012", "HistoryBuyer")
    seed_completed_deal(
        test_db,
        seller_id,
        buyer_id,
        offer_type="swap",
        amount=None,
    )

    rows = db_module.get_transactions_for_user(buyer_id, "buyer")

    assert rows[0]["transaction_type"] == "swap"
    assert rows[0]["amount"] is None


def test_history_is_empty_for_unknown_user(test_db):
    """An unknown user ID returns an empty history."""
    assert db_module.get_transactions_for_user(999999, "buyer") == []
    assert db_module.get_transactions_for_user(999999, "seller") == []


def test_history_rejects_invalid_role_before_opening_database(monkeypatch):
    """Invalid roles fail without executing a database query."""
    monkeypatch.setattr(
        db_module,
        "get_db_connection",
        lambda: pytest.fail("database should not be opened"),
    )

    with pytest.raises(ValueError, match="role must be 'buyer' or 'seller'"):
        db_module.get_transactions_for_user(1, "admin")
