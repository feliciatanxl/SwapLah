"""
Unit tests for:
  GET /profile
  GET /profile/<user_id>

All DB calls are monkeypatched — no real database needed.
"""
import app as app_module


FAKE_USER = {
    "id": 1,
    "student_id": "S1000001",
    "first_name": "Alice",
    "last_name": "Tan",
    "display_name": "Alice",
    "email": "alice@mymail.nyp.edu.sg",
    "contact_number": "91234567",
    "role": "user",
    "status": "Active",
    "created_at": "2026-01-01 10:00:00",
}

FAKE_OTHER_USER = {**FAKE_USER, "id": 2, "display_name": "Bob"}

FAKE_STATS_WITH_REVIEWS = {
    "average_rating": 4.5,
    "review_count": 2,
    "active_count": 0,
    "total_sales": 0,
    "sold_count": 0,
    "trust_badge": "New Seller",
    "response_rate": None,
}
FAKE_STATS_NO_REVIEWS = {
    "average_rating": None,
    "review_count": 0,
    "active_count": 0,
    "total_sales": 0,
    "sold_count": 0,
    "trust_badge": "New Seller",
    "response_rate": None,
}

FAKE_REVIEWS = [
    {
        "id": 1,
        "reviewed_user_id": 1,
        "reviewer_id": 2,
        "rating": 4,
        "comment": "Reliable seller.",
        "created_at": "2026-01-02 10:00:00",
        "reviewer_name": "Bob",
    },
]


def _client(monkeypatch):
    """Create a test client with init_db monkeypatched to avoid touching disk."""
    monkeypatch.setattr(app_module, "init_db", lambda: None)
    monkeypatch.setattr(app_module, "get_active_listings_by_seller", lambda uid: [])
    monkeypatch.setattr(app_module, "get_sold_listings_by_seller", lambda uid: [])
    flask_app = app_module.create_app()
    flask_app.config["TESTING"] = True
    return flask_app.test_client()


def login_as(client, user_id):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


# ===========================================================================
# GET /profile — own profile
# ===========================================================================

def test_own_profile_shows_edit_and_account_details(monkeypatch):
    """Own profile must show the Edit Profile button and Account Details card."""
    client = _client(monkeypatch)
    login_as(client, 1)
    monkeypatch.setattr(app_module, "get_user_by_id", lambda uid: FAKE_USER)
    monkeypatch.setattr(app_module, "get_user_profile_stats", lambda uid: FAKE_STATS_WITH_REVIEWS)
    monkeypatch.setattr(app_module, "get_reviews_for_user", lambda uid: FAKE_REVIEWS)

    resp = client.get("/profile")

    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Edit profile" in html
    assert "Account Details" in html
    assert "Reviews (2)" in html


def test_own_profile_shows_empty_state_with_no_reviews(monkeypatch):
    """A user with zero reviews must see the 'No reviews yet' empty state."""
    client = _client(monkeypatch)
    login_as(client, 1)
    monkeypatch.setattr(app_module, "get_user_by_id", lambda uid: FAKE_USER)
    monkeypatch.setattr(app_module, "get_user_profile_stats", lambda uid: FAKE_STATS_NO_REVIEWS)
    monkeypatch.setattr(app_module, "get_reviews_for_user", lambda uid: [])

    resp = client.get("/profile")
    html = resp.get_data(as_text=True)

    assert "No reviews yet" in html
    assert "Reviews (0)" in html


def test_profile_redirects_when_logged_out(monkeypatch):
    """An unauthenticated request to /profile must redirect to login."""
    client = _client(monkeypatch)

    resp = client.get("/profile")

    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


# ===========================================================================
# GET /profile/<user_id> — another user's profile
# ===========================================================================

def test_other_profile_hides_edit_and_account_details(monkeypatch):
    """Another user's profile must hide the Edit Profile button and Account Details."""
    client = _client(monkeypatch)
    login_as(client, 1)
    monkeypatch.setattr(
        app_module, "get_user_by_id",
        lambda uid: FAKE_OTHER_USER if uid == 2 else FAKE_USER,
    )
    monkeypatch.setattr(app_module, "get_user_profile_stats", lambda uid: FAKE_STATS_WITH_REVIEWS)
    monkeypatch.setattr(app_module, "get_reviews_for_user", lambda uid: FAKE_REVIEWS)

    resp = client.get("/profile/2")

    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Edit profile" not in html
    assert "Account Details" not in html


def test_other_profile_shows_average_rating(monkeypatch):
    """Another user's profile shows their real average rating and review count."""
    client = _client(monkeypatch)
    login_as(client, 1)
    monkeypatch.setattr(app_module, "get_user_by_id", lambda uid: FAKE_OTHER_USER)
    monkeypatch.setattr(app_module, "get_user_profile_stats", lambda uid: FAKE_STATS_WITH_REVIEWS)
    monkeypatch.setattr(app_module, "get_reviews_for_user", lambda uid: FAKE_REVIEWS)

    resp = client.get("/profile/2")
    html = resp.get_data(as_text=True)

    assert "4.5" in html
    assert "Reviews (2)" in html


def test_viewing_own_id_via_other_profile_route_redirects_to_profile(monkeypatch):
    """Requesting /profile/<own_id> must redirect to /profile instead of rendering."""
    client = _client(monkeypatch)
    login_as(client, 1)

    resp = client.get("/profile/1")

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")


def test_unknown_user_id_redirects_to_index(monkeypatch):
    """Requesting a profile for a user that does not exist must redirect away."""
    client = _client(monkeypatch)
    login_as(client, 1)
    monkeypatch.setattr(app_module, "get_user_by_id", lambda uid: None)

    resp = client.get("/profile/999999")

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")


def test_logged_out_user_can_view_another_users_profile(monkeypatch):
    """Viewing another user's profile does not require being logged in."""
    client = _client(monkeypatch)
    monkeypatch.setattr(app_module, "get_user_by_id", lambda uid: FAKE_OTHER_USER)
    monkeypatch.setattr(app_module, "get_user_profile_stats", lambda uid: FAKE_STATS_WITH_REVIEWS)
    monkeypatch.setattr(app_module, "get_reviews_for_user", lambda uid: FAKE_REVIEWS)

    resp = client.get("/profile/2")

    assert resp.status_code == 200
