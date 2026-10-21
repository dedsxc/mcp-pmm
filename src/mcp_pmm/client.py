"""HTTP client for the PMM API (read-only)."""

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class PMMAPIError(Exception):
    """Base exception for PMM API errors."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.details = details


class PMMAuthenticationError(PMMAPIError):
    """Authentication error (missing or invalid token)."""


class PMMPermissionError(PMMAPIError):
    """The token is valid but its role is not allowed to call this endpoint."""


class PMMClient:
    """Client for the PMM API.

    Configuration (environment variables):
        PMM_URL: Base URL of PMM (default: http://localhost)
        PMM_TOKEN: Grafana service account token (Bearer)
        PMM_TIMEOUT: HTTP timeout in seconds (default: 30)
        PMM_VERIFY_SSL: set to "false" to disable TLS verification
    """

    def __init__(self) -> None:
        self.base_url = os.getenv("PMM_URL", "http://localhost").rstrip("/")
        self._token = os.getenv("PMM_TOKEN")
        self._timeout = float(os.getenv("PMM_TIMEOUT", "30"))
        self._verify = os.getenv("PMM_VERIFY_SSL", "true").lower() != "false"

    def _request(
        self, method: str, path: str, params: dict | None = None, json: dict | None = None
    ) -> Any:
        if not self._token:
            raise PMMAuthenticationError("PMM_TOKEN is not set")
        try:
            with httpx.Client(timeout=self._timeout, verify=self._verify) as http:
                resp = http.request(
                    method,
                    f"{self.base_url}{path}",
                    params=params,
                    json=json,
                    headers={"Authorization": f"Bearer {self._token}"},
                )
        except httpx.HTTPError as e:
            raise PMMAPIError(f"Request to PMM failed: {e}") from e
        if resp.status_code == 401:
            raise PMMAuthenticationError("PMM rejected the token (HTTP 401)")
        if resp.status_code == 403:
            raise PMMPermissionError("Token role is not allowed to call this endpoint (HTTP 403)")
        if resp.status_code >= 400:
            raise PMMAPIError(f"PMM returned HTTP {resp.status_code}", resp.text[:500])
        if not resp.content:
            return {}
        return resp.json()

    def get(self, path: str, params: dict | None = None) -> Any:
        return self._request("GET", path, params=params)

    def post(self, path: str, json: dict | None = None) -> Any:
        return self._request("POST", path, json=json or {})
