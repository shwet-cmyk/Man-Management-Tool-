from __future__ import annotations

import time
from dataclasses import dataclass

import httpx


@dataclass
class ApiError(Exception):
    category: str
    message: str
    status_code: int | None = None
    retryable: bool = False


class ApiClient:
    def __init__(self, base_url: str, timeout_seconds: int = 30, max_retries: int = 3, auth_mode: str = "api_key", token: str | None = None, api_key_header: str = "x-api-key", extra_headers: dict[str, str] | None = None):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.auth_mode = auth_mode
        self.token = token
        self.api_key_header = api_key_header
        self.extra_headers = extra_headers or {}

    def get(self, endpoint: str, params: dict | None = None) -> dict:
        headers = self._build_headers()
        last_error: ApiError | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.get(f"{self.base_url}/{endpoint.lstrip('/')}", params=params or {}, headers=headers)
                    if response.status_code in {401, 403}:
                        raise ApiError(category="auth_error", message="Authentication failed while calling external API", status_code=response.status_code, retryable=False)
                    response.raise_for_status()
                    payload = response.json()
                    if isinstance(payload, list):
                        return {"success": True, "data": payload}
                    if isinstance(payload, dict):
                        return {"success": True, "data": payload.get("data", payload)}
                    return {"success": True, "data": []}
            except ApiError as exc:
                last_error = exc
                break
            except httpx.TimeoutException as exc:
                last_error = ApiError(category="retryable_error", message=f"Timeout while calling external API: {exc}", retryable=True)
            except httpx.RequestError as exc:
                last_error = ApiError(category="retryable_error", message=f"Network failure while calling external API: {exc}", retryable=True)
            except Exception as exc:  # noqa: BLE001
                last_error = ApiError(category="failure", message=f"Failed to parse external API response: {exc}", retryable=False)

            if attempt < self.max_retries and last_error and last_error.retryable:
                time.sleep(0.5 * attempt)

        assert last_error is not None
        raise last_error

    def _build_headers(self) -> dict[str, str]:
        headers = {**self.extra_headers}
        if self.auth_mode == "bearer" and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        elif self.auth_mode == "api_key" and self.token:
            headers[self.api_key_header] = self.token
        elif self.auth_mode == "custom" and self.token:
            headers["Authorization"] = self.token
        return headers
