from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.integrations.tez_erp_client import TezERPClient
from app.models.ref_employee import RefEmployee


class MasterValidationService:
    def __init__(self, db: Session):
        self.db = db
        self.tez_client = TezERPClient()

    def derive_from_project(
        self,
        project_id: int | None,
        company_id: int | None,
        branch_id: int | None,
        department_id: int | None,
        customer_id: int | None,
        manager_emp_id: int | None,
    ) -> dict:
        if project_id is None or not settings.strict_master_validation:
            return {
                "company_id": company_id,
                "branch_id": branch_id,
                "department_id": department_id,
                "customer_id": customer_id,
                "manager_emp_id": manager_emp_id,
            }

        project = self.tez_client.get_master_record("project", project_id)
        if not project:
            raise HTTPException(status_code=422, detail=f"Invalid project: {project_id}")

        derived = {
            "company_id": company_id or project.get("companyId"),
            "branch_id": branch_id or project.get("branchId"),
            "department_id": department_id or project.get("departmentId"),
            "customer_id": customer_id or project.get("customerId"),
            "manager_emp_id": manager_emp_id or project.get("managerEmpId"),
        }

        if customer_id and project.get("customerId") and str(customer_id) != str(project.get("customerId")):
            raise HTTPException(status_code=422, detail="Customer does not match project mapping")

        return derived

    def validate_org_masters(self, company_id: int | None, branch_id: int | None, department_id: int | None) -> None:
        if company_id is None:
            raise HTTPException(status_code=422, detail="Company is required")
        if settings.strict_master_validation:
            self._ensure_master_exists("company", company_id)
            if branch_id is not None:
                self._ensure_master_exists("branch", branch_id)
            if department_id is not None:
                self._ensure_master_exists("department", department_id)

    def validate_customer(self, customer_id: int | None, required: bool) -> None:
        if required and customer_id is None:
            raise HTTPException(status_code=422, detail="Customer is required for billable task")
        if customer_id is not None and settings.strict_master_validation:
            self._ensure_master_exists("customer", customer_id)

    def validate_workflow(self, workflow_id: int | None, save_mode: str) -> str:
        if workflow_id is None:
            return "DRAFT" if save_mode == "DRAFT" else "OPEN"
        if settings.strict_master_validation:
            self._ensure_master_exists("workflow", workflow_id)
        return "OPEN"

    def employee_is_active(self, emp_id: int | None) -> bool:
        if emp_id is None:
            return False
        return (
            self.db.query(RefEmployee)
            .filter(RefEmployee.emp_id == emp_id, RefEmployee.is_active.is_(True))
            .first()
            is not None
        )

    def _ensure_master_exists(self, master_type: str, record_id: int) -> None:
        exists = self.tez_client.master_exists(master_type=master_type, record_id=record_id)
        if not exists:
            raise HTTPException(status_code=422, detail=f"Invalid or inactive {master_type}: {record_id}")
