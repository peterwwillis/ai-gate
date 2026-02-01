"""Policy engine for classifying and gating requests."""

import os
import json
import logging
from typing import Dict, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class SecurityMode(Enum):
    """Security enforcement mode."""
    STRICT = "strict"
    CAUTIOUS = "cautious"


class PolicyEngine:
    """Classifies requests and determines if approval is required."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize policy engine."""
        self.config_path = config_path or os.getenv("GATEWAY_CONFIG_PATH", "config/gateway.yaml")
        self.tenant_policies: Dict[str, Dict[str, Any]] = {}
        self._load_policies()

    def _load_policies(self):
        """Load tenant policies from config."""
        config_file = os.getenv("POLICY_CONFIG_FILE", "config/policies.json")
        if os.path.exists(config_file):
            with open(config_file) as f:
                self.tenant_policies = json.load(f)
            logger.info(f"Loaded policies from {config_file}")
        else:
            # Default policy: Strict mode for all tenants
            self.tenant_policies = {
                "default": {
                    "mode": "strict",
                    "exceptions": [],
                }
            }

    def requires_approval(
        self,
        tenant_id: str,
        action_type: Any,  # ActionType enum
        provider: str,
        method: str,
        path: str,
    ) -> bool:
        """Determine if a request requires approval."""

        # Reads never require approval
        if action_type.value == "read":
            return False

        # Get tenant policy
        policy = self.tenant_policies.get(tenant_id, self.tenant_policies.get("default"))
        mode = policy.get("mode", "strict")

        # In Strict mode, all writes require approval
        if mode == "strict":
            return True

        # In Cautious mode, check for exceptions
        if mode == "cautious":
            return not self._is_exception(provider, method, path, policy)

        return True

    def _is_exception(
        self,
        provider: str,
        method: str,
        path: str,
        policy: Dict[str, Any],
    ) -> bool:
        """Check if request matches a cautious-mode exception."""
        exceptions = policy.get("exceptions", [])

        for exception in exceptions:
            if self._matches_exception(provider, method, path, exception):
                return True

        return False

    def _matches_exception(
        self,
        provider: str,
        method: str,
        path: str,
        exception: Dict[str, Any],
    ) -> bool:
        """Check if request matches an exception rule."""
        exc_provider = exception.get("provider")
        exc_methods = exception.get("methods", [])
        exc_paths = exception.get("paths", [])

        if exc_provider and exc_provider != provider:
            return False

        if exc_methods and method not in exc_methods:
            return False

        if exc_paths:
            for path_pattern in exc_paths:
                if self._path_matches(path, path_pattern):
                    return True
            return False

        return True

    def _path_matches(self, path: str, pattern: str) -> bool:
        """Check if path matches pattern (supports wildcards)."""
        import fnmatch
        return fnmatch.fnmatch(path, pattern)

    def classify_cli_command(self, provider: str, command: str) -> str:
        """Classify CLI command as read or write."""
        # Based on DESIGN.md heuristics
        command_lower = command.lower()

        if provider == "aws":
            if any(command_lower.startswith(p) for p in ["list", "describe", "get"]):
                return "read"
            return "write"

        elif provider == "gcp":
            if command_lower in ["list", "describe"]:
                return "read"
            if any(command_lower.startswith(p) for p in ["create", "delete", "update", "deploy", "set", "enable", "disable"]):
                return "write"
            return "read"

        elif provider == "terraform":
            if any(p in command_lower for p in ["apply", "destroy"]):
                return "write"
            return "read"

        elif provider == "kubectl":
            if any(p in command_lower for p in ["apply", "delete", "scale", "patch", "set image", "rollout restart"]):
                return "write"
            return "read"

        elif provider == "gh":
            # GitHub mutations
            mutating = ["create", "delete", "update", "edit", "merge", "close", "open", "fork"]
            if any(m in command_lower for m in mutating):
                return "write"
            return "read"

        elif provider == "curl":
            # curl: non-GET is write
            if any(method in command_lower for method in ["-X POST", "-X PUT", "-X PATCH", "-X DELETE", "-d "]):
                return "write"
            return "read"

        # Default: conservative (treat as write)
        return "write"
