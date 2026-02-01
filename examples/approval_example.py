"""Example: Check approval status."""

import requests
import os

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:5000")
SESSION_TOKEN = os.getenv("GATEWAY_SESSION_TOKEN")


def check_approval_status(approval_id: str):
    """Check the status of an approval request."""
    if not SESSION_TOKEN:
        print("Error: GATEWAY_SESSION_TOKEN not set")
        return

    headers = {
        "Authorization": f"Bearer {SESSION_TOKEN}",
    }

    response = requests.get(
        f"{GATEWAY_URL}/approvals/{approval_id}/status",
        headers=headers,
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


def approve_request(approval_id: str):
    """Approve a pending request."""
    if not SESSION_TOKEN:
        print("Error: GATEWAY_SESSION_TOKEN not set")
        return

    headers = {
        "Authorization": f"Bearer {SESSION_TOKEN}",
    }

    response = requests.post(
        f"{GATEWAY_URL}/approvals/{approval_id}/approve",
        headers=headers,
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


def deny_request(approval_id: str):
    """Deny a pending request."""
    if not SESSION_TOKEN:
        print("Error: GATEWAY_SESSION_TOKEN not set")
        return

    headers = {
        "Authorization": f"Bearer {SESSION_TOKEN}",
    }

    response = requests.post(
        f"{GATEWAY_URL}/approvals/{approval_id}/deny",
        headers=headers,
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python approval_example.py <check|approve|deny> <approval_id>")
        sys.exit(1)

    action = sys.argv[1]
    approval_id = sys.argv[2]

    if action == "check":
        check_approval_status(approval_id)
    elif action == "approve":
        approve_request(approval_id)
    elif action == "deny":
        deny_request(approval_id)
    else:
        print(f"Unknown action: {action}")
