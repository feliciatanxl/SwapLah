"""API/template tests for editable profile picture and cover image."""

# pylint: disable=redefined-outer-name

import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module
from app import create_app

PROFILE_URL = "https://cdn.example.com/avatar.png"
COVER_URL = "https://cdn.example.com/cover.png"


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a Flask test client backed by an isolated temporary database."""
    test_db = tmp_path / "test_profile_images.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client, test_db


def create_user(test_db, student_id, display_name="ImageUser"):
    """Insert a user and return its ID."""
    conn = sqlite3.connect(test_db)
    cursor = conn.execute(
        """
        INSERT INTO users (student_id, first_name, last_name, display_name,
                           email, contact_number, password_hash, role, status)
        VALUES (?, 'Image', 'User', ?, ?, '91234567', ?, 'user', 'Active')
        """,
        (student_id, display_name, f"{student_id.lower()}@mymail.nyp.edu.sg",
         generate_password_hash("Password1")),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def login_as(test_client, user_id):
    """Log a user into the test session."""
    with test_client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["display_name"] = "ImageUser"


def edit_form(**overrides):
    """Return a complete edit-profile form payload."""
    form = {
        "first_name": "Image",
        "last_name": "User",
        "display_name": "ImageUser",
        "contact_number": "91234567",
        "password": "",
        "confirm_password": "",
        "profile_image_url": "",
        "cover_image_url": "",
    }
    form.update(overrides)
    return form


def get_images(test_db, user_id):
    """Return the stored (profile, cover) image URLs for a user."""
    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT profile_image_url, cover_image_url FROM users WHERE id=?",
        (user_id,),
    ).fetchone()
    conn.close()
    return row


def test_saved_profile_image_appears_on_own_profile(client):
    """A saved profile image renders on the owner's profile page."""
    test_client, test_db = client
    user_id = create_user(test_db, "S7000001")
    login_as(test_client, user_id)

    test_client.post("/profile/edit", data=edit_form(profile_image_url=PROFILE_URL))

    html = test_client.get("/profile").get_data(as_text=True)
    assert PROFILE_URL in html


def test_saved_cover_image_appears_on_own_profile(client):
    """A saved cover image renders on the owner's profile page."""
    test_client, test_db = client
    user_id = create_user(test_db, "S7000002")
    login_as(test_client, user_id)

    test_client.post("/profile/edit", data=edit_form(cover_image_url=COVER_URL))

    html = test_client.get("/profile").get_data(as_text=True)
    assert COVER_URL in html


def test_saved_images_appear_on_public_profile(client):
    """A saved profile image renders when another user views the profile."""
    test_client, test_db = client
    owner_id = create_user(test_db, "S7000003", "Owner")
    viewer_id = create_user(test_db, "S7000004", "Viewer")

    login_as(test_client, owner_id)
    test_client.post("/profile/edit", data=edit_form(profile_image_url=PROFILE_URL))

    login_as(test_client, viewer_id)
    html = test_client.get(f"/profile/{owner_id}").get_data(as_text=True)
    assert PROFILE_URL in html


def test_blank_fields_use_generated_avatar_default(client):
    """With no configured images the profile falls back to a generated avatar."""
    test_client, test_db = client
    user_id = create_user(test_db, "S7000005", "Defaulty")
    login_as(test_client, user_id)

    html = test_client.get("/profile").get_data(as_text=True)
    assert "ui-avatars.com" in html
    assert PROFILE_URL not in html


def test_invalid_url_scheme_is_rejected(client):
    """A javascript: URL is rejected and not stored."""
    test_client, test_db = client
    user_id = create_user(test_db, "S7000006")
    login_as(test_client, user_id)

    response = test_client.post(
        "/profile/edit",
        data=edit_form(profile_image_url="javascript:alert(1)"),
        follow_redirects=True,
    )

    assert b"Image URL must start with http" in response.data
    assert get_images(test_db, user_id)["profile_image_url"] is None


def test_logged_out_user_cannot_edit_images(client):
    """A logged-out edit attempt redirects to login and stores nothing."""
    test_client, test_db = client
    user_id = create_user(test_db, "S7000007")

    response = test_client.post(
        "/profile/edit",
        data=edit_form(profile_image_url=PROFILE_URL),
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    assert get_images(test_db, user_id)["profile_image_url"] is None


def test_user_cannot_change_another_users_images(client):
    """Editing only affects the logged-in user's own images."""
    test_client, test_db = client
    owner_id = create_user(test_db, "S7000008", "Owner")
    other_id = create_user(test_db, "S7000009", "Other")

    login_as(test_client, owner_id)
    test_client.post("/profile/edit", data=edit_form(profile_image_url=PROFILE_URL))

    login_as(test_client, other_id)
    test_client.post("/profile/edit", data=edit_form(profile_image_url=COVER_URL))

    assert get_images(test_db, owner_id)["profile_image_url"] == PROFILE_URL
    assert get_images(test_db, other_id)["profile_image_url"] == COVER_URL


def test_updating_normal_fields_preserves_images(client):
    """Re-submitting the edit form with a new name keeps the saved images."""
    test_client, test_db = client
    user_id = create_user(test_db, "S7000010")
    login_as(test_client, user_id)

    test_client.post(
        "/profile/edit",
        data=edit_form(profile_image_url=PROFILE_URL, cover_image_url=COVER_URL),
    )
    test_client.post(
        "/profile/edit",
        data=edit_form(
            display_name="RenamedUser",
            profile_image_url=PROFILE_URL,
            cover_image_url=COVER_URL,
        ),
    )

    images = get_images(test_db, user_id)
    assert images["profile_image_url"] == PROFILE_URL
    assert images["cover_image_url"] == COVER_URL


def test_edit_form_prefills_existing_image_urls(client):
    """The edit form pre-fills previously saved image URLs."""
    test_client, test_db = client
    user_id = create_user(test_db, "S7000011")
    login_as(test_client, user_id)
    test_client.post("/profile/edit", data=edit_form(profile_image_url=PROFILE_URL))

    html = test_client.get("/profile/edit").get_data(as_text=True)
    assert PROFILE_URL in html
    assert 'name="profile_image_url"' in html
    assert 'name="cover_image_url"' in html
