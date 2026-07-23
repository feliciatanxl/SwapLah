"""
User administration functions.

Provides admin-level user listing and status management, separate from db.py
to keep the latter under 1000 lines.
"""

from .db import get_db_connection, get_user_by_id

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