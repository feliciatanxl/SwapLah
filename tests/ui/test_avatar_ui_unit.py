"""Fast UI tests for the navbar avatar and profile cover layering."""

# pylint: disable=redefined-outer-name

import sqlite3
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

import app as app_module
import app.db as db_module
from app import create_app

STYLE_CSS = Path(app_module.__file__).resolve().parent / "static" / "css" / "style.css"
PROFILE_URL = "https://cdn.example.com/avatar.png"
COVER_URL = "https://cdn.example.com/cover.png"


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a Flask test client backed by an isolated temporary database."""
    test_db = tmp_path / "avatar_ui_unit.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client, test_db


def create_user(test_db, student_id, profile_image_url=None, cover_image_url=None):
    """Insert a user and return its ID."""
    conn = sqlite3.connect(test_db)
    cursor = conn.execute(
        """
        INSERT INTO users (student_id, first_name, last_name, display_name, email,
                           contact_number, password_hash, role, status,
                           profile_image_url, cover_image_url)
        VALUES (?, 'Nav', 'User', 'NavUser', ?, '91234567', ?, 'user', 'Active', ?, ?)
        """,
        (student_id, f"{student_id.lower()}@mymail.nyp.edu.sg",
         generate_password_hash("Password1"), profile_image_url, cover_image_url),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def login_as(test_client, user_id):
    """Log a user into the test session."""
    with test_client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["display_name"] = "NavUser"


# --- Navbar --------------------------------------------------------------

def test_navbar_shows_saved_profile_image(client):
    """The navbar trigger shows the saved image as a circular cover image."""
    test_client, test_db = client
    user_id = create_user(test_db, "S9300001", profile_image_url=PROFILE_URL)
    login_as(test_client, user_id)

    page = test_client.get("/history").get_data(as_text=True)
    assert 'class="avatar-mini avatar-img"' in page
    assert PROFILE_URL in page


def test_navbar_uses_initials_fallback_without_image(client):
    """The navbar falls back to the generated initials circle when no image is set."""
    test_client, test_db = client
    user_id = create_user(test_db, "S9300002")
    login_as(test_client, user_id)

    page = test_client.get("/history").get_data(as_text=True)
    assert '<span class="avatar-mini">' in page
    assert "avatar-img" not in page


def test_navbar_reflects_image_saved_on_next_response(client):
    """Saving a new profile image shows it in the navbar on the following request."""
    test_client, test_db = client
    user_id = create_user(test_db, "S9300003")
    login_as(test_client, user_id)

    test_client.post(
        "/profile/edit",
        data={
            "first_name": "Nav", "last_name": "User", "display_name": "NavUser",
            "contact_number": "91234567", "password": "", "confirm_password": "",
            "profile_image_url": PROFILE_URL, "cover_image_url": "",
        },
    )

    page = test_client.get("/history").get_data(as_text=True)
    assert PROFILE_URL in page
    assert 'class="avatar-mini avatar-img"' in page


def test_logged_out_navbar_does_not_fail(client):
    """A logged-out auth page renders without an account avatar and without error."""
    test_client, _test_db = client

    response = test_client.get("/login")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "avatar-img" not in page
    assert "Log In" in page


# --- Profile cover layering ---------------------------------------------

def test_cover_renders_behind_profile_identity(client):
    """The cover image markup precedes the identity section (lower layer)."""
    test_client, test_db = client
    user_id = create_user(test_db, "S9300004", cover_image_url=COVER_URL)
    login_as(test_client, user_id)

    page = test_client.get("/profile").get_data(as_text=True)
    assert page.index("profile-header") < page.index("profile-cover-img")
    assert page.index("profile-cover-img") < page.index("profile-identity")


def test_profile_layout_classes_exist(client):
    """The expected layering classes are present on the profile page."""
    test_client, test_db = client
    user_id = create_user(test_db, "S9300005", profile_image_url=PROFILE_URL, cover_image_url=COVER_URL)
    login_as(test_client, user_id)

    page = test_client.get("/profile").get_data(as_text=True)
    for token in ("profile-header", "profile-cover-img", "profile-identity", "profile-avatar"):
        assert token in page


def _css_block(name):
    """Return the CSS declaration block for a selector."""
    css = STYLE_CSS.read_text(encoding="utf-8")
    start = css.index(name + " {")
    return css[start:css.index("}", start)]


def test_css_establishes_cover_below_identity():
    """The stylesheet layers the identity above the cover with a positioned card."""
    assert "position: relative" in _css_block(".profile-card")
    identity = _css_block(".profile-identity")
    assert "position: relative" in identity
    assert "z-index: 2" in identity
    assert "z-index: 0" in _css_block(".profile-cover-img")


def test_css_defines_avatar_image_cover():
    """The shared avatar image class uses object-fit: cover."""
    assert "object-fit: cover" in _css_block(".avatar-img")
