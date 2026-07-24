"""Unit tests for listing API routes."""

# pylint: disable=missing-function-docstring,redefined-outer-name,too-many-positional-arguments

import pytest

from app import create_app
from app.routes import listing as listing_routes

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def login_test_user(client):
    with client.session_transaction() as session:
        session["user_id"] = 1


def fake_create_listing(seller_id, title, description, price, category, condition, image_url):
    return {
        "id": 1,
        "seller_id": seller_id,
        "title": title,
        "description": description,
        "price": price,
        "category": category,
        "item_condition": condition,
        "image_url": image_url,
        "listing_date": "2026-06-03 20:00:00",
        "last_modified_timestamp": "2026-06-03 20:00:00"
    }

def fake_soft_delete_listing(listing_id, seller_id):
    """Return a fake soft-deleted listing."""
    return {
        "id": listing_id,
        "seller_id": seller_id,
        "title": "Casio Calculator",
        "description": "Good condition calculator",
        "price": "25.00",
        "category": "Electronics",
        "item_condition": "Good",
        "image_url": "[\"https://example.com/calculator.jpg\"]",
        "listing_date": "2026-06-03 20:00:00",
        "last_modified_timestamp": "2026-06-03 20:10:00",
        "status": "Deleted",
    }, None


def test_create_listing_success(client, monkeypatch):
    login_test_user(client)

    monkeypatch.setattr(listing_routes, "create_listing", fake_create_listing)

    response = client.post("/api/listings", json={
        "title": "Casio Calculator",
        "description": "Good condition calculator",
        "price": "25",
        "category": "Electronics",
        "condition": "Good",
        "imageUrl": "[\"https://example.com/calculator.jpg\"]"
    })

    assert response.status_code == 201

    data = response.get_json()

    assert data["message"] == "Listing created successfully."
    assert data["listing"]["id"] == 1
    assert data["listing"]["sellerId"] == 1
    assert data["listing"]["title"] == "Casio Calculator"
    assert data["listing"]["category"] == "Electronics"
    assert data["listing"]["condition"] == "Good"
    assert data["listing"]["listingDate"] is not None
    assert data["listing"]["lastModifiedTimestamp"] is not None


def test_create_listing_free_price(client, monkeypatch):
    login_test_user(client)

    monkeypatch.setattr(listing_routes, "create_listing", fake_create_listing)

    response = client.post("/api/listings", json={
        "title": "Free Notes",
        "description": "Giving away notes",
        "price": "Free",
        "category": "Textbooks",
        "condition": "Good",
        "imageUrl": "[\"https://example.com/notes.jpg\"]"
    })

    assert response.status_code == 201

    data = response.get_json()

    assert data["listing"]["price"] == "Free"


def test_create_listing_swap_only_price(client, monkeypatch):
    login_test_user(client)

    monkeypatch.setattr(listing_routes, "create_listing", fake_create_listing)

    response = client.post("/api/listings", json={
        "title": "Mouse",
        "description": "Swap for stationery",
        "price": "Swap Only",
        "category": "Electronics",
        "condition": "Good",
        "imageUrl": "[\"https://example.com/mouse.jpg\"]"
    })

    assert response.status_code == 201

    data = response.get_json()

    assert data["listing"]["price"] == "Swap Only"


def test_create_listing_missing_required_field(client):
    login_test_user(client)

    response = client.post("/api/listings", json={
        "title": "",
        "description": "Missing title test",
        "price": "25",
        "category": "Electronics",
        "condition": "Good",
        "imageUrl": "[\"https://example.com/item.jpg\"]"
    })

    assert response.status_code == 400

    data = response.get_json()

    assert "error" in data


def test_create_listing_invalid_price(client):
    login_test_user(client)

    response = client.post("/api/listings", json={
        "title": "Calculator",
        "description": "Invalid price test",
        "price": "abc",
        "category": "Electronics",
        "condition": "Good",
        "imageUrl": "[\"https://example.com/item.jpg\"]"
    })

    assert response.status_code == 400

    data = response.get_json()

    assert "error" in data


def test_create_listing_invalid_condition(client):
    login_test_user(client)

    response = client.post("/api/listings", json={
        "title": "Calculator",
        "description": "Invalid condition test",
        "price": "25",
        "category": "Electronics",
        "condition": "Terrible",
        "imageUrl": "[\"https://example.com/item.jpg\"]"
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid item condition."


def test_create_listing_long_decimal_price(client):
    login_test_user(client)

    response = client.post("/api/listings", json={
        "title": "Calculator",
        "description": "Long decimal price test",
        "price": "3.333333333",
        "category": "Electronics",
        "condition": "Good",
        "imageUrl": "[\"https://example.com/item.jpg\"]"
    })

    assert response.status_code == 400

    data = response.get_json()

    assert "error" in data


def test_create_listing_not_logged_in(client):
    response = client.post("/api/listings", json={
        "title": "Laptop Stand",
        "description": "Adjustable laptop stand",
        "price": "8",
        "category": "Electronics",
        "condition": "Good",
        "imageUrl": "[\"https://example.com/stand.jpg\"]"
    })

    assert response.status_code == 401

    data = response.get_json()

    assert "error" in data


def test_create_listing_invalid_request_body(client):
    login_test_user(client)

    response = client.post(
        "/api/listings",
        data="not json",
        content_type="text/plain"
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "error" in data


def test_update_listing_rejects_invalid_condition(client):
    login_test_user(client)

    response = client.put("/api/listings/1", json={
        "title": "Calculator",
        "description": "Invalid condition update",
        "price": "25",
        "category": "Electronics",
        "condition": "Terrible",
        "imageUrl": "[\"https://example.com/item.jpg\"]"
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid item condition."


def test_delete_listing_success(client, monkeypatch):
    """Owner can soft-delete their own listing."""
    login_test_user(client)

    monkeypatch.setattr(
        listing_routes,
        "soft_delete_listing",
        fake_soft_delete_listing,
    )

    response = client.delete("/api/listings/1")

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == "Listing deleted successfully."
    assert data["listing"]["id"] == 1
    assert data["listing"]["sellerId"] == 1
    assert data["listing"]["status"] == "Deleted"


def test_delete_listing_not_logged_in(client):
    """Unauthenticated user cannot delete a listing."""
    response = client.delete("/api/listings/1")

    assert response.status_code == 401

    data = response.get_json()

    assert data["error"] == "You must be logged in to delete a listing."


def test_delete_listing_not_found(client, monkeypatch):
    """Return 404 when deleting a missing listing."""
    login_test_user(client)

    monkeypatch.setattr(
        listing_routes,
        "soft_delete_listing",
        lambda listing_id, seller_id: (None, "not_found"),
    )

    response = client.delete("/api/listings/999")

    assert response.status_code == 404

    data = response.get_json()

    assert data["error"] == "Listing not found or has already been deleted."


def test_delete_listing_forbidden_for_non_owner(client, monkeypatch):
    """Return 403 when user does not own the listing."""
    login_test_user(client)

    monkeypatch.setattr(
        listing_routes,
        "soft_delete_listing",
        lambda listing_id, seller_id: (None, "forbidden"),
    )

    response = client.delete("/api/listings/1")

    assert response.status_code == 403

    data = response.get_json()

    assert data["error"] == "You are not allowed to delete this listing."
