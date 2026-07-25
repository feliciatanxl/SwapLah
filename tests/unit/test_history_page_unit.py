"""Fast UI regression tests for the transaction-history page contract."""

# pylint: disable=redefined-outer-name

import pytest

import app as app_module
import app.db as db_module
from app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a Flask client backed by a temporary database."""
    test_db = tmp_path / "history_page_unit.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)
    monkeypatch.setattr(app_module, "init_db", db_module.init_db)

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client


def login_as(test_client, user_id=1):
    """Set a logged-in user ID in the test session."""
    with test_client.session_transaction() as sess:
        sess["user_id"] = user_id


def test_history_page_redirects_logged_out_user(client):
    """The history page remains protected for logged-out visitors."""
    response = client.get("/history")

    assert response.status_code == 302
    assert response.location.endswith("/login")


def test_history_page_renders_tables_stats_and_empty_states(client):
    """All DOM hooks used while loading both histories are rendered."""
    login_as(client)

    response = client.get("/history")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    for element_id in (
        "statTotalEarned",
        "statTotalSpent",
        "statCompletedDeals",
        "buyerTableCard",
        "sellerTableCard",
        "buyerEmptyState",
        "sellerEmptyState",
        "buyerHistoryBody",
        "sellerHistoryBody",
        "historyError",
        "historyFlash",
    ):
        assert f'id="{element_id}"' in page


def test_history_page_loads_buyer_and_seller_api_roles(client):
    """Page JavaScript requests both sides of a user's transaction history."""
    login_as(client)

    page = client.get("/history").get_data(as_text=True)

    assert 'loadHistory("buyer"' in page
    assert 'loadHistory("seller"' in page
    assert 'fetch("/api/transactions?role=" + role)' in page


def test_history_page_review_modal_has_complete_form(client):
    """The review modal offers ratings one to five and an optional comment."""
    login_as(client)

    page = client.get("/history").get_data(as_text=True)

    assert 'id="reviewBuyerModal"' in page
    assert 'id="reviewBuyerName"' in page
    assert 'id="reviewRating"' in page
    assert 'id="reviewComment"' in page
    assert 'id="confirmReviewBtn"' in page
    assert 'id="reviewModalError"' in page
    for rating in range(1, 6):
        assert f'<option value="{rating}">' in page


def test_history_page_posts_reviews_using_offer_id(client):
    """The modal submits to the unified review API with its offer ID."""
    login_as(client)

    page = client.get("/history").get_data(as_text=True)

    assert 'data-offer-id="' in page
    assert 'fetch("/api/reviews", {' in page
    assert "offer_id: Number(pendingReviewOfferId)" in page
    assert "rating: rating" in page
    assert "comment: comment" in page


def test_history_page_does_not_use_removed_review_routes(client):
    """The old transaction-specific review routes are not reintroduced."""
    login_as(client)

    page = client.get("/history").get_data(as_text=True)

    assert "/buyer-review" not in page
    assert '/review", {' not in page
