"""Unit tests for the transaction-history API blueprint."""

# pylint: disable=redefined-outer-name

import pytest
from flask import Flask

from app.routes import history as history_routes


@pytest.fixture
def client():
    """Create a minimal Flask app containing only the history blueprint."""
    flask_app = Flask(__name__)
    flask_app.config.update(SECRET_KEY="test-secret-key", TESTING=True)
    flask_app.register_blueprint(history_routes.history_bp)

    with flask_app.test_client() as test_client:
        yield test_client


def login_as(test_client, user_id=42):
    """Set a logged-in user ID in the test session."""
    with test_client.session_transaction() as sess:
        sess["user_id"] = user_id


def transaction_row(**overrides):
    """Return a complete database-style transaction row."""
    row = {
        "id": 7,
        "offer_id": 11,
        "transaction_type": "cash",
        "amount": 18.5,
        "created_at": "2026-07-03 14:30:00",
        "listing_title": "Route Test Item",
        "listing_category": "Electronics",
        "counterparty_display_name": "Counterparty",
    }
    row.update(overrides)
    return row


def test_transactions_require_authentication(client, monkeypatch):
    """Logged-out requests are rejected without querying history."""
    monkeypatch.setattr(
        history_routes.db_module,
        "get_transactions_for_user",
        lambda *_args: pytest.fail("database should not be queried"),
    )

    response = client.get("/api/transactions?role=buyer")

    assert response.status_code == 401
    assert response.get_json() == {"error": "Login required"}


def test_transactions_default_to_buyer_role(client, monkeypatch):
    """Omitting the role parameter requests the logged-in user's purchases."""
    requested = []
    monkeypatch.setattr(
        history_routes.db_module,
        "get_transactions_for_user",
        lambda user_id, role: requested.append((user_id, role)) or [],
    )
    login_as(client, user_id=73)

    response = client.get("/api/transactions")

    assert response.status_code == 200
    assert response.get_json() == {"transactions": []}
    assert requested == [(73, "buyer")]


def test_transactions_pass_seller_role_to_database(client, monkeypatch):
    """The seller role is forwarded with the authenticated user ID."""
    requested = []
    monkeypatch.setattr(
        history_routes.db_module,
        "get_transactions_for_user",
        lambda user_id, role: requested.append((user_id, role)) or [],
    )
    login_as(client, user_id=91)

    response = client.get("/api/transactions?role=seller")

    assert response.status_code == 200
    assert requested == [(91, "seller")]


@pytest.mark.parametrize("role", ["admin", "BUYER", "", " buyer "])
def test_transactions_reject_invalid_roles(client, monkeypatch, role):
    """Only the exact buyer and seller role values are accepted."""
    monkeypatch.setattr(
        history_routes.db_module,
        "get_transactions_for_user",
        lambda *_args: pytest.fail("database should not be queried"),
    )
    login_as(client)

    response = client.get("/api/transactions", query_string={"role": role})

    assert response.status_code == 400
    assert response.get_json() == {"error": "role must be 'buyer' or 'seller'"}


def test_transactions_serialise_database_fields(client, monkeypatch):
    """Database snake_case fields are exposed using the page's JSON contract."""
    monkeypatch.setattr(
        history_routes.db_module,
        "get_transactions_for_user",
        lambda _user_id, _role: [transaction_row()],
    )
    login_as(client)

    response = client.get("/api/transactions?role=buyer")

    assert response.status_code == 200
    assert response.get_json() == {
        "transactions": [
            {
                "id": 7,
                "offerId": 11,
                "transactionType": "cash",
                "amount": 18.5,
                "createdAt": "2026-07-03 14:30:00",
                "listingTitle": "Route Test Item",
                "listingCategory": "Electronics",
                "counterpartyDisplayName": "Counterparty",
            }
        ]
    }


def test_transactions_serialise_nullable_amount(client, monkeypatch):
    """A swap transaction's nullable amount remains JSON null."""
    monkeypatch.setattr(
        history_routes.db_module,
        "get_transactions_for_user",
        lambda _user_id, _role: [
            transaction_row(transaction_type="swap", amount=None)
        ],
    )
    login_as(client)

    response = client.get("/api/transactions?role=buyer")

    transaction = response.get_json()["transactions"][0]
    assert transaction["transactionType"] == "swap"
    assert transaction["amount"] is None


def test_transactions_preserve_database_order(client, monkeypatch):
    """The route does not disturb the database's newest-first ordering."""
    monkeypatch.setattr(
        history_routes.db_module,
        "get_transactions_for_user",
        lambda _user_id, _role: [
            transaction_row(id=2, listing_title="Newest"),
            transaction_row(id=1, listing_title="Oldest"),
        ],
    )
    login_as(client)

    response = client.get("/api/transactions?role=seller")

    titles = [item["listingTitle"] for item in response.get_json()["transactions"]]
    assert titles == ["Newest", "Oldest"]
