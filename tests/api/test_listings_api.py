"""API integration tests for Sprint 2 listing endpoints."""

# pylint: disable=redefined-outer-name,too-many-arguments,too-many-positional-arguments

import sqlite3
import time

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app


DEFAULT_PASSWORD = "Password123"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Create a Flask test client using an isolated SQLite database."""
    test_db = tmp_path / "test_listings_api.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "listing-api-test-secret"

    with flask_app.test_client() as test_client:
        yield test_client


def seed_user(
    student_id="S76543210",
    email="seller@mymail.nyp.edu.sg",
    display_name="SellerUser",
    status="Active",
):
    """Create one user and return the generated user ID."""
    conn = sqlite3.connect(db_module.DATABASE)
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
            "Listing",
            "Tester",
            display_name,
            email,
            "91234567",
            generate_password_hash(DEFAULT_PASSWORD),
            "user",
            status,
        ),
    )
    conn.commit()
    conn.close()
    return cursor.lastrowid


def login_as(client, user_id):
    """Log in through the Flask session for API endpoint testing."""
    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["email"] = f"user{user_id}@mymail.nyp.edu.sg"
        session["display_name"] = f"User {user_id}"
        session["role"] = "user"
        session["last_activity"] = time.time()


def seed_listing(
    seller_id,
    title="Casio Calculator",
    description="Good condition calculator for DSA.",
    price="25.00",
    category="Electronics",
    condition="Good",
    image_url="https://example.com/calculator.jpg",
    status="Active",
):
    """Create one listing and optionally update its status."""
    listing = db_module.create_listing(
        seller_id=seller_id,
        title=title,
        description=description,
        price=price,
        category=category,
        condition=condition,
        image_url=image_url,
    )

    if status != "Active":
        conn = sqlite3.connect(db_module.DATABASE)
        conn.execute(
            "UPDATE listings SET status = ? WHERE id = ?",
            (status, listing["id"]),
        )
        conn.commit()
        conn.close()
        listing["status"] = status

    return listing


def valid_listing_payload(title="Mechanical Keyboard"):
    """Return a valid listing API payload."""
    return {
        "title": title,
        "description": "RGB keyboard in good condition.",
        "price": "45",
        "category": "Electronics",
        "condition": "Like New",
        "imageUrl": "https://example.com/keyboard.jpg",
    }


def test_get_active_listings_returns_pagination_metadata(client):
    """GET /api/listings returns only active listings with pagination metadata."""
    seller_id = seed_user()
    login_as(client, seller_id)

    for index in range(12):
        seed_listing(
            seller_id=seller_id,
            title=f"Listing {index}",
            category="Electronics",
            condition="Good",
        )

    seed_listing(
        seller_id=seller_id,
        title="Deleted Listing",
        category="Electronics",
        condition="Good",
        status="Deleted",
    )

    response = client.get("/api/listings?page=2")

    assert response.status_code == 200

    data = response.get_json()

    assert data["page"] == 2
    assert data["perPage"] == 10
    assert data["totalListings"] == 12
    assert data["totalPages"] == 2
    assert len(data["listings"]) == 2
    assert all(listing["status"] == "Active" for listing in data["listings"])


def test_get_active_listings_searches_title_and_description(client):
    """GET /api/listings?search= matches listing title and description."""
    seller_id = seed_user()
    login_as(client, seller_id)
    seed_listing(
        seller_id=seller_id,
        title="Python Textbook",
        description="Useful for programming revision.",
        category="Textbooks",
    )
    seed_listing(
        seller_id=seller_id,
        title="Scientific Calculator",
        description="Useful for mathematics revision.",
        category="Electronics",
    )

    response = client.get("/api/listings?search=python")

    assert response.status_code == 200

    data = response.get_json()

    assert data["totalListings"] == 1
    assert data["listings"][0]["title"] == "Python Textbook"


def test_get_active_listings_filters_by_category_and_condition(client):
    """GET /api/listings filters by Category and Condition together."""
    seller_id = seed_user()
    login_as(client, seller_id)
    seed_listing(
        seller_id=seller_id,
        title="Like New Mouse",
        category="Electronics",
        condition="Like New",
    )
    seed_listing(
        seller_id=seller_id,
        title="Fair Mouse",
        category="Electronics",
        condition="Fair",
    )
    seed_listing(
        seller_id=seller_id,
        title="Like New Notes",
        category="Textbooks",
        condition="Like New",
    )

    response = client.get("/api/listings?category=Electronics&condition=Like%20New")

    assert response.status_code == 200

    data = response.get_json()

    assert data["totalListings"] == 1
    assert data["listings"][0]["title"] == "Like New Mouse"


def test_get_listing_detail_returns_seller_contact_information(client):
    """GET /api/listings/<id> returns listing details and seller contact info."""
    seller_id = seed_user(
        email="contact@mymail.nyp.edu.sg",
        display_name="Contact Seller",
    )
    login_as(client, seller_id)
    listing = seed_listing(seller_id=seller_id)

    response = client.get(f"/api/listings/{listing['id']}")

    assert response.status_code == 200

    data = response.get_json()
    listing_data = data["listing"]

    assert listing_data["title"] == "Casio Calculator"
    assert listing_data["seller"]["displayName"] == "Contact Seller"
    assert listing_data["seller"]["email"] == "contact@mymail.nyp.edu.sg"
    assert listing_data["seller"]["contactNumber"] == "91234567"


def test_get_listing_detail_returns_404_for_missing_listing(client):
    """GET /api/listings/<id> returns 404 for unavailable listing."""
    user_id = seed_user()
    login_as(client, user_id)

    response = client.get("/api/listings/999")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Listing not found or unavailable."


def test_get_my_listings_returns_only_authenticated_users_active_listings(client):
    """GET /api/my-listings returns only active listings owned by the session user."""
    seller_id = seed_user(
        student_id="S55555555",
        email="mine@mymail.nyp.edu.sg",
        display_name="Mine",
    )
    other_seller_id = seed_user(
        student_id="S66666666",
        email="otherlistings@mymail.nyp.edu.sg",
        display_name="Other Listings",
    )
    own_listing = seed_listing(seller_id=seller_id, title="My Active Listing")
    seed_listing(seller_id=other_seller_id, title="Other User Listing")
    seed_listing(seller_id=seller_id, title="My Deleted Listing", status="Deleted")
    login_as(client, seller_id)

    response = client.get("/api/my-listings")

    assert response.status_code == 200
    assert response.get_json() == [
        {"id": own_listing["id"], "title": "My Active Listing"},
    ]


def test_get_my_listings_returns_empty_list_for_user_without_listings(client):
    """GET /api/my-listings returns an empty list for a user without active listings."""
    seller_id = seed_user(
        student_id="S77777777",
        email="empty@mymail.nyp.edu.sg",
        display_name="Empty",
    )
    login_as(client, seller_id)

    response = client.get("/api/my-listings")

    assert response.status_code == 200
    assert response.get_json() == []


def test_get_my_listings_rejects_unauthenticated_user(client):
    """GET /api/my-listings requires an authenticated user."""
    response = client.get("/api/my-listings")

    assert response.status_code == 401
    assert response.get_json()["error"] == "Not logged in."


def test_get_my_listings_excludes_soft_deleted_listings(client):
    """GET /api/my-listings excludes soft-deleted listings from active choices."""
    seller_id = seed_user(
        student_id="S88888888",
        email="deleted@mymail.nyp.edu.sg",
        display_name="Deleted",
    )
    seed_listing(seller_id=seller_id, title="Deleted Personal Listing", status="Deleted")
    login_as(client, seller_id)

    response = client.get("/api/my-listings")

    assert response.status_code == 200
    assert response.get_json() == []


def test_get_my_listings_does_not_expose_sensitive_account_data(client):
    """GET /api/my-listings returns only the fields required by the swap dropdown."""
    seller_id = seed_user(
        student_id="S99999999",
        email="private@mymail.nyp.edu.sg",
        display_name="Private",
    )
    seed_listing(seller_id=seller_id, title="Minimal Listing")
    login_as(client, seller_id)

    response = client.get("/api/my-listings")

    assert response.status_code == 200

    [listing] = response.get_json()
    assert set(listing) == {"id", "title"}
    assert "private@mymail.nyp.edu.sg" not in response.get_data(as_text=True)
    assert "91234567" not in response.get_data(as_text=True)


def test_create_listing_success_for_logged_in_seller(client):
    """POST /api/listings creates a listing for a logged-in seller."""
    seller_id = seed_user()
    login_as(client, seller_id)

    response = client.post("/api/listings", json=valid_listing_payload())

    assert response.status_code == 201

    data = response.get_json()

    assert data["message"] == "Listing created successfully."
    assert data["listing"]["sellerId"] == seller_id
    assert data["listing"]["title"] == "Mechanical Keyboard"
    assert data["listing"]["price"] == "45.00"


def test_create_listing_rejects_unauthenticated_user(client):
    """POST /api/listings rejects users who are not logged in."""
    response = client.post("/api/listings", json=valid_listing_payload())

    assert response.status_code == 401
    assert response.get_json()["error"] == "You must be logged in to create a listing."


def test_create_listing_rejects_invalid_price(client):
    """POST /api/listings validates price input."""
    seller_id = seed_user()
    login_as(client, seller_id)

    payload = valid_listing_payload()
    payload["price"] = "not-a-price"

    response = client.post("/api/listings", json=payload)

    assert response.status_code == 400
    assert response.get_json()["error"] == "Price must be a number, Free, or Swap Only."


def test_update_listing_success_for_owner(client):
    """PUT /api/listings/<id> updates a listing when the user is the owner."""
    seller_id = seed_user()
    listing = seed_listing(seller_id=seller_id)
    login_as(client, seller_id)

    payload = valid_listing_payload(title="Updated Keyboard")
    response = client.put(f"/api/listings/{listing['id']}", json=payload)

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == "Listing updated successfully."
    assert data["listing"]["title"] == "Updated Keyboard"
    assert data["listing"]["sellerId"] == seller_id
    assert data["listing"]["lastModifiedTimestamp"] is not None


def test_update_listing_rejects_non_owner(client):
    """PUT /api/listings/<id> rejects users who do not own the listing."""
    owner_id = seed_user(
        student_id="S11111111",
        email="owner@mymail.nyp.edu.sg",
        display_name="Owner",
    )
    other_user_id = seed_user(
        student_id="S22222222",
        email="other@mymail.nyp.edu.sg",
        display_name="Other",
    )
    listing = seed_listing(seller_id=owner_id)
    login_as(client, other_user_id)

    response = client.put(f"/api/listings/{listing['id']}", json=valid_listing_payload())

    assert response.status_code == 403
    assert response.get_json()["error"] == "You are not allowed to edit this listing."


def test_delete_listing_success_for_owner(client):
    """DELETE /api/listings/<id> soft-deletes a listing owned by the user."""
    seller_id = seed_user()
    listing = seed_listing(seller_id=seller_id)
    login_as(client, seller_id)

    response = client.delete(f"/api/listings/{listing['id']}")

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == "Listing deleted successfully."
    assert data["listing"]["status"] == "Deleted"

    detail_response = client.get(f"/api/listings/{listing['id']}")
    assert detail_response.status_code == 404


def test_delete_listing_rejects_non_owner(client):
    """DELETE /api/listings/<id> rejects users who do not own the listing."""
    owner_id = seed_user(
        student_id="S33333333",
        email="deleteowner@mymail.nyp.edu.sg",
        display_name="Delete Owner",
    )
    other_user_id = seed_user(
        student_id="S44444444",
        email="deleteother@mymail.nyp.edu.sg",
        display_name="Delete Other",
    )
    listing = seed_listing(seller_id=owner_id)
    login_as(client, other_user_id)

    response = client.delete(f"/api/listings/{listing['id']}")

    assert response.status_code == 403
    assert response.get_json()["error"] == "You are not allowed to delete this listing."

def test_create_listing_rejects_missing_required_fields(client):
    """POST /api/listings rejects a payload with a missing required field."""
    seller_id = seed_user()
    login_as(client, seller_id)

    payload = valid_listing_payload()
    payload.pop("title")

    response = client.post("/api/listings", json=payload)

    assert response.status_code == 400
    assert response.get_json()["error"] == "All fields are required."


def test_create_listing_rejects_invalid_request_body(client):
    """POST /api/listings rejects malformed JSON request data."""
    seller_id = seed_user()
    login_as(client, seller_id)

    response = client.post(
        "/api/listings",
        data="this is not valid JSON",
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid request body."


def test_update_listing_rejects_unauthenticated_user(client):
    """PUT /api/listings/<id> requires an authenticated user."""
    seller_id = seed_user()
    listing = seed_listing(seller_id=seller_id)

    response = client.put(
        f"/api/listings/{listing['id']}",
        json=valid_listing_payload(),
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == (
        "You must be logged in to edit a listing."
    )


def test_update_listing_returns_404_for_missing_listing(client):
    """PUT /api/listings/<id> returns 404 when the listing does not exist."""
    seller_id = seed_user()
    login_as(client, seller_id)

    response = client.put(
        "/api/listings/999999",
        json=valid_listing_payload(),
    )

    assert response.status_code == 404
    assert response.get_json()["error"] == (
        "Listing not found or has already been deleted."
    )


def test_delete_listing_rejects_unauthenticated_user(client):
    """DELETE /api/listings/<id> requires an authenticated user."""
    seller_id = seed_user()
    listing = seed_listing(seller_id=seller_id)

    response = client.delete(f"/api/listings/{listing['id']}")

    assert response.status_code == 401
    assert response.get_json()["error"] == (
        "You must be logged in to delete a listing."
    )


def test_delete_listing_returns_404_for_missing_listing(client):
    """DELETE /api/listings/<id> returns 404 when the listing does not exist."""
    seller_id = seed_user()
    login_as(client, seller_id)

    response = client.delete("/api/listings/999999")

    assert response.status_code == 404
    assert response.get_json()["error"] == (
        "Listing not found or has already been deleted."
    )


def test_get_active_listings_returns_empty_list_for_no_match(client):
    """GET /api/listings returns an empty page when no listing matches."""
    seller_id = seed_user()
    login_as(client, seller_id)
    seed_listing(
        seller_id=seller_id,
        title="Python Textbook",
    )

    response = client.get(
        "/api/listings?search=nonexistent-keyword"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["listings"] == []
    assert data["page"] == 1
    assert data["perPage"] == 10
    assert data["totalListings"] == 0
    assert data["totalPages"] == 1


def test_get_active_listings_requires_login(client):
    """Logged-out users cannot browse listing data through the API."""
    response = client.get("/api/listings")

    assert response.status_code == 401
    assert response.get_json()["error"] == "You must be logged in to view listings."
