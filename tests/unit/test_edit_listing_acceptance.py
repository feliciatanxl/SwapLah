"""Acceptance tests for editing listings."""

# pylint: disable=missing-function-docstring

from app import create_app
from app import db

def create_test_user(email, student_id):
    conn = db.get_db_connection()

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


def login_as(client, user_id):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


def test_owner_can_update_listing_and_timestamp_changes(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATABASE", tmp_path / "test_swaplah.db")

    app = create_app()
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"

    client = app.test_client()

    seller_id = create_test_user("seller@mymail.nyp.edu.sg", "S001")

    listing = db.create_listing(
        seller_id=seller_id,
        title="Old Title",
        description="Old Description",
        price="10.00",
        category="Textbooks",
        condition="Good",
        image_url="test-image.jpg",
    )

    old_timestamp = listing["last_modified_timestamp"]

    login_as(client, seller_id)

    response = client.put(
        f"/api/listings/{listing['id']}",
        json={
            "title": "Updated Title",
            "description": "Updated Description",
            "price": "15",
            "category": "Electronics",
            "condition": "Like New",
            "imageUrl": "updated-image.jpg",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == "Listing updated successfully."
    assert data["listing"]["title"] == "Updated Title"
    assert data["listing"]["description"] == "Updated Description"
    assert data["listing"]["price"] == "15.00"
    assert data["listing"]["category"] == "Electronics"
    assert data["listing"]["condition"] == "Like New"
    assert data["listing"]["imageUrl"] == "updated-image.jpg"
    assert data["listing"]["lastModifiedTimestamp"] != old_timestamp

    updated_listing = db.get_listing_by_id(listing["id"])

    assert updated_listing["title"] == "Updated Title"
    assert updated_listing["description"] == "Updated Description"


def test_non_owner_cannot_update_listing(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATABASE", tmp_path / "test_swaplah.db")

    app = create_app()
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"

    client = app.test_client()

    seller_id = create_test_user("seller@mymail.nyp.edu.sg", "S001")
    other_user_id = create_test_user("other@mymail.nyp.edu.sg", "S002")

    listing = db.create_listing(
        seller_id=seller_id,
        title="Original Title",
        description="Original Description",
        price="10.00",
        category="Textbooks",
        condition="Good",
        image_url="test-image.jpg",
    )

    login_as(client, other_user_id)

    response = client.put(
        f"/api/listings/{listing['id']}",
        json={
            "title": "Hacked Title",
            "description": "Hacked Description",
            "price": "99",
            "category": "Electronics",
            "condition": "New",
            "imageUrl": "hacked-image.jpg",
        },
    )

    assert response.status_code == 403

    data = response.get_json()
    assert data["error"] == "You are not allowed to edit this listing."

    unchanged_listing = db.get_listing_by_id(listing["id"])
    assert unchanged_listing["title"] == "Original Title"


def test_missing_listing_returns_404_when_editing(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATABASE", tmp_path / "test_swaplah.db")

    app = create_app()
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"

    client = app.test_client()

    seller_id = create_test_user("seller@mymail.nyp.edu.sg", "S001")
    login_as(client, seller_id)

    response = client.put(
        "/api/listings/999",
        json={
            "title": "Updated Title",
            "description": "Updated Description",
            "price": "15",
            "category": "Electronics",
            "condition": "Like New",
            "imageUrl": "updated-image.jpg",
        },
    )

    assert response.status_code == 404

    data = response.get_json()
    assert data["error"] == "Listing not found or has already been deleted."


def test_deleted_listing_cannot_be_updated(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATABASE", tmp_path / "test_swaplah.db")

    app = create_app()
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"

    client = app.test_client()

    seller_id = create_test_user("seller@mymail.nyp.edu.sg", "S001")

    listing = db.create_listing(
        seller_id=seller_id,
        title="Deleted Listing",
        description="Deleted Description",
        price="10.00",
        category="Textbooks",
        condition="Good",
        image_url="test-image.jpg",
    )

    conn = db.get_db_connection()
    conn.execute(
        "UPDATE listings SET status = 'Deleted' WHERE id = ?",
        (listing["id"],),
    )
    conn.commit()
    conn.close()

    login_as(client, seller_id)

    response = client.put(
        f"/api/listings/{listing['id']}",
        json={
            "title": "Should Not Update",
            "description": "Should Not Update",
            "price": "15",
            "category": "Electronics",
            "condition": "Like New",
            "imageUrl": "updated-image.jpg",
        },
    )

    assert response.status_code == 404

    data = response.get_json()
    assert data["error"] == "Listing not found or has already been deleted."


def test_unauthenticated_user_cannot_update_listing(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATABASE", tmp_path / "test_swaplah.db")

    app = create_app()
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"

    client = app.test_client()

    seller_id = create_test_user("seller@mymail.nyp.edu.sg", "S001")

    listing = db.create_listing(
        seller_id=seller_id,
        title="Original Title",
        description="Original Description",
        price="10.00",
        category="Textbooks",
        condition="Good",
        image_url="test-image.jpg",
    )

    response = client.put(
        f"/api/listings/{listing['id']}",
        json={
            "title": "Updated Title",
            "description": "Updated Description",
            "price": "15",
            "category": "Electronics",
            "condition": "Like New",
            "imageUrl": "updated-image.jpg",
        },
    )

    assert response.status_code == 401

    data = response.get_json()
    assert data["error"] == "You must be logged in to edit a listing."


def test_update_listing_requires_all_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATABASE", tmp_path / "test_swaplah.db")

    app = create_app()
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"

    client = app.test_client()

    seller_id = create_test_user("seller@mymail.nyp.edu.sg", "S001")

    listing = db.create_listing(
        seller_id=seller_id,
        title="Original Title",
        description="Original Description",
        price="10.00",
        category="Textbooks",
        condition="Good",
        image_url="test-image.jpg",
    )

    login_as(client, seller_id)

    response = client.put(
        f"/api/listings/{listing['id']}",
        json={
            "title": "",
            "description": "Updated Description",
            "price": "15",
            "category": "Electronics",
            "condition": "Like New",
            "imageUrl": "updated-image.jpg",
        },
    )

    assert response.status_code == 400

    data = response.get_json()
    assert data["error"] == "All fields are required."


def test_update_listing_rejects_invalid_price(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATABASE", tmp_path / "test_swaplah.db")

    app = create_app()
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"

    client = app.test_client()

    seller_id = create_test_user("seller@mymail.nyp.edu.sg", "S001")

    listing = db.create_listing(
        seller_id=seller_id,
        title="Original Title",
        description="Original Description",
        price="10.00",
        category="Textbooks",
        condition="Good",
        image_url="test-image.jpg",
    )

    login_as(client, seller_id)

    response = client.put(
        f"/api/listings/{listing['id']}",
        json={
            "title": "Updated Title",
            "description": "Updated Description",
            "price": "abc",
            "category": "Electronics",
            "condition": "Like New",
            "imageUrl": "updated-image.jpg",
        },
    )

    assert response.status_code == 400

    data = response.get_json()
    assert data["error"] == "Price must be a number, Free, or Swap Only."
