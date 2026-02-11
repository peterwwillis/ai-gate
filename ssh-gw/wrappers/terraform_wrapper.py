"""Terraform CLI wrapper."""

import os
import sys
from typing import List, Dict, Any
from .base import CLIWrapper, ActionType


class TerraformWrapper(CLIWrapper):
    """Wrapper for Terraform CLI."""

    COMMAND_NAME = "terraform"

    def classify_action(self) -> ActionType:
        """Classify Terraform command as read or write."""
        if not self.args:
            return ActionType.READ

        subcommand = self.args[0].lower()

        # Mutating operations
        if subcommand in ["apply", "destroy", "taint", "untaint", "import"]:
            return ActionType.WRITE

        return ActionType.READ

    def _inject_credentials(self, env: Dict[str, str], credentials: Dict[str, Any]):
        """Inject Terraform credentials into environment."""
        # Terraform typically uses provider-specific credentials
        if "token" in credentials:
            # Could be for multiple providers
            env["TF_VAR_api_token"] = credentials["token"]
        if "credentials_json" in credentials:
            # GCP service account
            env["GOOGLE_APPLICATION_CREDENTIALS"] = credentials["credentials_json"]


def main():
    """Terraform wrapper entry point."""
    wrapper = TerraformWrapper(sys.argv[1:])
    return wrapper.run()


if __name__ == "__main__":
    sys.exit(main())
