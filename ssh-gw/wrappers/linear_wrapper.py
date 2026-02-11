"""Linear CLI wrapper."""

import os
import sys
from typing import List, Dict, Any
from .base import CLIWrapper, ActionType


class LinearWrapper(CLIWrapper):
    """Wrapper for Linear CLI."""

    COMMAND_NAME = "linear"

    def classify_action(self) -> ActionType:
        """Classify Linear command as read or write."""
        if not self.args:
            return ActionType.READ

        subcommand = self.args[0].lower()

        # Mutating operations
        mutating = ["create", "delete", "update", "edit", "assign", "move"]
        if any(subcommand.startswith(op) or subcommand == op for op in mutating):
            return ActionType.WRITE

        return ActionType.READ

    def _inject_credentials(self, env: Dict[str, str], credentials: Dict[str, Any]):
        """Inject Linear credentials into environment."""
        if "api_key" in credentials:
            env["LINEAR_API_KEY"] = credentials["api_key"]


def main():
    """Linear wrapper entry point."""
    wrapper = LinearWrapper(sys.argv[1:])
    return wrapper.run()


if __name__ == "__main__":
    sys.exit(main())
