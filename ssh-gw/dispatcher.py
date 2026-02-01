"""SSH Gateway - Restricted SSH with CLI wrappers."""

import os
import sys
import logging
from typing import List, Optional

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


ALLOWED_COMMANDS = {
    "aws": "aws_wrapper.py",
    "gcloud": "gcloud_wrapper.py",
    "gh": "gh_wrapper.py",
    "terraform": "terraform_wrapper.py",
    "kubectl": "kubectl_wrapper.py",
    "datadog": "datadog_wrapper.py",
    "linear": "linear_wrapper.py",
    "curl": "curl_wrapper.py",
}


def dispatch_command(command: str, args: List[str]) -> int:
    """Dispatch command to appropriate wrapper."""
    if command not in ALLOWED_COMMANDS:
        logger.error(f"Command not allowed: {command}")
        print(f"Error: Command '{command}' is not allowed", file=sys.stderr)
        return 1

    wrapper = ALLOWED_COMMANDS[command]
    wrapper_path = os.path.join(os.path.dirname(__file__), "wrappers", wrapper)

    if not os.path.exists(wrapper_path):
        logger.error(f"Wrapper not found: {wrapper_path}")
        print(f"Error: Command wrapper not found", file=sys.stderr)
        return 1

    logger.debug(f"Dispatching to wrapper: {wrapper}")

    # Execute wrapper (in production, would fork/exec here)
    # For now, import and call
    try:
        # This is a simplified version; real implementation would use subprocess
        print(f"Would execute: {wrapper} {' '.join(args)}", file=sys.stderr)
        return 0
    except Exception as e:
        logger.error(f"Error executing wrapper: {str(e)}")
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1


def main():
    """SSH gateway main entry point."""
    # ForceCommand environment variable set by sshd
    ssh_command = os.environ.get("SSH_ORIGINAL_COMMAND", "")

    if not ssh_command:
        logger.error("No command provided")
        print("Error: No command provided", file=sys.stderr)
        return 1

    # Parse command and args
    parts = ssh_command.split()
    if not parts:
        logger.error("Empty command")
        return 1

    command = parts[0]
    args = parts[1:]

    logger.info(f"Gateway command: {command} {' '.join(args)}")

    return dispatch_command(command, args)


if __name__ == "__main__":
    sys.exit(main())
