"""Unit tests for listing category and condition filters."""

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


def create_listing(seller_id, title, category, condition):
    """Create a listing for filter tests."""
    return app_db.create_listing(
        seller_id=seller_id,
        title=title,
        description=f"{title} description",
        price="10.00",
        category=category,
        condition=condition,
        image_url="https://example.com/item.jpg",
    )


def login_as(client, user_id):
    """Authenticate a test session before accessing protected listing routes."""
    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["email"] = f"user{user_id}@mymail.nyp.edu.sg"
        session["display_name"] = f"User {user_id}"
        session["role"] = "user"


def test_api_filter_by_category(tmp_path, monkeypatch):
    """API should return only listings in the selected category."""
    monkeypatch.setattr(app_db, "DATABASE", tmp_path / "test_swaplah.db")

    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    seller_id = create_test_user("seller@mymail.nyp.edu.sg", "S001")
    login_as(client, seller_id)

    create_listing(seller_id, "Calculator", "Electronics", "Good")
    create_listing(seller_id, "Textbook", "Textbooks", "Good")

    response = client.get("/api/listings?category=Electronics")

    assert response.status_code == 200

    data = response.get_json()
    titles = [listing["title"] for listing in data["listings"]]

    assert titles == ["Calculator"]
    assert data["totalListings"] == 1


def test_api_filter_by_condition(tmp_path, monkeypatch):
    """API should return only listings with the selected condition."""
    monkeypatch.setattr(app_db, "DATABASE", tmp_path / "test_swaplah.db")

    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    seller_id = create_test_user("seller@mymail.nyp.edu.sg", "S001")
    login_as(client, seller_id)

    create_listing(seller_id, "Calculator", "Electronics", "Good")
    create_listing(seller_id, "Keyboard", "Electronics", "Like New")

    response = client.get("/api/listings?condition=Like+New")

    assert response.status_code == 200

    data = response.get_json()
    titles = [listing["title"] for listing in data["listings"]]

    assert titles == ["Keyboard"]
    assert data["totalListings"] == 1


def test_api_filter_by_category_and_condition(tmp_path, monkeypatch):
    """API should return listings matching both category and condition."""
    monkeypatch.setattr(app_db, "DATABASE", tmp_path / "test_swaplah.db")

    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    seller_id = create_test_user("seller@mymail.nyp.edu.sg", "S001")
    login_as(client, seller_id)

    create_listing(seller_id, "Calculator", "Electronics", "Good")
    create_listing(seller_id, "Keyboard", "Electronics", "Like New")
    create_listing(seller_id, "Textbook", "Textbooks", "Like New")

    response = client.get("/api/listings?category=Electronics&condition=Like+New")

    assert response.status_code == 200

    data = response.get_json()
    titles = [listing["title"] for listing in data["listings"]]

    assert titles == ["Keyboard"]
    assert data["totalListings"] == 1


def test_homepage_filter_by_category_and_condition(tmp_path, monkeypatch):
    """Homepage shell should load with filter params; results come via the API.

    Listing content is fetched client-side from /api/listings (verified by
    test_api_filter_by_category_and_condition above), so this only checks the
    server-rendered shell responds successfully with the filters applied.
    """
    monkeypatch.setattr(app_db, "DATABASE", tmp_path / "test_swaplah.db")

    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    seller_id = create_test_user("seller@mymail.nyp.edu.sg", "S001")
    login_as(client, seller_id)

    create_listing(seller_id, "Calculator", "Electronics", "Good")
    create_listing(seller_id, "Keyboard", "Electronics", "Like New")
    create_listing(seller_id, "Biology Guide", "Textbooks", "Like New")

    response = client.get("/?category=Electronics&condition=Like+New")

    assert response.status_code == 200
    assert b'value="Electronics" selected' in response.data
