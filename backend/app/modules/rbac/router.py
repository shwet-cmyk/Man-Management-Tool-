from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.modules.rbac.privileges import ROLE_GRANTS, build_catalog, is_granted

router = APIRouter(tags=["Users & Roles"])

_ROLES: dict[int, dict] = {
    1: {
        "id": 1,
        "role_name": "Super Admin",
        "role_code": "SUPER_ADMIN",
        "parent_role": None,
        "status": "ACTIVE",
        "description": "Global administration role",
        "permissions": ["*"]
    },
    2: {
        "id": 2,
        "role_name": "Admin",
        "role_code": "ADMIN",
        "parent_role": "SUPER_ADMIN",
        "status": "ACTIVE",
        "description": "Administrative role",
        "permissions": ["USER_VIEW", "USER_EDIT", "ROLE_VIEW", "ROLE_EDIT"],
    },
}


class RolePayload(BaseModel):
    role_name: str
    role_code: str
    parent_role: str | None = None
    status: bool = True
    description: str | None = None
    permissions: list[str]


@router.get("/rbac/permission-tree")
def permission_tree():
    catalog = build_catalog()
    return {"module": "API", "children": [x["code"] for x in catalog[:200]]}


@router.get("/rbac/privileges/catalog")
def privilege_catalog():
    catalog = build_catalog()
    return {"count": len(catalog), "items": catalog}


@router.get("/rbac/default-role-mapping")
def default_role_mapping():
    return ROLE_GRANTS


@router.get('/rbac/check')
def check_privilege(role: str, code: str):
    return {'role': role, 'code': code, 'allowed': is_granted(role, code)}


@router.get('/rbac/field-matrix/{module_name}')
def field_matrix(module_name: str):
    base = module_name.upper()
    fields = ['status', 'priority', 'assignee', 'planned_start', 'planned_end', 'actual_start', 'actual_end', 'cost', 'billable', 'approval_required']
    rows = []
    for f in fields:
        visible_code = f'{base}_VIEW_FIELD_VISIBLE'
        editable_code = f'{base}_EDIT_FIELD_EDITABLE'
        rows.append({'field': f, 'visible_privilege': visible_code, 'editable_privilege': editable_code})
    return {'module': base, 'rows': rows}


@router.get("/roles/list")
def list_roles(include_inactive: bool = True):
    rows = list(_ROLES.values())
    if not include_inactive:
        rows = [r for r in rows if r["status"] == "ACTIVE"]
    return {"count": len(rows), "items": rows}


@router.get("/roles/{role_id}")
def get_role(role_id: int):
    role = _ROLES.get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.post("/roles/create")
def create_role(payload: RolePayload):
    if any(r["role_code"].lower() == payload.role_code.lower() for r in _ROLES.values()):
        raise HTTPException(status_code=409, detail="Duplicate role code blocked")
    if payload.parent_role and payload.parent_role == payload.role_code:
        raise HTTPException(status_code=422, detail="Parent role cannot create circular inheritance")
    if payload.status and not payload.permissions:
        raise HTTPException(status_code=422, detail="At least one permission required for active role")

    next_id = max(_ROLES.keys(), default=0) + 1
    _ROLES[next_id] = {
        "id": next_id,
        "role_name": payload.role_name,
        "role_code": payload.role_code,
        "parent_role": payload.parent_role,
        "status": "ACTIVE" if payload.status else "INACTIVE",
        "description": payload.description,
        "permissions": payload.permissions,
        "created_at": datetime.now(UTC).isoformat(),
    }
    return _ROLES[next_id]


@router.put("/roles/update/{role_id}")
def update_role(role_id: int, payload: RolePayload):
    role = _ROLES.get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    for rid, row in _ROLES.items():
        if rid != role_id and row["role_code"].lower() == payload.role_code.lower():
            raise HTTPException(status_code=409, detail="Duplicate role code blocked")

    role.update(
        {
            "role_name": payload.role_name,
            "role_code": payload.role_code,
            "parent_role": payload.parent_role,
            "status": "ACTIVE" if payload.status else "INACTIVE",
            "description": payload.description,
            "permissions": payload.permissions,
            "updated_at": datetime.now(UTC).isoformat(),
        }
    )
    return role


@router.post("/roles/clone/{role_id}")
def clone_role(role_id: int):
    role = _ROLES.get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    next_id = max(_ROLES.keys(), default=0) + 1
    clone = {**role, "id": next_id, "role_code": f"{role['role_code']}_CLONE_{next_id}", "role_name": f"{role['role_name']} (Clone)"}
    _ROLES[next_id] = clone
    return clone


@router.post("/roles/deactivate/{role_id}")
def deactivate_role(role_id: int):
    role = _ROLES.get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    role["status"] = "INACTIVE"
    return {"status": "success", "item": role}


@router.get("/roles/analytics")
def role_analytics():
    rows = list(_ROLES.values())
    usage_count = {r["role_code"]: len(r["permissions"]) for r in rows}
    privileged = sorted(rows, key=lambda r: len(r["permissions"]), reverse=True)
    return {
        "role_usage_count": usage_count,
        "most_privileged_roles": [r["role_code"] for r in privileged[:5]],
        "permission_distribution_heatmap": [{"role_code": r["role_code"], "permission_count": len(r["permissions"])} for r in rows],
    }
