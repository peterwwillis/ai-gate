"""Main gatewayd application."""

import json
import logging
import os
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from enum import Enum

from flask import Flask, request, jsonify, Response
from werkzeug.exceptions import HTTPException

from .proxy import HTTPProxy
from .approvals import ApprovalOrchestrator
from .credentials import CredentialBroker
from .policy import PolicyEngine
from .auth import SessionManager


# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Classification of actions."""
    READ = "read"
    WRITE = "write"


@dataclass
class GatewayRequest:
    """Request metadata for logging and classification."""
    id: str
    timestamp: str
    method: str
    path: str
    provider: str
    action_type: ActionType
    requires_approval: bool
    session_token: Optional[str] = None
    cred_selector: Optional[str] = None
    approval_id: Optional[str] = None


def create_app(config_path: Optional[str] = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    # Initialize core components
    session_manager = SessionManager()
    credential_broker = CredentialBroker(config_path)
    policy_engine = PolicyEngine(config_path)
    approval_orchestrator = ApprovalOrchestrator()
    http_proxy = HTTPProxy(credential_broker, policy_engine)

    # Store references for request handlers
    app.extensions["session_manager"] = session_manager
    app.extensions["credential_broker"] = credential_broker
    app.extensions["policy_engine"] = policy_engine
    app.extensions["approval_orchestrator"] = approval_orchestrator
    app.extensions["http_proxy"] = http_proxy

    @app.before_request
    def log_request():
        """Log incoming requests."""
        logger.debug(
            f"Incoming request: {request.method} {request.path}",
            extra={"remote_addr": request.remote_addr},
        )

    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint."""
        return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

    @app.route("/session/new", methods=["POST"])
    def create_session():
        """Create a new agent session."""
        data = request.get_json() or {}
        tenant_id = data.get("tenant_id")
        enrollment_secret = data.get("enrollment_secret")

        if not tenant_id or not enrollment_secret:
            return jsonify({"error": "Missing tenant_id or enrollment_secret"}), 400

        # Verify enrollment secret (in production, validate against secure storage)
        if not session_manager.verify_enrollment(tenant_id, enrollment_secret):
            logger.warning(f"Failed enrollment attempt for tenant: {tenant_id}")
            return jsonify({"error": "Invalid credentials"}), 401

        # Generate session token
        token = session_manager.create_session(tenant_id)
        ttl_seconds = 3600  # 1 hour default

        return jsonify({
            "session_token": token,
            "ttl_seconds": ttl_seconds,
            "expires_at": (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat(),
        }), 201

    @app.route("/api/v1/proxy/<path:target_path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
    def proxy_request(target_path: str):
        """HTTP proxy endpoint for external API calls."""
        # Verify session
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header[7:]
        session_info = session_manager.validate_token(token)
        if not session_info:
            return jsonify({"error": "Invalid or expired session"}), 401

        tenant_id = session_info["tenant_id"]
        cred_selector = request.headers.get("X-Creds")
        provider = request.headers.get("X-Provider", "unknown")

        # Create request metadata
        gateway_req = GatewayRequest(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            method=request.method,
            path=target_path,
            provider=provider,
            action_type=ActionType.READ if request.method in ["GET", "HEAD", "OPTIONS"] else ActionType.WRITE,
            session_token=token,
            cred_selector=cred_selector,
            requires_approval=False,  # Will be determined by policy engine
        )

        # Classify and determine if approval required
        gateway_req.requires_approval = policy_engine.requires_approval(
            tenant_id=tenant_id,
            action_type=gateway_req.action_type,
            provider=provider,
            method=request.method,
            path=target_path,
        )

        logger.info(
            f"Classified request {gateway_req.id}: {request.method} {target_path} "
            f"({gateway_req.action_type.value}, approval_required={gateway_req.requires_approval})"
        )

        # If write and approval required, request approval
        if gateway_req.requires_approval:
            approval_id = approval_orchestrator.request_approval(
                gateway_req=gateway_req,
                tenant_id=tenant_id,
                details={
                    "method": request.method,
                    "path": target_path,
                    "provider": provider,
                    "headers": dict(request.headers),
                },
            )
            gateway_req.approval_id = approval_id

            logger.info(f"Approval requested: {approval_id} for request {gateway_req.id}")

            # Block and wait for approval (with timeout)
            approved = approval_orchestrator.wait_for_approval(approval_id, timeout_seconds=3600)

            if not approved:
                logger.warning(f"Approval denied or timed out: {approval_id}")
                return jsonify({"error": "Request not approved"}), 403

            logger.info(f"Approval granted: {approval_id}")

        # Fetch credentials if needed
        credentials = None
        if cred_selector:
            credentials = credential_broker.get_credentials(tenant_id, cred_selector)
            if not credentials:
                logger.error(f"Failed to retrieve credentials: {cred_selector}")
                return jsonify({"error": "Failed to retrieve credentials"}), 500

        # Forward request through proxy
        try:
            response_data = http_proxy.forward_request(
                method=request.method,
                path=target_path,
                headers=dict(request.headers),
                data=request.get_data(),
                credentials=credentials,
                provider=provider,
            )

            logger.info(f"Request {gateway_req.id} completed successfully")

            return Response(
                response_data["body"],
                status=response_data.get("status_code", 200),
                headers=response_data.get("headers", {}),
            )

        except Exception as e:
            logger.error(f"Error forwarding request {gateway_req.id}: {str(e)}")
            return jsonify({"error": "Proxy error"}), 502

    @app.route("/approvals/<approval_id>/approve", methods=["POST"])
    def approve_request(approval_id: str):
        """Approve a pending request."""
        duration_minutes = (request.get_json() or {}).get("duration_minutes")
        approval_orchestrator.approve(approval_id, duration_minutes=duration_minutes)
        logger.info(f"Approval granted: {approval_id}")
        return jsonify({"status": "approved"}), 200

    @app.route("/approvals/<approval_id>/deny", methods=["POST"])
    def deny_request(approval_id: str):
        """Deny a pending request."""
        approval_orchestrator.deny(approval_id)
        logger.info(f"Approval denied: {approval_id}")
        return jsonify({"status": "denied"}), 200

    @app.route("/approvals/<approval_id>/status", methods=["GET"])
    def approval_status(approval_id: str):
        """Get approval status."""
        status = approval_orchestrator.get_status(approval_id)
        if not status:
            return jsonify({"error": "Approval not found"}), 404
        return jsonify(status), 200

    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        """Handle HTTP errors."""
        logger.error(f"HTTP error: {e.code} - {e.description}")
        return jsonify({"error": e.description}), e.code

    @app.errorhandler(Exception)
    def handle_error(e):
        """Handle unexpected errors."""
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=os.getenv("DEBUG", "false").lower() == "true")
