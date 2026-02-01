"""Initialize test credentials for local testing."""

import json
import os

# Simple test credentials storage
TEST_CREDENTIALS = {
    "default:github:personal": {
        "type": "github_pat",
        "token": "ghs_test_token_12345",
    },
    "default:aws:prod-readonly": {
        "type": "aws_assumerole",
        "access_key": "AKIAIOSFODNN7EXAMPLE",
        "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "region": "us-east-1",
    },
    "test:github:test": {
        "type": "github_pat",
        "token": "ghs_test_12345",
    },
}

if __name__ == "__main__":
    # Write test credentials
    with open("config/credentials.json", "w") as f:
        json.dump(TEST_CREDENTIALS, f, indent=2)
    print("Test credentials initialized")
