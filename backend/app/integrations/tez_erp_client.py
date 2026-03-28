from __future__ import annotations

import time

import httpx

from app.core.config import settings


class TezERPClient:
    def __init__(self) -> None:
        self.base_url = settings.tez_erp_base_url.rstrip("/")
        self.endpoint = settings.tez_employee_endpoint
        self.api_key = settings.tez_erp_api_key
        self.timeout = settings.tez_timeout_seconds
        self.max_retries = settings.tez_max_retries
        self.master_endpoints = {
            "company": settings.tez_company_endpoint,
            "branch": settings.tez_branch_endpoint,
            "department": settings.tez_department_endpoint,
            "customer": settings.tez_customer_endpoint,
            "workflow": settings.tez_workflow_endpoint,
            "project": settings.tez_project_endpoint,
            "cost_center": settings.tez_cost_center_endpoint,
        }

    def get_employees(self) -> list[dict]:
        return self._get_list(self.endpoint)

    def get_master_record(self, master_type: str, record_id: int) -> dict | None:
        endpoint = self.master_endpoints.get(master_type)
        if not endpoint:
            return None
        records = self._get_list(endpoint)
        for row in records:
            row_id = row.get("id") or row.get(f"{master_type}Id") or row.get("code")
            if str(row_id) == str(record_id):
                return row
        return None

    def master_exists(self, master_type: str, record_id: int) -> bool:
        row = self.get_master_record(master_type, record_id)
        if not row:
            return False
        return bool(row.get("active", 1))

    def _get_list(self, endpoint: str) -> list[dict]:
        last_error = None
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.get(f"{self.base_url}/{endpoint}", headers=headers)
                    response.raise_for_status()
                    payload = response.json()
                    data = payload.get("data", []) if isinstance(payload, dict) else payload
                    return data if isinstance(data, list) else []
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(0.5 * attempt)

        raise RuntimeError(f"Tez ERP fetch failed for {endpoint} after {self.max_retries} attempts: {last_error}")
