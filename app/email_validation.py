"""Canonical student-email validation and SQLite guard definitions."""

STUDENT_EMAIL_DOMAIN = "mymail.nyp.edu.sg"
STUDENT_EMAIL_SUFFIX = f"@{STUDENT_EMAIL_DOMAIN}"
STUDENT_EMAIL_SUFFIX_LENGTH = len(STUDENT_EMAIL_SUFFIX)
EMAIL_INSERT_TRIGGER_NAME = "validate_users_email_insert"
EMAIL_UPDATE_TRIGGER_NAME = "validate_users_email_update"

STUDENT_EMAIL_CHECK_SQL = (
    "email = trim(email) "
    f"AND length(email) > {STUDENT_EMAIL_SUFFIX_LENGTH} "
    f"AND substr(lower(email), -{STUDENT_EMAIL_SUFFIX_LENGTH}) = "
    f"'{STUDENT_EMAIL_SUFFIX}' "
    "AND instr(substr(email, 1, length(email) - "
    f"{STUDENT_EMAIL_SUFFIX_LENGTH}), '@') = 0"
)

NEW_STUDENT_EMAIL_CHECK_SQL = (
    "NEW.email = trim(NEW.email) "
    f"AND length(NEW.email) > {STUDENT_EMAIL_SUFFIX_LENGTH} "
    f"AND substr(lower(NEW.email), -{STUDENT_EMAIL_SUFFIX_LENGTH}) = "
    f"'{STUDENT_EMAIL_SUFFIX}' "
    "AND instr(substr(NEW.email, 1, length(NEW.email) - "
    f"{STUDENT_EMAIL_SUFFIX_LENGTH}), '@') = 0"
)

CREATE_USERS_EMAIL_INSERT_TRIGGER_SQL = f"""
CREATE TRIGGER {EMAIL_INSERT_TRIGGER_NAME}
BEFORE INSERT ON users
FOR EACH ROW
WHEN NOT ({NEW_STUDENT_EMAIL_CHECK_SQL})
BEGIN
    SELECT RAISE(ABORT, 'email must end exactly with {STUDENT_EMAIL_SUFFIX}');
END
"""

CREATE_USERS_EMAIL_UPDATE_TRIGGER_SQL = f"""
CREATE TRIGGER {EMAIL_UPDATE_TRIGGER_NAME}
BEFORE UPDATE OF email ON users
FOR EACH ROW
WHEN NOT ({NEW_STUDENT_EMAIL_CHECK_SQL})
BEGIN
    SELECT RAISE(ABORT, 'email must end exactly with {STUDENT_EMAIL_SUFFIX}');
END
"""


def normalize_student_email(email):
    """Return a canonical student email or raise ValueError when invalid."""
    if not isinstance(email, str):
        raise ValueError(f"Email must end exactly with {STUDENT_EMAIL_SUFFIX}")

    normalized = email.strip().lower()
    local_part, separator, domain = normalized.rpartition("@")

    if (
        not separator
        or not local_part
        or "@" in local_part
        or domain != STUDENT_EMAIL_DOMAIN
    ):
        raise ValueError(f"Email must end exactly with {STUDENT_EMAIL_SUFFIX}")

    return normalized


def is_valid_student_email(email):
    """Return True only for a valid student email address."""
    try:
        normalize_student_email(email)
    except ValueError:
        return False
    return True


def install_user_email_guards(conn):
    """Replace email guard triggers without rebuilding the users table."""
    conn.execute(f"DROP TRIGGER IF EXISTS {EMAIL_INSERT_TRIGGER_NAME}")
    conn.execute(f"DROP TRIGGER IF EXISTS {EMAIL_UPDATE_TRIGGER_NAME}")
    conn.execute(CREATE_USERS_EMAIL_INSERT_TRIGGER_SQL)
    conn.execute(CREATE_USERS_EMAIL_UPDATE_TRIGGER_SQL)
