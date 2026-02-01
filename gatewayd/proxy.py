"""HTTP forward proxy implementation."""

import logging
import requests
from typing import Dict, Any, Optional
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class HTTPProxy:
    """HTTP forward proxy that intercepts, classifies, and forwards requests."""

    def __init__(self, credential_broker, policy_engine):
        """Initialize HTTP proxy."""
        self.credential_broker = credential_broker
        self.policy_engine = policy_engine
        self.base_urls = {
            "github": "https://api.github.com",
            "aws": "https://aws.amazonaws.com",
            "gcp": "https://www.googleapis.com",
            "slack": "https://slack.com/api",
            "datadog": "https://api.datadoghq.com",
            "linear": "https://api.linear.app/graphql",
        }

    def forward_request(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        data: Optional[bytes],
        credentials: Optional[Dict[str, Any]],
        provider: str,
    ) -> Dict[str, Any]:
        """Forward request with credential injection."""

        # Build full URL
        base_url = self.base_urls.get(provider, "https://api.example.com")
        url = urljoin(base_url, path)

        logger.debug(f"Forwarding {method} request to {url}")

        # Prepare request headers
        request_headers = dict(headers)
        # Remove gateway-specific headers
        request_headers.pop("X-Creds", None)
        request_headers.pop("X-Provider", None)
        request_headers.pop("Authorization", None)

        # Inject credentials if provided
        if credentials:
            request_headers.update(self._inject_credentials(credentials, provider))

        # Make request
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=request_headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=request_headers, data=data, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=request_headers, data=data, timeout=30)
            elif method.upper() == "PATCH":
                response = requests.patch(url, headers=request_headers, data=data, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=request_headers, timeout=30)
            elif method.upper() == "HEAD":
                response = requests.head(url, headers=request_headers, timeout=30)
            else:
                return {"status_code": 405, "body": b"Method not allowed"}

            # Scrub sensitive data from response headers
            response_headers = dict(response.headers)
            sensitive_headers = ["authorization", "x-api-key", "cookie"]
            for header in sensitive_headers:
                response_headers.pop(header, None)

            return {
                "status_code": response.status_code,
                "body": response.content,
                "headers": response_headers,
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise

    def _inject_credentials(self, credentials: Dict[str, Any], provider: str) -> Dict[str, str]:
        """Inject credentials into request headers."""
        headers = {}

        if provider == "github":
            if "token" in credentials:
                headers["Authorization"] = f"token {credentials['token']}"
            elif "bearer_token" in credentials:
                headers["Authorization"] = f"Bearer {credentials['bearer_token']}"

        elif provider == "slack":
            if "token" in credentials:
                headers["Authorization"] = f"Bearer {credentials['token']}"

        elif provider == "aws":
            # AWS uses different auth mechanism (SigV4), typically handled via boto3
            # For HTTP proxy, we'd need to sign the request
            if "access_key" in credentials and "secret_key" in credentials:
                # This is simplified; real AWS signing is more complex
                headers["X-AWS-Access-Key"] = credentials["access_key"]

        elif provider == "gcp":
            if "bearer_token" in credentials:
                headers["Authorization"] = f"Bearer {credentials['bearer_token']}"

        elif provider == "datadog":
            if "api_key" in credentials:
                headers["DD-API-KEY"] = credentials["api_key"]
            if "app_key" in credentials:
                headers["DD-APPLICATION-KEY"] = credentials["app_key"]

        elif provider == "linear":
            if "api_key" in credentials:
                headers["Authorization"] = f"Bearer {credentials['api_key']}"

        return headers
