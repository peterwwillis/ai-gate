"""GCP CLI wrapper."""

import os
import sys
from typing import List, Dict, Any
from base import CLIWrapper, ActionType


class GCPWrapper(CLIWrapper):
    """Wrapper for GCP gcloud CLI."""

    COMMAND_NAME = "gcloud"

    def classify_action(self) -> ActionType:
        """Classify gcloud command as read or write."""
        if not self.args:
            return ActionType.READ

        # Extract operation from args (may have flags)
        operation = self.args[0].lower()

        # Read operations
        read_ops = ["list", "describe"]
        if any(operation == op for op in read_ops):
            return ActionType.READ

        # Mutating operations
        write_ops = ["create", "delete", "update", "deploy", "set", "enable", "disable"]
        if any(operation == op for op in write_ops):
            return ActionType.WRITE

        return ActionType.READ

    def _inject_credentials(self, env: Dict[str, str], credentials: Dict[str, Any]):
        """Inject GCP credentials into environment."""
        if "credentials_json" in credentials:
            # Write service account JSON to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                f.write(credentials["credentials_json"])
                env["GOOGLE_APPLICATION_CREDENTIALS"] = f.name
        if "project_id" in credentials:
            env["GCLOUD_PROJECT"] = credentials["project_id"]


def main():
    """GCP wrapper entry point."""
    wrapper = GCPWrapper(sys.argv[1:])
    return wrapper.run()


if __name__ == "__main__":
    sys.exit(main())
