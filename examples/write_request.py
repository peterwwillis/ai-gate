"""Example: Make a write request through the gateway (requires approval)."""

import requests
import os
import json

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:5000")
SESSION_TOKEN = os.getenv("GATEWAY_SESSION_TOKEN")


def create_github_issue():
    """Create a GitHub issue (write operation - requires approval)."""
    if not SESSION_TOKEN:
        print("Error: GATEWAY_SESSION_TOKEN not set")
        return

    headers = {
        "Authorization": f"Bearer {SESSION_TOKEN}",
        "X-Provider": "github",
        "X-Creds": "default:github:personal",
        "Content-Type": "application/json",
    }

    body = {
        "title": "Test issue from AI-GATE",
        "body": "This is a test issue created via the gateway",
    }

    response = requests.post(
        f"{GATEWAY_URL}/api/v1/proxy/repos/owner/repo/issues",
        headers=headers,
        json=body,
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


if __name__ == "__main__":
    create_github_issue()
