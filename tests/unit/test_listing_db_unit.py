import json

from werkzeug.security import generate_password_hash

from app import db as app_db


def test_create_and_get_listing_from_db(tmp_path, monkeypatch):
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
            generate_password_hash("password123")
        )
    )
    conn.commit()

    user = conn.execute(
        "SELECT * FROM users WHERE email = ?",
        ("felicia@mymail.nyp.edu.sg",)
    ).fetchone()
    conn.close()

    image_data = json.dumps([
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg"
    ])

    listing = app_db.create_listing(
        seller_id=user["id"],
        title="Casio Calculator",
        description="Good condition calculator",
        price="25.00",
        category="Electronics",
        condition="Good",
        image_url=image_data
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
    test_db = tmp_path / "test_swaplah.db"
    monkeypatch.setattr(app_db, "DATABASE", test_db)

    app_db.init_db()

    listing = app_db.get_listing_by_id(999999)

    assert listing is None