"""AWS CLI wrapper."""

import os
import sys
from typing import List, Dict, Any, Optional
from base import CLIWrapper, ActionType


class AWSWrapper(CLIWrapper):
    """Wrapper for AWS CLI."""

    COMMAND_NAME = "aws"

    def classify_action(self) -> ActionType:
        """Classify AWS command as read or write."""
        if not self.args:
            return ActionType.READ

        # Get the operation (first positional arg, may be after flags)
        operation = self.args[0].lower()

        # Read operations
        read_ops = ["list", "describe", "get"]
        if any(operation.startswith(op) for op in read_ops):
            return ActionType.READ

        return ActionType.WRITE

    def _inject_credentials(self, env: Dict[str, str], credentials: Dict[str, Any]):
        """Inject AWS credentials into environment."""
        if "access_key" in credentials:
            env["AWS_ACCESS_KEY_ID"] = credentials["access_key"]
        if "secret_key" in credentials:
            env["AWS_SECRET_ACCESS_KEY"] = credentials["secret_key"]
        if "session_token" in credentials:
            env["AWS_SESSION_TOKEN"] = credentials["session_token"]
        if "region" in credentials:
            env["AWS_REGION"] = credentials["region"]


def main():
    """AWS wrapper entry point."""
    wrapper = AWSWrapper(sys.argv[1:])
    return wrapper.run()


if __name__ == "__main__":
    sys.exit(main())
