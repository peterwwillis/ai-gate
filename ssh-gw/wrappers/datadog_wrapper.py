"""Datadog CLI wrapper."""

import os
import sys
from typing import List, Dict, Any
from .base import CLIWrapper, ActionType


class DatadogWrapper(CLIWrapper):
    """Wrapper for Datadog CLI."""

    COMMAND_NAME = "datadog"

    def classify_action(self) -> ActionType:
        """Classify Datadog command as read or write."""
        if not self.args:
            return ActionType.READ

        subcommand = self.args[0].lower()

        # Mutating operations
        mutating = ["create", "delete", "update", "edit", "set"]
        if any(subcommand.startswith(op) or subcommand == op for op in mutating):
            return ActionType.WRITE

        return ActionType.READ

    def _inject_credentials(self, env: Dict[str, str], credentials: Dict[str, Any]):
        """Inject Datadog credentials into environment."""
        if "api_key" in credentials:
            env["DD_API_KEY"] = credentials["api_key"]
        if "app_key" in credentials:
            env["DD_APP_KEY"] = credentials["app_key"]


def main():
    """Datadog wrapper entry point."""
    wrapper = DatadogWrapper(sys.argv[1:])
    return wrapper.run()


if __name__ == "__main__":
    sys.exit(main())
