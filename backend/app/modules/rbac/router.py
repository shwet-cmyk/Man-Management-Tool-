from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.rbac.schemas import (
    AccessCheckRequest,
    ApprovalCheckRequest,
    ApprovalLimitRequest,
    PermissionAssignRequest,
    PermissionScopeRequest,
    RoleCreateRequest,
    RoleUpdateRequest,
    UserAssignRoleRequest,
)
from app.modules.rbac.service import RbacService

router = APIRouter(prefix="", tags=["Work Management - RBAC"])


class RoleInheritanceRequest(BaseModel):
    parent_role_id: int
    child_role_id: int


class OverrideRequest(BaseModel):
    user_id: int
    permission_id: int
    is_allowed: bool


@router.post("/roles")
def create_role(payload: RoleCreateRequest, db: Session = Depends(get_db)):
    return RbacService(db).create_role(payload)


@router.get("/roles")
def list_roles(db: Session = Depends(get_db)):
    return RbacService(db).list_roles()


@router.put("/roles/{role_id}")
def update_role(role_id: int, payload: RoleUpdateRequest, db: Session = Depends(get_db)):
    return RbacService(db).update_role(role_id, payload)


@router.delete("/roles/{role_id}")
def delete_role(role_id: int, db: Session = Depends(get_db)):
    return RbacService(db).delete_role(role_id)


@router.post("/roles/{role_id}/permissions")
def assign_permission(role_id: int, payload: PermissionAssignRequest, db: Session = Depends(get_db)):
    return RbacService(db).assign_permission(role_id, payload)


@router.get("/roles/{role_id}/permissions")
def list_role_permissions(role_id: int, db: Session = Depends(get_db)):
    return RbacService(db).list_role_permissions(role_id)


@router.post("/users/{user_id}/assign-role")
def assign_role(user_id: int, payload: UserAssignRoleRequest, db: Session = Depends(get_db)):
    return RbacService(db).assign_user_role(user_id, payload.role_id)


@router.post("/users/roles")
def assign_role_alias(payload: UserAssignRoleRequest, db: Session = Depends(get_db)):
    if payload.user_id is None:
        raise HTTPException(status_code=422, detail="user_id is required")
    return RbacService(db).assign_user_role(payload.user_id, payload.role_id)


@router.get("/users/{user_id}/permissions")
def list_user_permissions(user_id: int, db: Session = Depends(get_db)):
    return RbacService(db).list_user_permissions(user_id)


@router.post("/permissions/{permission_id}/scope")
def assign_scope(permission_id: int, payload: PermissionScopeRequest, db: Session = Depends(get_db)):
    return RbacService(db).assign_scope(permission_id, payload)


@router.post("/role-inheritance")
def add_role_inheritance(payload: RoleInheritanceRequest, db: Session = Depends(get_db)):
    return RbacService(db).add_role_inheritance(payload.parent_role_id, payload.child_role_id)


@router.post("/overrides")
def add_override(payload: OverrideRequest, db: Session = Depends(get_db)):
    return RbacService(db).add_user_override(payload.user_id, payload.permission_id, payload.is_allowed)


@router.post("/access/check")
def check_access(payload: AccessCheckRequest, db: Session = Depends(get_db)):
    return RbacService(db).check_access(payload)


@router.post("/auth/check-permission")
def check_access_alias(payload: AccessCheckRequest, db: Session = Depends(get_db)):
    return RbacService(db).check_access(payload)


@router.post("/users/{user_id}/approval-limit")
def upsert_approval_limit(user_id: int, payload: ApprovalLimitRequest, db: Session = Depends(get_db)):
    return RbacService(db).upsert_approval_limit(user_id, payload)


@router.post("/approvals/check")
def check_approval_limit(payload: ApprovalCheckRequest, db: Session = Depends(get_db)):
    return RbacService(db).check_approval_limit(payload)
