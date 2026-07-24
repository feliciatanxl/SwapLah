"""Fast UI regression tests for the history review-button rendering contract."""

# pylint: disable=redefined-outer-name

import pytest

import app as app_module
import app.db as db_module
from app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a Flask client backed by a temporary database."""
    test_db = tmp_path / "history_review_button_unit.db"
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


def _history_page(client):
    login_as(client)
    return client.get("/history").get_data(as_text=True)


def test_review_cell_has_reviewed_branch(client):
    """The review cell chooses between a review button and a reviewed badge."""
    page = _history_page(client)
    assert "if (t.hasReviewed)" in page
    assert "reviewedBadge()" in page
    assert "Leave a review" in page


def test_reviewed_badge_is_non_clickable(client):
    """The reviewed state renders a badge span, not a button."""
    page = _history_page(client)
    assert "function reviewedBadge()" in page
    assert "Reviewed</span>" in page


def test_missing_offer_id_hides_review_action(client):
    """A transaction without an offer id shows no review control."""
    page = _history_page(client)
    assert "t.offerId === null || t.offerId === undefined" in page


def test_history_dates_render_in_singapore_time(client):
    """Client-side date formatting pins the timezone to Asia/Singapore."""
    page = _history_page(client)
    assert 'timeZone: "Asia/Singapore"' in page
