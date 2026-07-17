"""Unit tests for listing database helpers."""

import json

from werkzeug.security import generate_password_hash

from app import db as app_db


def create_test_user(email, student_id):
    """Create a test user and return the user ID."""
    conn = app_db.get_db_connection()
    cursor = conn.execute(
        """
        INSERT INTO users (
            student_id,
            first_name,
            last_name,
            display_name,
            email,
            contact_number,
            password_hash
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            student_id,
            "Test",
            "User",
            "Test User",
            email,
            "91234567",
            generate_password_hash("password123"),
        ),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id

def test_create_and_get_listing_from_db(tmp_path, monkeypatch):
    """Create a listing and retrieve it from the database."""
    test_db = tmp_path / "test_swaplah.db"
    monkeypatch.setattr(app_db, "DATABASE", test_db)

    app_db.init_db()

    conn = app_db.get_db_connection()
    conn.execute(
        """
        INSERT INTO users (
            student_id,
            first_name,
            last_name,
            display_name,
            email,
            contact_number,
            password_hash
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "S1234567A",
            "Felicia",
            "Tan",
            "Felicia",
            "felicia@mymail.nyp.edu.sg",
            "91234567",
            generate_password_hash("password123"),
        ),
    )
    conn.commit()

    user = conn.execute(
        "SELECT * FROM users WHERE email = ?",
        ("felicia@mymail.nyp.edu.sg",),
    ).fetchone()
    conn.close()

    image_data = json.dumps(
        [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg",
        ]
    )

    listing = app_db.create_listing(
        seller_id=user["id"],
        title="Casio Calculator",
        description="Good condition calculator",
        price="25.00",
        category="Electronics",
        condition="Good",
        image_url=image_data,
    )

    assert listing["id"] is not None
    assert listing["title"] == "Casio Calculator"
    assert listing["seller_id"] == user["id"]

    fetched_listing = app_db.get_listing_by_id(listing["id"])

    assert fetched_listing["title"] == "Casio Calculator"
    assert fetched_listing["seller_display_name"] == "Felicia"
    assert fetched_listing["seller_email"] == "felicia@mymail.nyp.edu.sg"
    assert fetched_listing["seller_contact_number"] == "91234567"
    assert fetched_listing["images"][0] == "https://example.com/image1.jpg"

    all_listings = app_db.get_all_listings()

    assert len(all_listings) == 1
    assert all_listings[0]["title"] == "Casio Calculator"
    assert all_listings[0]["image"] == "https://example.com/image1.jpg"


def test_get_listing_by_id_not_found(tmp_path, monkeypatch):
    """Return None when the listing does not exist."""
    test_db = tmp_path / "test_swaplah.db"
    monkeypatch.setattr(app_db, "DATABASE", test_db)

    app_db.init_db()

    listing = app_db.get_listing_by_id(999999)

    assert listing is None

def test_soft_delete_listing_marks_deleted_and_hides_from_active_results(tmp_path, monkeypatch):
    """Soft-delete a listing and hide it from active listing queries."""
    test_db = tmp_path / "test_swaplah.db"
    monkeypatch.setattr(app_db, "DATABASE", test_db)

    app_db.init_db()

    seller_id = create_test_user("seller@mymail.nyp.edu.sg", "S001")

    listing = app_db.create_listing(
        seller_id=seller_id,
        title="Calculator",
        description="Good condition calculator",
        price="25.00",
        category="Electronics",
        condition="Good",
        image_url="https://example.com/calculator.jpg",
    )

    deleted_listing, error = app_db.soft_delete_listing(listing["id"], seller_id)

    assert error is None
    assert deleted_listing["status"] == "Deleted"

    conn = app_db.get_db_connection()
    row = conn.execute(
        "SELECT status FROM listings WHERE id = ?",
        (listing["id"],),
    ).fetchone()
    conn.close()

    assert row["status"] == "Deleted"
    assert app_db.get_listing_by_id(listing["id"]) is None
    assert app_db.get_all_listings() == []


def test_soft_delete_listing_blocks_non_owner(tmp_path, monkeypatch):
    """Return forbidden when a non-owner tries to soft-delete a listing."""
    test_db = tmp_path / "test_swaplah.db"
    monkeypatch.setattr(app_db, "DATABASE", test_db)

    app_db.init_db()

    seller_id = create_test_user("seller@mymail.nyp.edu.sg", "S001")
    other_user_id = create_test_user("other@mymail.nyp.edu.sg", "S002")

    listing = app_db.create_listing(
        seller_id=seller_id,
        title="Textbook",
        description="Used textbook",
        price="10.00",
        category="Textbooks",
        condition="Good",
        image_url="https://example.com/textbook.jpg",
    )

    deleted_listing, error = app_db.soft_delete_listing(listing["id"], other_user_id)

    assert deleted_listing is None
    assert error == "forbidden"

    active_listing = app_db.get_listing_by_id(listing["id"])

    assert active_listing is not None
    assert active_listing["title"] == "Textbook"


def test_soft_delete_listing_returns_not_found_for_missing_or_deleted_listing(
    tmp_path,
    monkeypatch,
):
    """Return not_found for missing listings and already-deleted listings."""
    test_db = tmp_path / "test_swaplah.db"
    monkeypatch.setattr(app_db, "DATABASE", test_db)

    app_db.init_db()

    missing_listing, missing_error = app_db.soft_delete_listing(999999, 1)

    assert missing_listing is None
    assert missing_error == "not_found"

    seller_id = create_test_user("seller@mymail.nyp.edu.sg", "S001")

    listing = app_db.create_listing(
        seller_id=seller_id,
        title="Mouse",
        description="Wireless mouse",
        price="8.00",
        category="Electronics",
        condition="Good",
        image_url="https://example.com/mouse.jpg",
    )

    first_delete, first_error = app_db.soft_delete_listing(listing["id"], seller_id)
    second_delete, second_error = app_db.soft_delete_listing(listing["id"], seller_id)

    assert first_error is None
    assert first_delete["status"] == "Deleted"
    assert second_delete is None
    assert second_error == "not_found"
