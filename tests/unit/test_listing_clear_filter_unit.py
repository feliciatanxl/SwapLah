"""Unit tests for clearing listing filters individually."""

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
    """Create a listing for clear filter tests."""
    return app_db.create_listing(
        seller_id=seller_id,
        title=title,
        description=f"{title} description",
        price="10.00",
        category=category,
        condition=condition,
        image_url="https://example.com/item.jpg",
    )


def seed_filter_listings():
    """Create listings used by clear filter tests."""
    seller_id = create_test_user("seller@mymail.nyp.edu.sg", "S001")

    create_listing(seller_id, "Calculator", "Electronics", "Good")
    create_listing(seller_id, "Keyboard", "Electronics", "Like New")
    create_listing(seller_id, "Biology Guide", "Textbooks", "Like New")

    return seller_id


def login_as(client, user_id):
    """Authenticate a test session before accessing protected listing routes."""
    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["email"] = f"user{user_id}@mymail.nyp.edu.sg"
        session["display_name"] = f"User {user_id}"
        session["role"] = "user"


def test_homepage_shows_individual_clear_filter_links(tmp_path, monkeypatch):
    """Homepage should show clear links for active category and condition filters."""
    monkeypatch.setattr(app_db, "DATABASE", tmp_path / "test_swaplah.db")

    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    seller_id = seed_filter_listings()
    login_as(client, seller_id)

    response = client.get("/?category=Electronics&condition=Like+New")

    assert response.status_code == 200
    assert b'aria-label="Clear category filter"' in response.data
    assert b'aria-label="Clear condition filter"' in response.data


def test_clear_category_keeps_condition_filter_homepage(tmp_path, monkeypatch):
    """Clearing category should keep condition filter active on homepage."""
    monkeypatch.setattr(app_db, "DATABASE", tmp_path / "test_swaplah.db")

    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    seller_id = seed_filter_listings()
    login_as(client, seller_id)

    response = client.get("/?condition=Like+New")

    assert response.status_code == 200
    assert b"Keyboard" in response.data
    assert b"Biology Guide" in response.data
    assert b"Calculator" not in response.data


def test_clear_condition_keeps_category_filter_homepage(tmp_path, monkeypatch):
    """Clearing condition should keep category filter active on homepage."""
    monkeypatch.setattr(app_db, "DATABASE", tmp_path / "test_swaplah.db")

    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    seller_id = seed_filter_listings()
    login_as(client, seller_id)

    response = client.get("/?category=Electronics")

    assert response.status_code == 200
    assert b"Calculator" in response.data
    assert b"Keyboard" in response.data
    assert b"Biology Guide" not in response.data


def test_clear_category_keeps_condition_filter_api(tmp_path, monkeypatch):
    """API should keep condition filter when category is cleared."""
    monkeypatch.setattr(app_db, "DATABASE", tmp_path / "test_swaplah.db")

    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    seller_id = seed_filter_listings()
    login_as(client, seller_id)

    response = client.get("/api/listings?condition=Like+New")

    assert response.status_code == 200

    data = response.get_json()
    titles = [listing["title"] for listing in data["listings"]]

    assert "Keyboard" in titles
    assert "Biology Guide" in titles
    assert "Calculator" not in titles
    assert data["totalListings"] == 2


def test_clear_condition_keeps_category_filter_api(tmp_path, monkeypatch):
    """API should keep category filter when condition is cleared."""
    monkeypatch.setattr(app_db, "DATABASE", tmp_path / "test_swaplah.db")

    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    seller_id = seed_filter_listings()
    login_as(client, seller_id)

    response = client.get("/api/listings?category=Electronics")

    assert response.status_code == 200

    data = response.get_json()
    titles = [listing["title"] for listing in data["listings"]]

    assert "Calculator" in titles
    assert "Keyboard" in titles
    assert "Biology Guide" not in titles
    assert data["totalListings"] == 2
