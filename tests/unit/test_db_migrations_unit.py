"""Unit tests for additive SQLite migrations run during init_db."""

# pylint: disable=redefined-outer-name

import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app.db as db_module


def _legacy_schema(db_path):
    """Create the pre-migration users and reviews tables with one row each."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT NOT NULL UNIQUE,
            first_name TEXT NOT NULL, last_name TEXT NOT NULL, display_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE, contact_number TEXT NOT NULL,
            password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user',
            status TEXT NOT NULL DEFAULT 'Active', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
        """
    )
    conn.execute(
        """
        CREATE TABLE reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT, reviewed_user_id INTEGER NOT NULL,
            reviewer_id INTEGER, rating INTEGER NOT NULL, comment TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
        """
    )
    conn.execute(
        "INSERT INTO users (student_id, first_name, last_name, display_name, email, "
        "contact_number, password_hash) VALUES "
        "('S1000001','Legacy','User','LegacyUser','s1000001@mymail.nyp.edu.sg','91234567',?)",
        (generate_password_hash("Password1"),),
    )
    conn.execute(
        "INSERT INTO reviews (reviewed_user_id, reviewer_id, rating, comment) "
        "VALUES (1, NULL, 5, 'Legacy review')"
    )
    conn.commit()
    conn.close()


@pytest.fixture
def migrated_db(tmp_path, monkeypatch):
    """Return a legacy database path after running init_db migrations on it."""
    db_path = tmp_path / "legacy.db"
    _legacy_schema(db_path)
    monkeypatch.setattr(db_module, "DATABASE", db_path)
    db_module.init_db()
    return db_path


def _columns(db_path, table):
    conn = sqlite3.connect(db_path)
    cols = [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]
    conn.close()
    return cols


def test_migration_adds_profile_image_columns_without_dropping_users(migrated_db):
    """Image columns are added and the existing user row survives."""
    columns = _columns(migrated_db, "users")
    assert "profile_image_url" in columns
    assert "cover_image_url" in columns

    conn = sqlite3.connect(migrated_db)
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    assert count == 1


def test_migration_adds_reviews_offer_id_and_preserves_rows(migrated_db):
    """The reviews.offer_id column is added and legacy rows remain with NULL offer_id."""
    assert "offer_id" in _columns(migrated_db, "reviews")

    conn = sqlite3.connect(migrated_db)
    row = conn.execute("SELECT offer_id, comment FROM reviews").fetchone()
    conn.close()
    assert row[0] is None
    assert row[1] == "Legacy review"


def test_partial_unique_index_blocks_duplicate_offer_reviewer(migrated_db):
    """The partial unique index rejects a duplicate (offer_id, reviewer_id) pair."""
    conn = sqlite3.connect(migrated_db)
    conn.execute(
        "INSERT INTO reviews (offer_id, reviewed_user_id, reviewer_id, rating, comment) "
        "VALUES (10, 1, 2, 5, 'first')"
    )
    conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO reviews (offer_id, reviewed_user_id, reviewer_id, rating, comment) "
            "VALUES (10, 1, 2, 4, 'second')"
        )
        conn.commit()
    conn.close()


def test_partial_index_allows_multiple_null_offer_ids(migrated_db):
    """Legacy NULL-offer reviews are exempt from the uniqueness rule."""
    conn = sqlite3.connect(migrated_db)
    conn.execute(
        "INSERT INTO reviews (offer_id, reviewed_user_id, reviewer_id, rating, comment) "
        "VALUES (NULL, 1, 2, 5, 'a')"
    )
    conn.execute(
        "INSERT INTO reviews (offer_id, reviewed_user_id, reviewer_id, rating, comment) "
        "VALUES (NULL, 1, 2, 4, 'b')"
    )
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM reviews WHERE offer_id IS NULL").fetchone()[0]
    conn.close()
    assert count == 3  # one legacy + two new


def test_startup_does_not_create_password_reset_tokens_table(migrated_db):
    """The internal reset flow is session-based, so no token table is created."""
    conn = sqlite3.connect(migrated_db)
    tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    conn.close()
    assert "password_reset_tokens" not in tables


def test_migration_is_idempotent(migrated_db):
    """Running init_db again does not error or duplicate columns."""
    db_module.init_db()
    columns = _columns(migrated_db, "users")
    assert columns.count("profile_image_url") == 1
