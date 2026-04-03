from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from app.modules.system_audit.service import audit_service

router = APIRouter(tags=["Organization Masters"])

_COMPANIES: dict[int, dict] = {
    1: {
        "id": 1,
        "company_code": "TEZ001",
        "company_name": "TEZ Global",
        "legal_name": "TEZ Global Private Limited",
        "currency": "USD",
        "financial_year_start": "2026-04-01",
        "country": "United States",
        "status": "ACTIVE",
        "default_company": True,
        "created_by": "system",
        "created_date": datetime.now(UTC).isoformat(),
    }
}

_BRANCHES: dict[int, dict] = {
    1: {
        "id": 1,
        "branch_code": "HO001",
        "branch_name": "Head Office",
        "company_id": 1,
        "branch_type": "HO",
        "country": "United States",
        "status": "ACTIVE",
    }
}

_DEPARTMENTS: dict[int, dict] = {
    1: {
        "id": 1,
        "department_code": "ENG001",
        "department_name": "Engineering",
        "company_id": 1,
        "branch_id": 1,
        "department_head": None,
        "status": "ACTIVE",
    }
}


class CompanyCreateRequest(BaseModel):
    company_code: str
    company_name: str
    legal_name: str
    currency: str
    financial_year_start: str
    country: str
    gst_tax_number: str | None = None
    pan_registration_no: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = None
    default_company: bool = False
    status: bool = True


class CompanyUpdateRequest(CompanyCreateRequest):
    pass


class BranchCreateRequest(BaseModel):
    branch_code: str
    branch_name: str
    company_id: int
    branch_type: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str
    pincode: str | None = None
    contact_person: str | None = None
    contact_number: str | None = None
    email: EmailStr | None = None
    status: bool = True


class BranchUpdateRequest(BranchCreateRequest):
    pass


class DepartmentCreateRequest(BaseModel):
    department_code: str
    department_name: str
    company_id: int
    branch_id: int
    department_head: int | None = None
    status: bool = True


class DepartmentUpdateRequest(DepartmentCreateRequest):
    pass


def _audit(action: str, reference_id: int, payload: dict) -> None:
    audit_service.add(
        {
            "user_name": "system",
            "module": "ORG_MASTER",
            "reference_id": str(reference_id),
            "action_type": action,
            "field_name": "payload",
            "old_value": None,
            "new_value": str(payload),
            "remarks": None,
            "context": payload,
        }
    )


