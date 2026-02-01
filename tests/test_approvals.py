"""Tests for approval orchestrator."""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gatewayd.approvals import ApprovalOrchestrator, ApprovalStatus


class MockGatewayRequest:
    """Mock gateway request for testing."""
    def __init__(self):
        self.id = "test-req-123"


def test_approval_request_creation():
    """Test creating an approval request."""
    orchestrator = ApprovalOrchestrator()
    gateway_req = MockGatewayRequest()

    approval_id = orchestrator.request_approval(
        gateway_req=gateway_req,
        tenant_id="default",
        details={"method": "POST", "path": "/test"},
    )

    assert approval_id is not None
    status = orchestrator.get_status(approval_id)
    assert status is not None
    assert status["status"] == ApprovalStatus.PENDING.value


def test_approval_approval():
    """Test approving a request."""
    orchestrator = ApprovalOrchestrator()
    gateway_req = MockGatewayRequest()

    approval_id = orchestrator.request_approval(
        gateway_req=gateway_req,
        tenant_id="default",
        details={"method": "POST", "path": "/test"},
    )

    orchestrator.approve(approval_id)

    status = orchestrator.get_status(approval_id)
    assert status["status"] == ApprovalStatus.APPROVED.value


def test_approval_denial():
    """Test denying a request."""
    orchestrator = ApprovalOrchestrator()
    gateway_req = MockGatewayRequest()

    approval_id = orchestrator.request_approval(
        gateway_req=gateway_req,
        tenant_id="default",
        details={"method": "POST", "path": "/test"},
    )

    orchestrator.deny(approval_id)

    status = orchestrator.get_status(approval_id)
    assert status["status"] == ApprovalStatus.DENIED.value


def test_wait_for_approval_approved():
    """Test waiting for approval (approved case)."""
    orchestrator = ApprovalOrchestrator()
    gateway_req = MockGatewayRequest()

    approval_id = orchestrator.request_approval(
        gateway_req=gateway_req,
        tenant_id="default",
        details={"method": "POST", "path": "/test"},
    )

    # Approve in a separate thread-like scenario
    import threading
    def approve_later():
        time.sleep(0.1)
        orchestrator.approve(approval_id)

    thread = threading.Thread(target=approve_later)
    thread.start()

    result = orchestrator.wait_for_approval(approval_id, timeout_seconds=2)
    thread.join()

    assert result is True


def test_wait_for_approval_denied():
    """Test waiting for approval (denied case)."""
    orchestrator = ApprovalOrchestrator()
    gateway_req = MockGatewayRequest()

    approval_id = orchestrator.request_approval(
        gateway_req=gateway_req,
        tenant_id="default",
        details={"method": "POST", "path": "/test"},
    )

    import threading
    def deny_later():
        time.sleep(0.1)
        orchestrator.deny(approval_id)

    thread = threading.Thread(target=deny_later)
    thread.start()

    result = orchestrator.wait_for_approval(approval_id, timeout_seconds=2)
    thread.join()

    assert result is False


if __name__ == "__main__":
    test_approval_request_creation()
    print("✓ test_approval_request_creation")

    test_approval_approval()
    print("✓ test_approval_approval")

    test_approval_denial()
    print("✓ test_approval_denial")

    test_wait_for_approval_approved()
    print("✓ test_wait_for_approval_approved")

    test_wait_for_approval_denied()
    print("✓ test_wait_for_approval_denied")

    print("\nAll approval tests passed!")
