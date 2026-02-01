"""GitHub CLI wrapper."""

import os
import sys
from typing import List, Dict, Any
from base import CLIWrapper, ActionType


class GithubWrapper(CLIWrapper):
    """Wrapper for GitHub CLI (gh)."""

    COMMAND_NAME = "gh"

    def classify_action(self) -> ActionType:
        """Classify GitHub command as read or write."""
        if not self.args:
            return ActionType.READ

        subcommand = self.args[0].lower()

        # Mutating operations
        mutating_ops = ["create", "delete", "update", "edit", "merge", "close", "open", "fork", "fork-repo"]

        if any(subcommand.startswith(op) or subcommand == op for op in mutating_ops):
            return ActionType.WRITE

        return ActionType.READ

    def _inject_credentials(self, env: Dict[str, str], credentials: Dict[str, Any]):
        """Inject GitHub credentials into environment."""
        if "token" in credentials:
            env["GH_TOKEN"] = credentials["token"]
        if "host" in credentials:
            env["GH_HOST"] = credentials["host"]


def main():
    """GitHub wrapper entry point."""
    wrapper = GithubWrapper(sys.argv[1:])
    return wrapper.run()


if __name__ == "__main__":
    sys.exit(main())