def _active_company(company_id: int) -> dict:
    company = _COMPANIES.get(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    if company["status"] != "ACTIVE":
        raise HTTPException(status_code=422, detail="Company is inactive")
    return company


@router.get("/masters/companies")
@router.get("/company/list")
def list_companies(include_inactive: bool = True):
    rows = list(_COMPANIES.values())
    if not include_inactive:
        rows = [r for r in rows if r["status"] == "ACTIVE"]
    return {"count": len(rows), "items": rows}


@router.get("/company/{company_id}")
def get_company(company_id: int):
    row = _COMPANIES.get(company_id)
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")
    return row


@router.post("/company/create")
def create_company(payload: CompanyCreateRequest):
    if any(c["company_code"].lower() == payload.company_code.lower() for c in _COMPANIES.values()):
        raise HTTPException(status_code=409, detail="Duplicate company code")
    if any(c["company_name"].lower() == payload.company_name.lower() for c in _COMPANIES.values()):
        raise HTTPException(status_code=409, detail="Duplicate company name")

    next_id = max(_COMPANIES.keys(), default=0) + 1
    row = {
        "id": next_id,
        **payload.model_dump(),
        "status": "ACTIVE" if payload.status else "INACTIVE",
        "created_by": "system",
        "created_date": datetime.now(UTC).isoformat(),
    }

    if payload.default_company:
        for company in _COMPANIES.values():
            company["default_company"] = False

    _COMPANIES[next_id] = row
    _audit("COMPANY_CREATED", next_id, row)
    return row


@router.put("/company/update/{company_id}")
def update_company(company_id: int, payload: CompanyUpdateRequest):
    existing = _COMPANIES.get(company_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Company not found")

    for cid, company in _COMPANIES.items():
        if cid == company_id:
            continue
        if company["company_code"].lower() == payload.company_code.lower():
            raise HTTPException(status_code=409, detail="Duplicate company code")

    update = payload.model_dump()
    if payload.default_company:
        for cid, company in _COMPANIES.items():
            if cid != company_id:
                company["default_company"] = False

    existing.update(update)
    existing["status"] = "ACTIVE" if payload.status else "INACTIVE"
    _audit("COMPANY_UPDATED", company_id, existing)
    return existing


@router.post("/company/deactivate/{company_id}")
def deactivate_company(company_id: int):
    company = _COMPANIES.get(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    has_dependency = any(b["company_id"] == company_id and b["status"] == "ACTIVE" for b in _BRANCHES.values())
    if has_dependency:
        return {
            "status": "blocked",
            "message": "Company has active branches/transactions. Delete blocked; only deactivation is allowed.",
            "action": "deactivate_confirmed",
        }

    company["status"] = "INACTIVE"
    company["default_company"] = False
    _audit("COMPANY_DEACTIVATED", company_id, company)
    return {"status": "success", "item": company}


@router.get("/masters/branches")
@router.get("/branch/list")
def list_branches(company_id: int | None = None, include_inactive: bool = True):
    rows = list(_BRANCHES.values())
    if company_id is not None:
        rows = [r for r in rows if r["company_id"] == company_id]
    if not include_inactive:
        rows = [r for r in rows if r["status"] == "ACTIVE"]
    return {"count": len(rows), "items": rows}


@router.post("/branch/create")
def create_branch(payload: BranchCreateRequest):
    company = _active_company(payload.company_id)
    if any(b["branch_code"].lower() == payload.branch_code.lower() and b["company_id"] == payload.company_id for b in _BRANCHES.values()):
        raise HTTPException(status_code=409, detail="Duplicate branch code within company")

    next_id = max(_BRANCHES.keys(), default=0) + 1
    row = {"id": next_id, **payload.model_dump(), "status": "ACTIVE" if payload.status else "INACTIVE"}
    _BRANCHES[next_id] = row
    _audit("BRANCH_CREATED", next_id, {**row, "company_name": company["company_name"]})
    return row


@router.put("/branch/update/{branch_id}")
def update_branch(branch_id: int, payload: BranchUpdateRequest):
    existing = _BRANCHES.get(branch_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Branch not found")
    _active_company(payload.company_id)
    existing.update(payload.model_dump())
    existing["status"] = "ACTIVE" if payload.status else "INACTIVE"
    _audit("BRANCH_UPDATED", branch_id, existing)
    return existing


@router.post("/branch/deactivate/{branch_id}")
def deactivate_branch(branch_id: int):
    branch = _BRANCHES.get(branch_id)
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    has_dependency = any(d["branch_id"] == branch_id and d["status"] == "ACTIVE" for d in _DEPARTMENTS.values())
    if has_dependency:
        raise HTTPException(status_code=409, detail="Branch has active departments/users; deactivation blocked")
    branch["status"] = "INACTIVE"
    _audit("BRANCH_DEACTIVATED", branch_id, branch)
    return {"status": "success", "item": branch}


@router.get("/masters/departments")
@router.get("/department/list")
def list_departments(company_id: int | None = None, branch_id: int | None = None, include_inactive: bool = True):
    rows = list(_DEPARTMENTS.values())
    if company_id is not None:
        rows = [r for r in rows if r["company_id"] == company_id]
    if branch_id is not None:
        rows = [r for r in rows if r["branch_id"] == branch_id]
    if not include_inactive:
        rows = [r for r in rows if r["status"] == "ACTIVE"]
    return {"count": len(rows), "items": rows}


@router.post("/department/create")
def create_department(payload: DepartmentCreateRequest):
    _active_company(payload.company_id)
    branch = _BRANCHES.get(payload.branch_id)
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    if branch["company_id"] != payload.company_id:
        raise HTTPException(status_code=422, detail="Branch must belong to selected company")
    if branch["status"] != "ACTIVE":
        raise HTTPException(status_code=422, detail="Branch inactive: creation blocked")

    if any(
        d["department_code"].lower() == payload.department_code.lower() and d["branch_id"] == payload.branch_id
        for d in _DEPARTMENTS.values()
    ):
        raise HTTPException(status_code=409, detail="Duplicate department code under same branch")

    next_id = max(_DEPARTMENTS.keys(), default=0) + 1
    row = {"id": next_id, **payload.model_dump(), "status": "ACTIVE" if payload.status else "INACTIVE"}
    _DEPARTMENTS[next_id] = row
    _audit("DEPARTMENT_CREATED", next_id, row)
    return row


@router.put("/department/update/{department_id}")
def update_department(department_id: int, payload: DepartmentUpdateRequest):
    existing = _DEPARTMENTS.get(department_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Department not found")

    branch = _BRANCHES.get(payload.branch_id)
    if not branch or branch["company_id"] != payload.company_id:
        raise HTTPException(status_code=422, detail="Branch-company mismatch")

    existing.update(payload.model_dump())
    existing["status"] = "ACTIVE" if payload.status else "INACTIVE"
    _audit("DEPARTMENT_UPDATED", department_id, existing)
    return existing


@router.post("/department/deactivate/{department_id}")
def deactivate_department(department_id: int):
    row = _DEPARTMENTS.get(department_id)
    if not row:
        raise HTTPException(status_code=404, detail="Department not found")
    row["status"] = "INACTIVE"
    _audit("DEPARTMENT_DEACTIVATED", department_id, row)
    return {"status": "success", "item": row}
