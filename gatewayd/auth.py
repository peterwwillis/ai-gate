"""Session and authentication management."""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional
import json


class SessionManager:
    """Manages agent sessions and authentication."""

    def __init__(self):
        """Initialize session manager."""
        self.sessions: Dict[str, Dict] = {}
        self.enrollments: Dict[str, str] = {}
        self._load_enrollments()

    def _load_enrollments(self):
        """Load enrollment secrets from file or environment."""
        enrollment_file = os.getenv("ENROLLMENT_SECRETS_FILE", "config/enrollments.json")
        if os.path.exists(enrollment_file):
            with open(enrollment_file) as f:
                self.enrollments = json.load(f)
        else:
            # Default test enrollments
            self.enrollments = {
                "default": hashlib.sha256(b"test-secret-123").hexdigest(),
                "test": hashlib.sha256(b"test-enrollment").hexdigest(),
            }

    def verify_enrollment(self, tenant_id: str, enrollment_secret: str) -> bool:
        """Verify tenant enrollment secret."""
        if tenant_id not in self.enrollments:
            return False

        secret_hash = hashlib.sha256(enrollment_secret.encode()).hexdigest()
        return secret_hash == self.enrollments[tenant_id]

    def create_session(self, tenant_id: str, ttl_seconds: int = 3600) -> str:
        """Create a new session token."""
        token = secrets.token_urlsafe(32)
        self.sessions[token] = {
            "tenant_id": tenant_id,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat(),
        }
        return token

    def validate_token(self, token: str) -> Optional[Dict]:
        """Validate a session token."""
        if token not in self.sessions:
            return None

        session = self.sessions[token]
        expires_at = datetime.fromisoformat(session["expires_at"])

        if datetime.utcnow() > expires_at:
            del self.sessions[token]
            return None

        return session

    def revoke_session(self, token: str) -> bool:
        """Revoke a session token."""
        if token in self.sessions:
            del self.sessions[token]
            return True
        return False
