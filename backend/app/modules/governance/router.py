from fastapi import APIRouter

from app.services.module_compliance_registry import module_compliance_report

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


@router.get('/module-compliance')
def module_compliance():
    return module_compliance_report()
