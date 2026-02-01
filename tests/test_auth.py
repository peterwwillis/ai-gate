"""Tests for session management and authentication."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gatewayd.auth import SessionManager


def test_session_creation():
    """Test creating a new session."""
    manager = SessionManager()
    token = manager.create_session("default")

    assert token is not None
    assert len(token) > 0

    session = manager.validate_token(token)
    assert session is not None
    assert session["tenant_id"] == "default"


def test_enrollment_verification():
    """Test enrollment secret verification."""
    manager = SessionManager()

    assert manager.verify_enrollment("default", "test-secret-123") is True
    assert manager.verify_enrollment("default", "wrong-secret") is False
    assert manager.verify_enrollment("nonexistent", "any-secret") is False


def test_token_validation():
    """Test token validation."""
    manager = SessionManager()
    token = manager.create_session("default")

    session = manager.validate_token(token)
    assert session is not None

    # Invalid token should return None
    invalid_session = manager.validate_token("invalid-token-xyz")
    assert invalid_session is None


def test_session_revocation():
    """Test revoking a session."""
    manager = SessionManager()
    token = manager.create_session("default")

    assert manager.validate_token(token) is not None

    manager.revoke_session(token)
    assert manager.validate_token(token) is None


if __name__ == "__main__":
    test_session_creation()
    print("✓ test_session_creation")

    test_enrollment_verification()
    print("✓ test_enrollment_verification")

    test_token_validation()
    print("✓ test_token_validation")

    test_session_revocation()
    print("✓ test_session_revocation")

    print("\nAll auth tests passed!")
