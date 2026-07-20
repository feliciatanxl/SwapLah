from functools import wraps
from flask import flash, redirect, session, url_for

from app.db import get_user_by_id


def _is_admin_user(user):
    return (
        user is not None
        and user["role"] == "admin"
        and user["status"] == "Active"
    )


def _require_admin_response():
    user_id = session.get("user_id")

    if not user_id:
        flash("Please log in as an administrator.", "danger")
        return redirect(url_for("login"))

    user = get_user_by_id(user_id)

    if not _is_admin_user(user):
        return "Forbidden", 403

    return None


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        response = _require_admin_response()

        if response:
            return response

        return view_func(*args, **kwargs)

    return wrapper