"""Shared pytest configuration for SwapLah tests."""

import pytest


@pytest.fixture(autouse=True)
def test_secret_key(monkeypatch):
    """Provide an obvious test-only Flask secret key."""
    monkeypatch.setenv("SECRET_KEY", "test-only-secret-key")
