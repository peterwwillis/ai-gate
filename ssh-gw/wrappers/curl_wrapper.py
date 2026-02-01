"""curl CLI wrapper."""

import os
import sys
from typing import List, Dict, Any
from .base import CLIWrapper, ActionType


class CurlWrapper(CLIWrapper):
    """Wrapper for curl."""

    COMMAND_NAME = "curl"

    def classify_action(self) -> ActionType:
        """Classify curl command as read or write."""
        if not self.args:
            return ActionType.READ

        # Check for non-GET methods
        args_str = " ".join(self.args)
        methods = ["-X POST", "-X PUT", "-X PATCH", "-X DELETE", "-d "]

        if any(method in args_str for method in methods):
            return ActionType.WRITE

        return ActionType.READ

    def _inject_credentials(self, env: Dict[str, str], credentials: Dict[str, Any]):
        """Inject credentials into environment for curl."""
        # curl uses various auth methods, typically passed via flags or env vars
        if "bearer_token" in credentials:
            env["CURL_AUTH_TOKEN"] = credentials["bearer_token"]
        if "api_key" in credentials:
            env["CURL_API_KEY"] = credentials["api_key"]


def main():
    """curl wrapper entry point."""
    wrapper = CurlWrapper(sys.argv[1:])
    return wrapper.run()


if __name__ == "__main__":
    sys.exit(main())
