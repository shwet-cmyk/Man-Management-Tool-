from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from app.modules.timesheet.router import TIMESHEETS

router = APIRouter(prefix="/billing", tags=["Billing & Costing"])
BILLING_DRAFTS: dict[int, dict] = {}


def _profitability(row: dict):
    return round(row["billing_amount"] - row["cost_amount"], 2)


@router.get("/overview")
def billing_overview(project: str | None = None, billing_status: str | None = None):
    rows = list(BILLING_DRAFTS.values())
    if project:
        rows = [r for r in rows if r["project"] == project]
    if billing_status:
        rows = [r for r in rows if r["billing_status"] == billing_status]
    return {"count": len(rows), "items": rows}


@router.post("/generate-draft")
def generate_billing_draft(period: str = "CURRENT"):
    approved = [r for r in TIMESHEETS.values() if r["approval_status"] == "APPROVED" and r["billable"]]
    grouped: dict[str, list[dict]] = {}
    for row in approved:
        grouped.setdefault(row["project"], []).append(row)

    created = []
    for project, entries in grouped.items():
        did = len(BILLING_DRAFTS) + 1
        billable_hours = sum(e["hours_logged"] for e in entries)
        billing_amount = round(billable_hours * 100, 2)
        cost_amount = round(billable_hours * 60, 2)
        draft = {
            "id": did,
            "reference_no": f"BIL-{datetime.now(UTC).year}-{did:05d}",
            "project": project,
            "customer": "Internal",
            "billable_hours": billable_hours,
            "billing_amount": billing_amount,
            "cost_amount": cost_amount,
            "profitability": round(billing_amount - cost_amount, 2),
            "billing_status": "DRAFT",
            "approval_status": "PENDING",
            "period": period,
            "created_at": datetime.now(UTC).isoformat(),
        }
        BILLING_DRAFTS[did] = draft
        created.append(draft)
    return {"generated": len(created), "items": created}


@router.get("/cost-detail/{draft_id}")
def cost_detail(draft_id: int):
    row = BILLING_DRAFTS.get(draft_id)
    if not row:
        raise HTTPException(status_code=404, detail="Draft not found")
    return {
        "reference_no": row["reference_no"],
        "project": row["project"],
        "billing_amount": row["billing_amount"],
        "cost_amount": row["cost_amount"],
        "profitability": _profitability(row),
        "cost_elements": [{"name": "effort_cost", "amount": row["cost_amount"]}],
    }


@router.post("/approve/{draft_id}")
def approve_billing(draft_id: int, remarks: str | None = None):
    row = BILLING_DRAFTS.get(draft_id)
    if not row:
        raise HTTPException(status_code=404, detail="Draft not found")
    row["approval_status"] = "APPROVED"
    row["billing_status"] = "APPROVED"
    row["remarks"] = remarks
    return row


@router.post("/mark-invoiced/{draft_id}")
def mark_invoiced(draft_id: int):
    row = BILLING_DRAFTS.get(draft_id)
    if not row:
        raise HTTPException(status_code=404, detail="Draft not found")
    if row["approval_status"] != "APPROVED":
        raise HTTPException(status_code=422, detail="Approvals incomplete, draft billing blocked")
    row["billing_status"] = "INVOICED"
    return row
