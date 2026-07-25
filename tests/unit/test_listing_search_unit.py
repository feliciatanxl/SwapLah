"""Unit tests for listing keyword search."""

# pylint: disable=redefined-outer-name

from app import create_app
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
            "fake_hash",
        ),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def update_listing_date(listing_id, listing_date):
    """Update listing date for ordering tests."""
    conn = app_db.get_db_connection()
    conn.execute(
        """
        UPDATE listings
        SET listing_date = ?,
            last_modified_timestamp = ?
        WHERE id = ?
        """,
        (listing_date, listing_date, listing_id),
    )
    conn.commit()
    conn.close()


def login_as(client, user_id):
    """Authenticate a test session before accessing protected listing routes."""
    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["email"] = f"user{user_id}@mymail.nyp.edu.sg"
        session["display_name"] = f"User {user_id}"
        session["role"] = "user"


def test_api_search_matches_title_and_description_ordered_newest_first(
    tmp_path,
    monkeypatch,
):
    """API search should match title and description, newest first."""
    monkeypatch.setattr(app_db, "DATABASE", tmp_path / "test_swaplah.db")

    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    seller_id = create_test_user("seller@mymail.nyp.edu.sg", "S001")
    login_as(client, seller_id)

    title_match = app_db.create_listing(
        seller_id=seller_id,
        title="Casio Calculator",
        description="Used for exams",
        price="25.00",
        category="Electronics",
        condition="Good",
        image_url="https://example.com/calculator.jpg",
    )

    description_match = app_db.create_listing(
        seller_id=seller_id,
        title="Math Notes",
        description="Includes calculator tips",
        price="5.00",
        category="Textbooks",
        condition="Good",
        image_url="https://example.com/notes.jpg",
    )

    unrelated = app_db.create_listing(
        seller_id=seller_id,
        title="Laptop Stand",
        description="Adjustable stand",
        price="8.00",
        category="Electronics",
        condition="Good",
        image_url="https://example.com/stand.jpg",
    )

    update_listing_date(title_match["id"], "2026-06-01 10:00:00")
    update_listing_date(description_match["id"], "2026-06-03 10:00:00")
    update_listing_date(unrelated["id"], "2026-06-04 10:00:00")

    response = client.get("/api/listings?search=calculator")

    assert response.status_code == 200

    data = response.get_json()
    titles = [listing["title"] for listing in data["listings"]]

    assert titles == ["Math Notes", "Casio Calculator"]
    assert "Laptop Stand" not in titles
    assert data["totalListings"] == 2


def test_api_search_returns_empty_when_no_match(tmp_path, monkeypatch):
    """API search should return empty results when nothing matches."""
    monkeypatch.setattr(app_db, "DATABASE", tmp_path / "test_swaplah.db")

    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    seller_id = create_test_user("seller@mymail.nyp.edu.sg", "S001")
    login_as(client, seller_id)

    app_db.create_listing(
        seller_id=seller_id,
        title="Laptop Stand",
        description="Adjustable stand",
        price="8.00",
        category="Electronics",
        condition="Good",
        image_url="https://example.com/stand.jpg",
    )

    response = client.get("/api/listings?search=keyboard")

    assert response.status_code == 200

    data = response.get_json()

    assert data["listings"] == []
    assert data["totalListings"] == 0


def test_api_search_excludes_deleted_listings(tmp_path, monkeypatch):
    """API search should not return soft-deleted listings."""
    monkeypatch.setattr(app_db, "DATABASE", tmp_path / "test_swaplah.db")

    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    seller_id = create_test_user("seller@mymail.nyp.edu.sg", "S001")
    login_as(client, seller_id)

    listing = app_db.create_listing(
        seller_id=seller_id,
        title="Mechanical Keyboard",
        description="RGB keyboard",
        price="30.00",
        category="Electronics",
        condition="Good",
        image_url="https://example.com/keyboard.jpg",
    )

    app_db.soft_delete_listing(listing["id"], seller_id)

    response = client.get("/api/listings?search=keyboard")

    assert response.status_code == 200

    data = response.get_json()

    assert data["listings"] == []
    assert data["totalListings"] == 0


def test_homepage_search_filters_listings_by_keyword(tmp_path, monkeypatch):
    """Homepage search should show matching listings only."""
    monkeypatch.setattr(app_db, "DATABASE", tmp_path / "test_swaplah.db")

    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    seller_id = create_test_user("seller@mymail.nyp.edu.sg", "S001")
    login_as(client, seller_id)

    app_db.create_listing(
        seller_id=seller_id,
        title="Casio Calculator",
        description="Good condition calculator",
        price="25.00",
        category="Electronics",
        condition="Good",
        image_url="https://example.com/calculator.jpg",
    )

    app_db.create_listing(
        seller_id=seller_id,
        title="Laptop Stand",
        description="Adjustable stand",
        price="8.00",
        category="Electronics",
        condition="Good",
        image_url="https://example.com/stand.jpg",
    )

    response = client.get("/?search=calculator")

    assert response.status_code == 200
    assert b"Casio Calculator" in response.data
    assert b"Laptop Stand" not in response.data


def test_homepage_search_no_results_message(tmp_path, monkeypatch):
    """Homepage search should show no matching message when nothing matches."""
    monkeypatch.setattr(app_db, "DATABASE", tmp_path / "test_swaplah.db")

    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    seller_id = create_test_user("seller@mymail.nyp.edu.sg", "S001")
    login_as(client, seller_id)

    app_db.create_listing(
        seller_id=seller_id,
        title="Laptop Stand",
        description="Adjustable stand",
        price="8.00",
        category="Electronics",
        condition="Good",
        image_url="https://example.com/stand.jpg",
    )

    response = client.get("/?search=calculator")

    assert response.status_code == 200
    assert b"No matching listings found." in response.data
