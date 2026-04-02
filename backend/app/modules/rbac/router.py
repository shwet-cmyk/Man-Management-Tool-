from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/rbac", tags=["Users & Roles"])

MODULES = [
    "PROJECT",
    "PHASE",
    "TASK",
    "JOB",
    "TIMESHEET",
    "APPROVAL",
    "NOTIFICATION",
    "CHAT",
    "AUDIT",
    "DASHBOARD",
    "REPORT",
    "ANALYTICS",
    "AUTOMATION",
    "TEMPLATE",
    "INTERCONNECT",
    "GOAL",
    "PORTFOLIO",
    "CLIENT_PORTAL",
    "DOCUMENTATION",
]

ACTIONS = [
    "VIEW",
    "CREATE",
    "EDIT",
    "DELETE",
    "ASSIGN",
    "APPROVE",
    "REJECT",
    "SEND_BACK",
    "CHANGE_STATUS",
    "EXPORT",
    "PRINT",
    "REPORT_VIEW",
    "ANALYTICS_VIEW",
    "AUDIT_VIEW",
    "TRIGGER_ACTION",
    "CONFIGURE_DASHBOARD",
    "CONFIGURE_TEMPLATES",
    "CONFIGURE_AUTOMATION",
    "VIEW_SENSITIVE_FIELDS",
]

SURFACES = ["SCREEN", "PANEL", "TAB", "WIDGET", "FIELD_VISIBLE", "FIELD_EDITABLE"]


def build_catalog() -> list[dict]:
    catalog = []
    idx = 1
    for module in MODULES:
        for action in ACTIONS:
            for surface in SURFACES:
                catalog.append(
                    {
                        "privilege_id": f"PRV-{idx:05d}",
                        "code": f"{module}_{action}_{surface}",
                        "module": module,
                        "action": action,
                        "surface": surface,
                    }
                )
                idx += 1
    return catalog


API_PERMISSION_TREE = {"module": "API", "children": [x["code"] for x in build_catalog()[:50]]}


@router.get("/permission-tree")
def permission_tree():
    return API_PERMISSION_TREE


@router.get("/privileges/catalog")
def privilege_catalog():
    catalog = build_catalog()
    return {"count": len(catalog), "items": catalog}


@router.get("/default-role-mapping")
def default_role_mapping():
    return {
        "Admin": ["*"],
        "SuperAdmin": ["*"],
        "Manager": ["*_VIEW_*", "*_CREATE_*", "*_EDIT_*", "*_APPROVE_*"],
        "Auditor": ["*_VIEW_*", "*_AUDIT_VIEW_*", "*_REPORT_VIEW_*"],
        "Employee": ["TASK_VIEW_SCREEN", "TIMESHEET_CREATE_SCREEN", "CHAT_VIEW_SCREEN"],
    }
