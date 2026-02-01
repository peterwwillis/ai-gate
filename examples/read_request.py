"""Example: Make a read request through the gateway."""

import requests
import os

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:5000")
SESSION_TOKEN = os.getenv("GATEWAY_SESSION_TOKEN")


def get_github_user():
    """Get GitHub user info (read operation)."""
    if not SESSION_TOKEN:
        print("Error: GATEWAY_SESSION_TOKEN not set")
        return

    headers = {
        "Authorization": f"Bearer {SESSION_TOKEN}",
        "X-Provider": "github",
        "X-Creds": "default:github:personal",
    }

    response = requests.get(
        f"{GATEWAY_URL}/api/v1/proxy/user",
        headers=headers,
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


if __name__ == "__main__":
    get_github_user()
