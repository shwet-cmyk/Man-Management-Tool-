from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.event_bus import publish_event
from app.modules.projects.router import PROJECTS
from app.modules.system_audit.router import AuditCreateRequest, add_audit_entry

router = APIRouter(prefix="/portfolios", tags=["Portfolio Management"])


class PortfolioCreateRequest(BaseModel):
    portfolio_name: str
    owner: str
    project_ids: list[int] = Field(default_factory=list)
    budget: float = 0.0
    status: str = "ACTIVE"


PORTFOLIOS: dict[int, dict] = {}


@router.post("")
def create_portfolio(payload: PortfolioCreateRequest):
    missing_projects = [p for p in payload.project_ids if p not in PROJECTS]
    if missing_projects:
        raise HTTPException(status_code=422, detail=f"Unknown project_ids: {missing_projects}")

    portfolio_id = len(PORTFOLIOS) + 1
    row = {
        "portfolio_id": portfolio_id,
        **payload.model_dump(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    PORTFOLIOS[portfolio_id] = row
    add_audit_entry(
        AuditCreateRequest(
            user_name=payload.owner,
            module="PORTFOLIO",
            reference_id=str(portfolio_id),
            action_type="CREATE",
            new_value={"projects": payload.project_ids},
        )
    )
    publish_event("PORTFOLIO_CREATED", {"portfolio_id": portfolio_id, "owner": payload.owner})
    return row


@router.get("")
def list_portfolios():
    return list(PORTFOLIOS.values())


@router.get("/{portfolio_id}/dashboard")
def portfolio_dashboard(portfolio_id: int):
    row = PORTFOLIOS.get(portfolio_id)
    if not row:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    projects = [PROJECTS[p] for p in row["project_ids"] if p in PROJECTS]
    total_estimated = sum(p["estimated_cost"] for p in projects)
    total_actual = sum(p["actual_cost"] for p in projects)
    delayed = len([p for p in projects if p["status"] == "DELAYED"])

    weighted_progress = round(sum(p.get("progress_pct", 0) for p in projects) / len(projects), 2) if projects else 0.0
    return {
        "portfolio_id": portfolio_id,
        "portfolio_name": row["portfolio_name"],
        "completion_pct": weighted_progress,
        "cost": {
            "budget": row["budget"],
            "estimated": total_estimated,
            "actual": total_actual,
            "variance": row["budget"] - total_actual,
        },
        "risk": {
            "delayed_projects": delayed,
            "at_risk_projects": len([p for p in projects if p.get("health_status") == "AT_RISK"]),
        },
        "project_count": len(projects),
    }
