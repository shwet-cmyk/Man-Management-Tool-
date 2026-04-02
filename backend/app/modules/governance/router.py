from fastapi import APIRouter

router = APIRouter(prefix="/governance", tags=["Governance"])


@router.get("/validation-rules")
def validation_rules():
    return {
        "field_level": ["mandatory", "format", "type"],
        "business_level": ["rbac_check", "scope_check", "hierarchy_check"],
    }


@router.get("/audit-events")
def audit_events():
    return {
        "tracked": ["field_changes", "role_changes", "status_changes", "login"],
        "audit_first": True,
    }
