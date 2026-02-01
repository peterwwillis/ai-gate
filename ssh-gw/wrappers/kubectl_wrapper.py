"""kubectl CLI wrapper."""

import os
import sys
from typing import List, Dict, Any
from base import CLIWrapper, ActionType


class KubectlWrapper(CLIWrapper):
    """Wrapper for kubectl."""

    COMMAND_NAME = "kubectl"

    def classify_action(self) -> ActionType:
        """Classify kubectl command as read or write."""
        if not self.args:
            return ActionType.READ

        verb = self.args[0].lower()

        # Mutating operations
        mutating_verbs = ["apply", "delete", "scale", "patch", "set", "rollout", "expose", "autoscale", "cordon", "drain", "taint"]

        if any(verb.startswith(v) or verb == v for v in mutating_verbs):
            return ActionType.WRITE

        return ActionType.READ

    def _inject_credentials(self, env: Dict[str, str], credentials: Dict[str, Any]):
        """Inject kubectl credentials into environment."""
        if "kubeconfig" in credentials:
            env["KUBECONFIG"] = credentials["kubeconfig"]
        if "token" in credentials:
            env["KUBECONFIG_TOKEN"] = credentials["token"]


def main():
    """kubectl wrapper entry point."""
    wrapper = KubectlWrapper(sys.argv[1:])
    return wrapper.run()


if __name__ == "__main__":
    sys.exit(main())
