"""Base wrapper for CLI commands."""

import logging
import os
import sys
import subprocess
import requests
from typing import List, Dict, Optional, Any
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Classification of actions."""
    READ = "read"
    WRITE = "write"


class CLIWrapper:
    """Base wrapper for CLI commands."""

    COMMAND_NAME = "generic"
    GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:5000")
    SESSION_TOKEN = os.getenv("GATEWAY_SESSION_TOKEN")
    TENANT_ID = os.getenv("GATEWAY_TENANT_ID", "default")

    def __init__(self, args: List[str]):
        """Initialize wrapper."""
        self.args = args
        self.gateway_session = None

    def run(self) -> int:
        """Execute wrapped command."""
        try:
            # Classify command
            action_type = self.classify_action()
            logger.info(f"{self.COMMAND_NAME} action: {action_type.value}")

            # Request approval if needed
            if action_type == ActionType.WRITE:
                if not self._request_approval(action_type):
                    logger.warning("Approval denied or not granted")
                    print("Error: Request not approved", file=sys.stderr)
                    return 1

            # Fetch credentials
            credentials = self._fetch_credentials()

            # Execute command
            return self._execute_command(credentials)

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            print(f"Error: {str(e)}", file=sys.stderr)
            return 1

    def classify_action(self) -> ActionType:
        """Classify command as read or write."""
        # Override in subclasses
        return ActionType.READ

    def _request_approval(self, action_type: ActionType) -> bool:
        """Request approval from gateway."""
        if not self.SESSION_TOKEN:
            logger.error("No session token available")
            return False

        headers = {
            "Authorization": f"Bearer {self.SESSION_TOKEN}",
            "Content-Type": "application/json",
        }

        payload = {
            "command": self.COMMAND_NAME,
            "args": self.args,
            "action_type": action_type.value,
            "details": {
                "tenant_id": self.TENANT_ID,
            },
        }

        try:
            # This would call a gateway endpoint to request approval
            # For now, simplified version
            response = requests.post(
                f"{self.GATEWAY_URL}/approvals/request",
                headers=headers,
                json=payload,
                timeout=3600,  # 1 hour timeout
            )

            if response.status_code != 200:
                logger.error(f"Approval request failed: {response.status_code}")
                return False

            approval_id = response.json().get("approval_id")
            logger.info(f"Approval requested: {approval_id}")

            # Wait for approval
            return self._wait_approval(approval_id)

        except Exception as e:
            logger.error(f"Error requesting approval: {str(e)}")
            return False

    def _wait_approval(self, approval_id: str) -> bool:
        """Wait for approval decision."""
        headers = {
            "Authorization": f"Bearer {self.SESSION_TOKEN}",
        }

        try:
            response = requests.get(
                f"{self.GATEWAY_URL}/approvals/{approval_id}/status",
                headers=headers,
                timeout=3600,
            )

            if response.status_code != 200:
                return False

            status = response.json().get("status")
            return status == "approved"

        except Exception as e:
            logger.error(f"Error checking approval status: {str(e)}")
            return False

    def _fetch_credentials(self) -> Optional[Dict[str, Any]]:
        """Fetch credentials from gateway."""
        if not self.SESSION_TOKEN:
            return None

        cred_selector = os.getenv("GATEWAY_CREDS")
        if not cred_selector:
            return None

        headers = {
            "Authorization": f"Bearer {self.SESSION_TOKEN}",
        }

        try:
            response = requests.post(
                f"{self.GATEWAY_URL}/credentials/fetch",
                headers=headers,
                json={"selector": cred_selector},
            )

            if response.status_code != 200:
                logger.error(f"Failed to fetch credentials: {response.status_code}")
                return None

            return response.json().get("credentials")

        except Exception as e:
            logger.error(f"Error fetching credentials: {str(e)}")
            return None

    def _execute_command(self, credentials: Optional[Dict[str, Any]]) -> int:
        """Execute the actual CLI command."""
        # Build command
        cmd = [self.COMMAND_NAME] + self.args

        # Prepare environment
        env = os.environ.copy()

        # Inject credentials as environment variables
        if credentials:
            self._inject_credentials(env, credentials)

        logger.info(f"Executing: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, env=env)
            return result.returncode

        except Exception as e:
            logger.error(f"Command execution failed: {str(e)}")
            return 1
        finally:
            # Scrub credentials from environment
            self._scrub_credentials(env)

    def _inject_credentials(self, env: Dict[str, str], credentials: Dict[str, Any]):
        """Inject credentials into environment."""
        # Override in subclasses
        pass

    def _scrub_credentials(self, env: Dict[str, str]):
        """Remove credential-related environment variables."""
        sensitive_keys = [k for k in env.keys() if any(s in k.upper() for s in ["KEY", "SECRET", "TOKEN", "PASSWORD"])]
        for key in sensitive_keys:
            env.pop(key, None)
