from __future__ import annotations

from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.interconnect_registry import REQUIRED_INTERCONNECTS, coverage_matrix as required_coverage_matrix, mark_covered

router = APIRouter(prefix="/interconnects", tags=["Interconnect Master"])


class FlowDirection(str, Enum):
    upstream = "UPSTREAM"
    downstream = "DOWNSTREAM"
    bidirectional = "BIDIRECTIONAL"


class InterconnectStatus(str, Enum):
    active = "ACTIVE"
    draft = "DRAFT"
    blocked = "BLOCKED"


class CoverageStatus(str, Enum):
    pending = "PENDING"
    covered = "COVERED"


class InterconnectCreateRequest(BaseModel):
    source_module_id: str = Field(..., min_length=2)
    target_module_id: str = Field(..., min_length=2)
    trigger_event: str = Field(..., min_length=2)
    source_status: str = Field(..., min_length=2)
    action_type: str = Field(..., min_length=2)
    flow_direction: FlowDirection
    data_flow: str = Field(..., min_length=2)
    validation_rules: list[str] = Field(default_factory=list)
    status_dependency: str = Field(..., min_length=2)
    failure_handling: str = Field(..., min_length=2)
    audit_required: bool = True
    allow_circular: bool = False
    use_case_reference: str | None = None
    expected_output: str | None = None


class CoverageUpdateRequest(BaseModel):
    coverage_status: CoverageStatus
    acknowledgement_note: str | None = None


INTERCONNECTS: dict[int, dict] = {}
MODULES = {x for pair in REQUIRED_INTERCONNECTS for x in pair} | {"LOGIN", "RBAC", "USER_MASTER", "ORG_MASTER", "REPORTS", "ANALYTICS", "INTERCONNECT_MASTER"}


def _detect_circular(source: str, target: str) -> bool:
    return any(row["source_module_id"] == target and row["target_module_id"] == source for row in INTERCONNECTS.values())


@router.get("/modules")
def list_modules():
    return sorted(MODULES)


@router.get("")
def list_interconnects(source_module_id: str | None = None, target_module_id: str | None = None, coverage_status: CoverageStatus | None = None):
    rows = list(INTERCONNECTS.values())
    if source_module_id:
        rows = [r for r in rows if r["source_module_id"] == source_module_id]
    if target_module_id:
        rows = [r for r in rows if r["target_module_id"] == target_module_id]
    if coverage_status:
        rows = [r for r in rows if r["coverage_status"] == coverage_status]
    return rows


@router.post("")
def create_interconnect(payload: InterconnectCreateRequest):
    if payload.source_module_id not in MODULES:
        raise HTTPException(status_code=422, detail="Missing source module")
    if payload.target_module_id not in MODULES:
        raise HTTPException(status_code=422, detail="Missing target module")
    if payload.source_module_id == payload.target_module_id:
        raise HTTPException(status_code=422, detail="Source and target cannot be identical")
    if _detect_circular(payload.source_module_id, payload.target_module_id) and not payload.allow_circular:
        raise HTTPException(status_code=422, detail="Circular dependency detected")

    next_id = len(INTERCONNECTS) + 1
    record = {
        "interconnect_id": next_id,
        **payload.model_dump(),
        "status": InterconnectStatus.active,
        "coverage_status": CoverageStatus.pending,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "audit_log": [
            {
                "event": "INTERCONNECT_CREATED",
                "at": datetime.utcnow(),
                "audit_required": payload.audit_required,
            }
        ],
    }
    INTERCONNECTS[next_id] = record
    mark_covered(payload.source_module_id, payload.target_module_id, source_ref=f"interconnect:{next_id}")
    return record


@router.patch("/{interconnect_id}/coverage")
def update_coverage(interconnect_id: int, payload: CoverageUpdateRequest):
    row = INTERCONNECTS.get(interconnect_id)
    if not row:
        raise HTTPException(status_code=404, detail="Interconnect not found")
    row["coverage_status"] = payload.coverage_status
    row["updated_at"] = datetime.utcnow()
    row["audit_log"].append({
        "event": "COVERAGE_UPDATED",
        "at": datetime.utcnow(),
        "note": payload.acknowledgement_note,
    })
    return row


@router.get("/coverage-matrix")
def coverage_matrix():
    matrix: dict[str, dict[str, str]] = {}
    for module in MODULES:
        matrix[module] = {}
        for mod2 in MODULES:
            matrix[module][mod2] = "-"

    for row in INTERCONNECTS.values():
        matrix[row["source_module_id"]][row["target_module_id"]] = row["coverage_status"]

    return {"declared": matrix, "required": required_coverage_matrix()}


@router.get("/reports/summary")
def interconnect_reports():
    total = len(INTERCONNECTS)
    covered = len([r for r in INTERCONNECTS.values() if r["coverage_status"] == CoverageStatus.covered])
    unresolved = total - covered
    connectivity: dict[str, int] = {m: 0 for m in MODULES}
    for r in INTERCONNECTS.values():
        connectivity[r["source_module_id"]] += 1
        connectivity[r["target_module_id"]] += 1

    return {
        "module_vs_interconnect_matrix": coverage_matrix(),
        "covered": covered,
        "uncovered": unresolved,
        "most_connected_modules": sorted(connectivity.items(), key=lambda x: x[1], reverse=True)[:5],
        "high_dependency_risk_areas": [m for m, c in connectivity.items() if c >= 3],
    }
