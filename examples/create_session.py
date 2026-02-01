"""Example: Create a session with the gateway."""

import requests
import os

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:5000")

def create_session():
    """Create a new agent session."""
    response = requests.post(
        f"{GATEWAY_URL}/session/new",
        json={
            "tenant_id": "default",
            "enrollment_secret": "test-secret-123",
        },
    )

    if response.status_code != 201:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

    session = response.json()
    print(f"Session created successfully!")
    print(f"Token: {session['session_token']}")
    print(f"Expires at: {session['expires_at']}")

    return session["session_token"]


if __name__ == "__main__":
    token = create_session()
    if token:
        print("\nSession token saved. Use for subsequent requests:")
        print(f"export GATEWAY_SESSION_TOKEN={token}")
