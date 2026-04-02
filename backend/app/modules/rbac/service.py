from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.wm_rbac_action import WmRbacAction
from app.models.wm_rbac_access_log import WmRbacAccessLog
from app.models.wm_rbac_approval_limit import WmRbacApprovalLimit
from app.models.wm_rbac_feature import WmRbacFeature
from app.models.wm_rbac_module import WmRbacModule
from app.models.wm_rbac_permission import WmRbacPermission
from app.models.wm_rbac_permission_scope import WmRbacPermissionScope
from app.models.wm_rbac_role import WmRbacRole
from app.models.wm_rbac_role_inheritance import WmRbacRoleInheritance
from app.models.wm_rbac_user_permission_override import WmRbacUserPermissionOverride
from app.models.wm_rbac_user_role import WmRbacUserRole
from app.modules.rbac.schemas import (
    AccessCheckRequest,
    ApprovalCheckRequest,
    ApprovalLimitRequest,
    PermissionAssignRequest,
    PermissionScopeRequest,
    RoleCreateRequest,
    RoleUpdateRequest,
)


class RbacService:
    def __init__(self, db: Session):
        self.db = db

    def create_role(self, payload: RoleCreateRequest):
        role = WmRbacRole(name=payload.name, description=payload.description, is_system_role=payload.is_system_role)
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return {"role_id": role.role_id, "name": role.name}

    def list_roles(self):
        rows = self.db.query(WmRbacRole).order_by(WmRbacRole.role_id.asc()).all()
        return [{"role_id": x.role_id, "name": x.name, "description": x.description, "is_active": x.is_active} for x in rows]

    def update_role(self, role_id: int, payload: RoleUpdateRequest):
        role = self.db.query(WmRbacRole).filter(WmRbacRole.role_id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        if payload.name is not None:
            role.name = payload.name
        if payload.description is not None:
            role.description = payload.description
        if payload.is_active is not None:
            role.is_active = payload.is_active
        self.db.commit()
        return {"role_id": role.role_id, "name": role.name, "is_active": role.is_active}

    def delete_role(self, role_id: int):
        role = self.db.query(WmRbacRole).filter(WmRbacRole.role_id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        role.is_active = False
        self.db.commit()
        return {"status": "SUCCESS", "role_id": role_id}

    def assign_permission(self, role_id: int, payload: PermissionAssignRequest):
        role = self.db.query(WmRbacRole).filter(WmRbacRole.role_id == role_id, WmRbacRole.is_active.is_(True)).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        module = self._get_or_create_module(payload.module_name)
        feature = self._get_or_create_feature(module.module_id, payload.feature_name)
        action = self._get_or_create_action(payload.action_name)

        permission = (
            self.db.query(WmRbacPermission)
            .filter(
                WmRbacPermission.role_id == role_id,
                WmRbacPermission.feature_id == feature.feature_id,
                WmRbacPermission.action_id == action.action_id,
            )
            .first()
        )
        if not permission:
            permission = WmRbacPermission(role_id=role_id, feature_id=feature.feature_id, action_id=action.action_id, is_allowed=payload.is_allowed)
        else:
            permission.is_allowed = payload.is_allowed

        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        return {"permission_id": permission.permission_id, "role_id": role_id}

    def list_role_permissions(self, role_id: int):
        rows = self.db.query(WmRbacPermission).filter(WmRbacPermission.role_id == role_id).all()
        out = []
        for row in rows:
            feature = self.db.query(WmRbacFeature).filter(WmRbacFeature.feature_id == row.feature_id).first()
            module = self.db.query(WmRbacModule).filter(WmRbacModule.module_id == feature.module_id).first() if feature else None
            action = self.db.query(WmRbacAction).filter(WmRbacAction.action_id == row.action_id).first()
            scopes = self.db.query(WmRbacPermissionScope).filter(WmRbacPermissionScope.permission_id == row.permission_id).all()
            out.append(
                {
                    "permission_id": row.permission_id,
                    "module_name": module.name if module else None,
                    "feature_name": feature.name if feature else None,
                    "action_name": action.name if action else None,
                    "is_allowed": row.is_allowed,
                    "scopes": [
                        {"company_id": s.company_id, "branch_id": s.branch_id, "department_id": s.department_id}
                        for s in scopes
                    ],
                }
            )
        return out

    def assign_user_role(self, user_id: int, role_id: int):
        role = self.db.query(WmRbacRole).filter(WmRbacRole.role_id == role_id, WmRbacRole.is_active.is_(True)).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found or inactive")
        exists = self.db.query(WmRbacUserRole).filter(WmRbacUserRole.user_id == user_id, WmRbacUserRole.role_id == role_id).first()
        if exists:
            return {"status": "SUCCESS", "message": "Role already assigned", "user_id": user_id, "role_id": role_id}
        row = WmRbacUserRole(user_id=user_id, role_id=role_id)
        self.db.add(row)
        self.db.commit()
        return {"status": "SUCCESS", "user_id": user_id, "role_id": role_id}

    def assign_scope(self, permission_id: int, payload: PermissionScopeRequest):
        row = WmRbacPermissionScope(
            permission_id=permission_id,
            company_id=payload.company_id,
            branch_id=payload.branch_id,
            department_id=payload.department_id,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return {"scope_id": row.scope_id, "permission_id": permission_id}

    def add_role_inheritance(self, parent_role_id: int, child_role_id: int):
        row = WmRbacRoleInheritance(parent_role_id=parent_role_id, child_role_id=child_role_id)
        self.db.add(row)
        self.db.commit()
        return {"status": "SUCCESS", "parent_role_id": parent_role_id, "child_role_id": child_role_id}

    def add_user_override(self, user_id: int, permission_id: int, is_allowed: bool):
        row = WmRbacUserPermissionOverride(user_id=user_id, permission_id=permission_id, is_allowed=is_allowed)
        self.db.add(row)
        self.db.commit()
        return {"override_id": row.override_id, "is_allowed": row.is_allowed}

    def list_user_permissions(self, user_id: int):
        permission_rows = self._resolve_user_permission_rows(user_id)
        out = []
        for row in permission_rows:
            feature = self.db.query(WmRbacFeature).filter(WmRbacFeature.feature_id == row.feature_id).first()
            module = self.db.query(WmRbacModule).filter(WmRbacModule.module_id == feature.module_id).first() if feature else None
            action = self.db.query(WmRbacAction).filter(WmRbacAction.action_id == row.action_id).first()
            out.append(
                {
                    "permission_id": row.permission_id,
                    "module_name": module.name if module else None,
                    "feature_name": feature.name if feature else None,
                    "action_name": action.name if action else None,
                    "is_allowed": row.is_allowed,
                }
            )
        return out

    def check_access(self, payload: AccessCheckRequest):
        feature = (
            self.db.query(WmRbacFeature)
            .join(WmRbacModule, WmRbacModule.module_id == WmRbacFeature.module_id)
            .filter(WmRbacModule.name == payload.module_name, WmRbacFeature.name == payload.feature_name)
            .first()
        )
        action = self.db.query(WmRbacAction).filter(WmRbacAction.name == payload.action_name).first()
        if not feature or not action:
            return self._access_result(payload, False, "Permission key not configured")

        permission_rows = self._resolve_user_permission_rows(payload.user_id)
        matched = [x for x in permission_rows if x.feature_id == feature.feature_id and x.action_id == action.action_id]
        if not matched:
            return self._access_result(payload, False, "No permission")

        # deny takes precedence
        scoped_outcomes = []
        for perm in matched:
            scopes = self.db.query(WmRbacPermissionScope).filter(WmRbacPermissionScope.permission_id == perm.permission_id).all()
            if not scopes:
                scoped_outcomes.append(perm.is_allowed)
                continue
            for scope in scopes:
                if self._match_scope(scope, payload):
                    scoped_outcomes.append(perm.is_allowed)

        if not scoped_outcomes:
            return self._access_result(payload, False, "Scope mismatch")
        if any(x is False for x in scoped_outcomes):
            return self._access_result(payload, False, "Denied by role/override")
        return self._access_result(payload, True, "Allowed")

    def upsert_approval_limit(self, user_id: int, payload: ApprovalLimitRequest):
        row = self.db.query(WmRbacApprovalLimit).filter(WmRbacApprovalLimit.user_id == user_id, WmRbacApprovalLimit.module_name == payload.module_name).first()
        if not row:
            row = WmRbacApprovalLimit(user_id=user_id, module_name=payload.module_name, max_amount=payload.max_amount)
        else:
            row.max_amount = payload.max_amount
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return {"approval_limit_id": row.approval_limit_id, "user_id": row.user_id, "module_name": row.module_name, "max_amount": float(row.max_amount)}

    def check_approval_limit(self, payload: ApprovalCheckRequest):
        row = self.db.query(WmRbacApprovalLimit).filter(WmRbacApprovalLimit.user_id == payload.user_id, WmRbacApprovalLimit.module_name == payload.module_name).first()
        if not row:
            return {"allowed": False, "reason": "Approval limit not configured"}
        allowed = float(payload.amount) <= float(row.max_amount)
        return {
            "allowed": allowed,
            "reason": "Allowed" if allowed else "Amount exceeds approval limit",
            "configured_limit": float(row.max_amount),
        }

    def _resolve_user_permission_rows(self, user_id: int):
        role_ids = {x.role_id for x in self.db.query(WmRbacUserRole).filter(WmRbacUserRole.user_id == user_id).all()}
        expanded = set(role_ids)
        changed = True
        while changed:
            changed = False
            inheritance_rows = self.db.query(WmRbacRoleInheritance).filter(WmRbacRoleInheritance.child_role_id.in_(expanded)).all()
            for row in inheritance_rows:
                if row.parent_role_id not in expanded:
                    expanded.add(row.parent_role_id)
                    changed = True

        perms = self.db.query(WmRbacPermission).filter(WmRbacPermission.role_id.in_(expanded)).all() if expanded else []

        overrides = self.db.query(WmRbacUserPermissionOverride).filter(WmRbacUserPermissionOverride.user_id == user_id).all()
        override_map = {x.permission_id: x.is_allowed for x in overrides}
        for perm in perms:
            if perm.permission_id in override_map:
                perm.is_allowed = override_map[perm.permission_id]
        return perms

    def _access_result(self, payload: AccessCheckRequest, allowed: bool, reason: str):
        self.db.add(
            WmRbacAccessLog(
                user_id=payload.user_id,
                module_name=payload.module_name,
                feature_name=payload.feature_name,
                action_name=payload.action_name,
                entity_id=payload.entity_id,
                is_allowed=allowed,
                reason=reason,
            )
        )
        self.db.commit()
        return {"allowed": allowed, "reason": reason}

    @staticmethod
    def _match_scope(scope: WmRbacPermissionScope, payload: AccessCheckRequest):
        return (
            (scope.company_id is None or scope.company_id == payload.company_id)
            and (scope.branch_id is None or scope.branch_id == payload.branch_id)
            and (scope.department_id is None or scope.department_id == payload.department_id)
        )

    def _get_or_create_module(self, name: str):
        row = self.db.query(WmRbacModule).filter(WmRbacModule.name == name).first()
        if not row:
            row = WmRbacModule(name=name)
            self.db.add(row)
            self.db.flush()
        return row

    def _get_or_create_feature(self, module_id: int, name: str):
        row = self.db.query(WmRbacFeature).filter(WmRbacFeature.module_id == module_id, WmRbacFeature.name == name).first()
        if not row:
            row = WmRbacFeature(module_id=module_id, name=name)
            self.db.add(row)
            self.db.flush()
        return row

    def _get_or_create_action(self, name: str):
        row = self.db.query(WmRbacAction).filter(WmRbacAction.name == name).first()
        if not row:
            row = WmRbacAction(name=name)
            self.db.add(row)
            self.db.flush()
        return row
