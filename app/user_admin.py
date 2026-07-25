"""
User administration functions.

Provides admin-level user listing and status management, separate from db.py
to keep the latter under 1000 lines.
"""

from .db import get_db_connection, get_user_by_id
from .email_validation import normalize_student_email

# --- SQL constants ------------------------------------------------------------

GET_ALL_USERS_SQL = """
SELECT
    id,
    student_id,
    first_name,
    last_name,
    display_name,
    email,
    contact_number,
    role,
    status,
    created_at
FROM users
ORDER BY created_at DESC
"""

UPDATE_USER_STATUS_SQL = """
UPDATE users
SET status = :status
WHERE id = :user_id
"""


# --- Public functions ---------------------------------------------------------

def get_all_users():
    """
    Retrieve all users ordered newest first.

    Returns:
        list[dict]: Each dict contains user fields excluding password_hash.
    """
    conn = get_db_connection()
    rows = conn.execute(GET_ALL_USERS_SQL).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_user_status(user_id, new_status):
    """
    Update a user's status to 'Active' or 'Suspended'.

    Args:
        user_id (int): ID of the user to update.
        new_status (str): Must be 'Active' or 'Suspended'.

    Returns:
        dict | None: The updated user dict (same shape as get_user_by_id)
                      or None if the user does not exist.

    Raises:
        ValueError: If new_status is not 'Active' or 'Suspended'.
    """
    if new_status not in ("Active", "Suspended"):
        raise ValueError("Invalid status")

    conn = get_db_connection()
    cursor = conn.execute(UPDATE_USER_STATUS_SQL, {"status": new_status, "user_id": user_id})
    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        return None

    # Re-fetch the user (excludes password_hash)
    return get_user_by_id(user_id)


def get_user_for_password_reset(email, student_id, contact_number):
    """Return {id, status} only when email, Student ID and contact match one user.

    The email must be an exact normalized NYP student address. Comparisons use
    parameterised queries; no role or status is read for authorisation.
    """
    try:
        normalized_email = normalize_student_email(email)
    except ValueError:
        return None

    conn = get_db_connection()
    row = conn.execute(
        "SELECT id, status FROM users "
        "WHERE lower(email)=? AND student_id=? AND contact_number=?",
        (normalized_email, (student_id or "").strip(), (contact_number or "").strip()),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_user_password(user_id, password_hash):
    """Update only a user's password hash; role and status are left unchanged."""
    conn = get_db_connection()
    conn.execute(
        "UPDATE users SET password_hash=? WHERE id=?",
        (password_hash, user_id),
    )
    conn.commit()
    conn.close()
