"""Unit tests for suspended user login helper."""

from app import _is_suspended_user


def test_is_suspended_user_returns_true_for_suspended_status():
    """Suspended users should be detected."""
    user = {"status": "Suspended"}

    assert _is_suspended_user(user) is True


def test_is_suspended_user_returns_false_for_active_status():
    """Active users should not be treated as suspended."""
    user = {"status": "Active"}

    assert _is_suspended_user(user) is False