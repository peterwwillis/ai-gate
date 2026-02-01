"""Tests for policy engine."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gatewayd.policy import PolicyEngine, SecurityMode
from gatewayd.app import ActionType


def test_read_never_requires_approval():
    """Reads should never require approval."""
    policy = PolicyEngine()

    assert policy.requires_approval(
        tenant_id="default",
        action_type=ActionType.READ,
        provider="github",
        method="GET",
        path="/user",
    ) is False


def test_strict_mode_all_writes_require_approval():
    """In strict mode, all writes require approval."""
    policy = PolicyEngine()

    assert policy.requires_approval(
        tenant_id="default",
        action_type=ActionType.WRITE,
        provider="github",
        method="POST",
        path="/repos/owner/repo/issues",
    ) is True


def test_cli_classification_aws():
    """Test AWS CLI classification."""
    policy = PolicyEngine()

    assert policy.classify_cli_command("aws", "list-buckets") == "read"
    assert policy.classify_cli_command("aws", "describe-instances") == "read"
    assert policy.classify_cli_command("aws", "get-object") == "read"
    assert policy.classify_cli_command("aws", "put-object") == "write"
    assert policy.classify_cli_command("aws", "delete-bucket") == "write"


def test_cli_classification_terraform():
    """Test Terraform classification."""
    policy = PolicyEngine()

    assert policy.classify_cli_command("terraform", "plan") == "read"
    assert policy.classify_cli_command("terraform", "apply") == "write"
    assert policy.classify_cli_command("terraform", "destroy") == "write"


def test_cli_classification_gcp():
    """Test GCP classification."""
    policy = PolicyEngine()

    assert policy.classify_cli_command("gcp", "list") == "read"
    assert policy.classify_cli_command("gcp", "describe") == "read"
    assert policy.classify_cli_command("gcp", "create") == "write"
    assert policy.classify_cli_command("gcp", "delete") == "write"


def test_cli_classification_kubectl():
    """Test kubectl classification."""
    policy = PolicyEngine()

    assert policy.classify_cli_command("kubectl", "get pods") == "read"
    assert policy.classify_cli_command("kubectl", "describe nodes") == "read"
    assert policy.classify_cli_command("kubectl", "apply") == "write"
    assert policy.classify_cli_command("kubectl", "delete") == "write"


if __name__ == "__main__":
    test_read_never_requires_approval()
    print("✓ test_read_never_requires_approval")

    test_strict_mode_all_writes_require_approval()
    print("✓ test_strict_mode_all_writes_require_approval")

    test_cli_classification_aws()
    print("✓ test_cli_classification_aws")

    test_cli_classification_terraform()
    print("✓ test_cli_classification_terraform")

    test_cli_classification_gcp()
    print("✓ test_cli_classification_gcp")

    test_cli_classification_kubectl()
    print("✓ test_cli_classification_kubectl")

    print("\nAll policy tests passed!")
