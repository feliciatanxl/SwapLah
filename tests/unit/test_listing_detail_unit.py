"""Unit tests for listing detail routes."""

# pylint: disable=redefined-outer-name

import pytest

import app as app_module
from app import create_app
from app.routes import listing as listing_routes


@pytest.fixture
def client():
    """Create a Flask test client."""
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client


def fake_listing():
    """Return a fake listing detail record."""
    return {
        "id": 1,
        "title": "Casio Calculator",
        "description": "Good condition calculator",
        "price": "25.00",
        "category": "Electronics",
        "condition": "Good",
        "image_url": "[\"https://example.com/calculator.jpg\"]",
        "images": [
            "https://example.com/calculator.jpg",
            "https://example.com/calculator-2.jpg",
        ],
        "image": "https://example.com/calculator.jpg",
        "listing_date": "2026-06-04 10:00:00",
        "last_modified_timestamp": "2026-06-04 10:00:00",
        "seller_display_name": "Felicia",
        "seller_email": "felicia@mymail.nyp.edu.sg",
        "seller_contact_number": "91234567",
    }


def test_api_get_listing_detail_success(client, monkeypatch):
    """Return listing detail JSON when the listing exists."""
    monkeypatch.setattr(
        listing_routes,
        "get_listing_by_id",
        lambda listing_id: fake_listing(),
    )

    response = client.get("/api/listings/1")

    assert response.status_code == 200

    data = response.get_json()

    assert data["listing"]["id"] == 1
    assert data["listing"]["title"] == "Casio Calculator"
    assert data["listing"]["description"] == "Good condition calculator"
    assert data["listing"]["price"] == "25.00"
    assert data["listing"]["category"] == "Electronics"
    assert data["listing"]["condition"] == "Good"
    assert data["listing"]["seller"]["displayName"] == "Felicia"
    assert data["listing"]["seller"]["email"] == "felicia@mymail.nyp.edu.sg"
    assert data["listing"]["seller"]["contactNumber"] == "91234567"


def test_api_get_listing_detail_not_found(client, monkeypatch):
    """Return 404 when listing detail is unavailable."""
    monkeypatch.setattr(
        listing_routes,
        "get_listing_by_id",
        lambda listing_id: None,
    )

    response = client.get("/api/listings/999999")

    assert response.status_code == 404

    data = response.get_json()

    assert data["error"] == "Listing not found or unavailable."


def test_listing_detail_page_success(client, monkeypatch):
    """Render listing detail page when listing exists."""
    monkeypatch.setattr(
        app_module,
        "get_listing_by_id",
        lambda listing_id: fake_listing(),
    )

    response = client.get("/listing/1")

    assert response.status_code == 200
    assert b"Casio Calculator" in response.data
    assert b"Good condition calculator" in response.data
    assert b"25.00" in response.data
    assert b"Electronics" in response.data
    assert b"Good" in response.data
    assert b"Felicia" in response.data
    assert b"felicia@mymail.nyp.edu.sg" in response.data
    assert b"91234567" in response.data


def test_listing_detail_page_not_found(client, monkeypatch):
    """Render 404 page when listing does not exist."""
    monkeypatch.setattr(
        app_module,
        "get_listing_by_id",
        lambda listing_id: None,
    )

    response = client.get("/listing/999999")

    assert response.status_code == 404
    assert b"This listing does not exist or is no longer available." in response.data
