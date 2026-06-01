import sqlite3
from pathlib import Path

DATABASE = Path(__file__).resolve().parent.parent / "swaplah.db"


def get_db_connection():
    """Return a SQLite database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create database tables if they do not exist."""
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL UNIQUE,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            display_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            contact_number TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            status TEXT NOT NULL DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def get_user_by_email(email):
    """Retrieve one user by email using a parameterized query."""
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE email = :email",
        {"email": email},
    ).fetchone()
    conn.close()
    return user