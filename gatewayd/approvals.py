"""Approval orchestrator for managing request approvals."""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from enum import Enum
import threading
import time

logger = logging.getLogger(__name__)


class ApprovalStatus(Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"


class ApprovalOrchestrator:
    """Manages approval requests and notifications."""

    def __init__(self):
        """Initialize approval orchestrator."""
        self.approvals: Dict[str, Dict[str, Any]] = {}
        self.approval_events: Dict[str, threading.Event] = {}

    def request_approval(
        self,
        gateway_req: Any,
        tenant_id: str,
        details: Dict[str, Any],
    ) -> str:
        """Request approval for a write operation."""
        approval_id = str(uuid.uuid4())

        self.approvals[approval_id] = {
            "id": approval_id,
            "tenant_id": tenant_id,
            "request_id": gateway_req.id,
            "status": ApprovalStatus.PENDING.value,
            "timestamp": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(seconds=3600)).isoformat(),
            "details": details,
            "decided_at": None,
            "decided_by": None,
        }

        self.approval_events[approval_id] = threading.Event()

        logger.info(
            f"Approval request created: {approval_id}",
            extra={
                "tenant_id": tenant_id,
                "details": details,
            },
        )

        # Send notifications
        self._send_notifications(approval_id)

        return approval_id

    def _send_notifications(self, approval_id: str):
        """Send approval notifications (Slack, terminal, desktop)."""
        approval = self.approvals[approval_id]

        # TODO: Implement notification channels:
        # - Slack DM
        # - Terminal prompt
        # - Desktop notification

        logger.info(f"Notifications sent for approval: {approval_id}")

    def approve(self, approval_id: str, duration_minutes: Optional[int] = None):
        """Approve a request."""
        if approval_id not in self.approvals:
            logger.warning(f"Approval not found: {approval_id}")
            return

        self.approvals[approval_id]["status"] = ApprovalStatus.APPROVED.value
        self.approvals[approval_id]["decided_at"] = datetime.utcnow().isoformat()

        # If duration specified, create persistent rule (future)
        if duration_minutes:
            logger.info(f"Approval granted with {duration_minutes} minute duration: {approval_id}")

        logger.info(f"Approval granted: {approval_id}")
        self.approval_events[approval_id].set()

    def deny(self, approval_id: str):
        """Deny a request."""
        if approval_id not in self.approvals:
            logger.warning(f"Approval not found: {approval_id}")
            return

        self.approvals[approval_id]["status"] = ApprovalStatus.DENIED.value
        self.approvals[approval_id]["decided_at"] = datetime.utcnow().isoformat()

        logger.info(f"Approval denied: {approval_id}")
        self.approval_events[approval_id].set()

    def wait_for_approval(self, approval_id: str, timeout_seconds: int = 3600) -> bool:
        """Block and wait for approval decision."""
        if approval_id not in self.approvals:
            logger.error(f"Approval not found: {approval_id}")
            return False

        logger.debug(f"Waiting for approval decision: {approval_id}")

        # Wait for approval event with timeout
        approved = self.approval_events[approval_id].wait(timeout=timeout_seconds)

        if not approved:
            # Timeout expired
            self.approvals[approval_id]["status"] = ApprovalStatus.EXPIRED.value
            logger.warning(f"Approval timed out: {approval_id}")
            return False

        # Check final status
        final_status = self.approvals[approval_id]["status"]
        return final_status == ApprovalStatus.APPROVED.value

    def get_status(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """Get approval status."""
        return self.approvals.get(approval_id)

    def cleanup_expired_approvals(self):
        """Periodically clean up expired approvals."""
        now = datetime.utcnow()
        expired = []

        for approval_id, approval in self.approvals.items():
            expires_at = datetime.fromisoformat(approval["expires_at"])
            if now > expires_at and approval["status"] == ApprovalStatus.PENDING.value:
                approval["status"] = ApprovalStatus.EXPIRED.value
                expired.append(approval_id)

        if expired:
            logger.info(f"Expired {len(expired)} pending approvals")
