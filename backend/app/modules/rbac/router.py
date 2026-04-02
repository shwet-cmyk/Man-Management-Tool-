from __future__ import annotations

from fastapi import APIRouter

from app.modules.rbac.privileges import ROLE_GRANTS, build_catalog, is_granted

router = APIRouter(prefix="/rbac", tags=["Users & Roles"])


@router.get("/permission-tree")
def permission_tree():
    catalog = build_catalog()
    return {"module": "API", "children": [x["code"] for x in catalog[:200]]}


@router.get("/privileges/catalog")
def privilege_catalog():
    catalog = build_catalog()
    return {"count": len(catalog), "items": catalog}


@router.get("/default-role-mapping")
def default_role_mapping():
    return ROLE_GRANTS


@router.get('/check')
def check_privilege(role: str, code: str):
    return {'role': role, 'code': code, 'allowed': is_granted(role, code)}


@router.get('/field-matrix/{module_name}')
def field_matrix(module_name: str):
    base = module_name.upper()
    fields = ['status', 'priority', 'assignee', 'planned_start', 'planned_end', 'actual_start', 'actual_end', 'cost', 'billable', 'approval_required']
    rows = []
    for f in fields:
        visible_code = f'{base}_VIEW_FIELD_VISIBLE'
        editable_code = f'{base}_EDIT_FIELD_EDITABLE'
        rows.append({'field': f, 'visible_privilege': visible_code, 'editable_privilege': editable_code})
    return {'module': base, 'rows': rows}
