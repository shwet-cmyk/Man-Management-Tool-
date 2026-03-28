from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ref_employee import RefEmployee
from app.models.wm_rbac_access_log import WmRbacAccessLog
from app.models.wm_rbac_action import WmRbacAction
from app.models.wm_rbac_approval_limit import WmRbacApprovalLimit
from app.models.wm_rbac_feature import WmRbacFeature
from app.models.wm_rbac_module import WmRbacModule
from app.models.wm_rbac_permission import WmRbacPermission
from app.models.wm_rbac_permission_node import WmRbacPermissionNode
from app.models.wm_rbac_permission_scope import WmRbacPermissionScope
from app.models.wm_rbac_role import WmRbacRole
from app.models.wm_rbac_role_inheritance import WmRbacRoleInheritance
from app.models.wm_rbac_user_access_profile import WmRbacUserAccessProfile
from app.models.wm_rbac_user_permission_override import WmRbacUserPermissionOverride
from app.models.wm_rbac_user_role import WmRbacUserRole
from app.models.wm_rbac_user_scope_map import WmRbacUserScopeMap
from app.modules.rbac.schemas import (
    AccessCheckRequest,
    ApprovalCheckRequest,
    ApprovalLimitRequest,
    EffectiveAccessRequest,
    PermissionAssignRequest,
    PermissionScopeRequest,
    RoleCreateRequest,
    RoleUpdateRequest,
    UserAccessProfileRequest,
    UserScopeMapRequest,
)


class RbacService:
    def __init__(self, db: Session):
        self.db = db

    # -------- role master --------
    def create_role(self, payload: RoleCreateRequest):
        role = WmRbacRole(role_id=self._next_id(WmRbacRole, WmRbacRole.role_id), name=payload.name, description=payload.description, is_system_role=payload.is_system_role)
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

    # -------- permission tree --------
    def seed_permission_tree(self):
        tree = self._tree_seed_rows()
        created = 0
        for row in tree:
            node = self.db.query(WmRbacPermissionNode).filter(WmRbacPermissionNode.permission_code == row["permission_code"]).first()
            if node:
                continue
            node_id = int((self.db.query(func.max(WmRbacPermissionNode.node_id)).scalar() or 0) + 1)
            self.db.add(WmRbacPermissionNode(node_id=node_id, **row))
            created += 1
        self.db.commit()
        return {"status": "success", "created": created}

    def permission_tree(self):
        rows = self.db.query(WmRbacPermissionNode).filter(WmRbacPermissionNode.active_flag.is_(True)).order_by(WmRbacPermissionNode.module_code.asc(), WmRbacPermissionNode.display_sequence.asc()).all()
        by_code = {x.permission_code: {"permission_code": x.permission_code, "permission_label": x.permission_label, "permission_type": x.permission_type, "is_sensitive": x.is_sensitive_flag, "children": []} for x in rows}
        modules: dict[str, dict] = {}
        for row in rows:
            if row.parent_permission_code and row.parent_permission_code in by_code:
                by_code[row.parent_permission_code]["children"].append(by_code[row.permission_code])
                continue
            if row.is_module_flag:
                modules[row.module_code] = {
                    "module_code": row.module_code,
                    "permission_code": row.permission_code,
                    "permission_label": row.permission_label,
                    "children": by_code[row.permission_code]["children"],
                }
        return {"status": "success", "rows": list(modules.values())}

    def seed_role_templates(self):
        names = [
            ("Admin", "Full enterprise access"),
            ("Manager", "Self and downline operations"),
            ("Employee", "Self-only operational access"),
            ("Finance", "Financial visibility and billing controls"),
            ("Support Executive", "Timesheet and support operations"),
            ("Customer Master Operator", "Customer master maintenance without sensitive ledger"),
            ("Billing User", "Invoice/proforma processing"),
        ]
        created = 0
        for name, desc in names:
            if self.db.query(WmRbacRole).filter(WmRbacRole.name == name).first():
                continue
            self.db.add(WmRbacRole(role_id=self._next_id(WmRbacRole, WmRbacRole.role_id), name=name, description=desc, is_system_role=True, is_active=True))
            created += 1
        self.db.commit()
        return {"status": "success", "created": created}

    # -------- role/permission mapping --------
    def assign_permission(self, role_id: int, payload: PermissionAssignRequest):
        role = self.db.query(WmRbacRole).filter(WmRbacRole.role_id == role_id, WmRbacRole.is_active.is_(True)).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        module = self._get_or_create_module(payload.module_name)
        feature = self._get_or_create_feature(module.module_id, payload.feature_name)
        action = self._get_or_create_action(payload.action_name)

        permission = self.db.query(WmRbacPermission).filter(WmRbacPermission.role_id == role_id, WmRbacPermission.feature_id == feature.feature_id, WmRbacPermission.action_id == action.action_id).first()
        if not permission:
            permission = WmRbacPermission(permission_id=self._next_id(WmRbacPermission, WmRbacPermission.permission_id), role_id=role_id, feature_id=feature.feature_id, action_id=action.action_id, is_allowed=payload.is_allowed)
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
            out.append({
                "permission_id": row.permission_id,
                "module_name": module.name if module else None,
                "feature_name": feature.name if feature else None,
                "action_name": action.name if action else None,
                "is_allowed": row.is_allowed,
                "scopes": [{"company_id": s.company_id, "branch_id": s.branch_id, "department_id": s.department_id} for s in scopes],
            })
        return out

    def assign_user_role(self, user_id: int, role_id: int):
        role = self.db.query(WmRbacRole).filter(WmRbacRole.role_id == role_id, WmRbacRole.is_active.is_(True)).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found or inactive")
        exists = self.db.query(WmRbacUserRole).filter(WmRbacUserRole.user_id == user_id, WmRbacUserRole.role_id == role_id).first()
        if exists:
            return {"status": "SUCCESS", "message": "Role already assigned", "user_id": user_id, "role_id": role_id}
        row = WmRbacUserRole(user_role_id=self._next_id(WmRbacUserRole, WmRbacUserRole.user_role_id), user_id=user_id, role_id=role_id)
        self.db.add(row)
        self.db.commit()
        return {"status": "SUCCESS", "user_id": user_id, "role_id": role_id}

    def assign_scope(self, permission_id: int, payload: PermissionScopeRequest):
        row = WmRbacPermissionScope(scope_id=self._next_id(WmRbacPermissionScope, WmRbacPermissionScope.scope_id), permission_id=permission_id, company_id=payload.company_id, branch_id=payload.branch_id, department_id=payload.department_id)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return {"scope_id": row.scope_id, "permission_id": permission_id}

    def add_role_inheritance(self, parent_role_id: int, child_role_id: int):
        row = WmRbacRoleInheritance(role_inheritance_id=self._next_id(WmRbacRoleInheritance, WmRbacRoleInheritance.role_inheritance_id), parent_role_id=parent_role_id, child_role_id=child_role_id)
        self.db.add(row)
        self.db.commit()
        return {"status": "SUCCESS", "parent_role_id": parent_role_id, "child_role_id": child_role_id}

    def add_user_override(self, user_id: int, permission_id: int, is_allowed: bool):
        row = self.db.query(WmRbacUserPermissionOverride).filter(WmRbacUserPermissionOverride.user_id == user_id, WmRbacUserPermissionOverride.permission_id == permission_id).first()
        if not row:
            row = WmRbacUserPermissionOverride(override_id=self._next_id(WmRbacUserPermissionOverride, WmRbacUserPermissionOverride.override_id), user_id=user_id, permission_id=permission_id, is_allowed=is_allowed)
        else:
            row.is_allowed = is_allowed
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
            out.append({"permission_id": row.permission_id, "module_name": module.name if module else None, "feature_name": feature.name if feature else None, "action_name": action.name if action else None, "is_allowed": row.is_allowed})
        return out

    # -------- user access setup + scopes --------
    def upsert_user_access_profile(self, user_id: int, payload: UserAccessProfileRequest):
        self._validate_access_profile(payload)
        row = self.db.query(WmRbacUserAccessProfile).filter(WmRbacUserAccessProfile.user_id == user_id).first()
        if not row:
            row = WmRbacUserAccessProfile(user_id=user_id, **payload.model_dump())
        else:
            for key, value in payload.model_dump().items():
                setattr(row, key, value)
            row.updated_on = datetime.utcnow()
        self.db.add(row)
        self.db.commit()
        return {"status": "success", "user_id": user_id}

    def set_user_scope(self, user_id: int, payload: UserScopeMapRequest):
        scope_type = payload.scope_type.upper()
        if scope_type not in {"COMPANY", "BRANCH", "DEPARTMENT"}:
            raise HTTPException(status_code=422, detail="scope_type must be COMPANY/BRANCH/DEPARTMENT")
        self.db.query(WmRbacUserScopeMap).filter(WmRbacUserScopeMap.user_id == user_id, WmRbacUserScopeMap.scope_type == scope_type).delete()
        for scope_id in sorted(set(payload.scope_ids)):
            next_id = int((self.db.query(func.max(WmRbacUserScopeMap.scope_map_id)).scalar() or 0) + 1)
            self.db.add(WmRbacUserScopeMap(scope_map_id=next_id, user_id=user_id, scope_type=scope_type, scope_id=scope_id))
        self.db.commit()
        return {"status": "success", "user_id": user_id, "scope_type": scope_type, "count": len(set(payload.scope_ids))}

    def get_user_scope(self, user_id: int):
        rows = self.db.query(WmRbacUserScopeMap).filter(WmRbacUserScopeMap.user_id == user_id).all()
        grouped = {"COMPANY": [], "BRANCH": [], "DEPARTMENT": []}
        for row in rows:
            grouped.setdefault(row.scope_type, []).append(int(row.scope_id))
        profile = self.db.query(WmRbacUserAccessProfile).filter(WmRbacUserAccessProfile.user_id == user_id).first()
        return {"user_id": user_id, "agent_level": profile.agent_level if profile else "SELF_ONLY", "scope": grouped}

    # -------- effective permission resolver --------
    def effective_permission(self, payload: EffectiveAccessRequest):
        feature = self.db.query(WmRbacFeature).join(WmRbacModule, WmRbacModule.module_id == WmRbacFeature.module_id).filter(WmRbacModule.name == payload.module_code, WmRbacFeature.name == payload.permission_code).first()
        action = self.db.query(WmRbacAction).filter(WmRbacAction.name == "ALLOW").first()
        if not feature or not action:
            return {"allowed": False, "reason": "Permission key not configured"}

        permission_rows = self._resolve_user_permission_rows(payload.user_id)
        matched = [x for x in permission_rows if x.feature_id == feature.feature_id and x.action_id == action.action_id]
        if not matched:
            return {"allowed": False, "reason": "No permission"}

        scoped = any(self._scope_match_for_user(payload.user_id, payload.company_id, payload.branch_id, payload.department_id) for _ in matched)
        if not scoped:
            return {"allowed": False, "reason": "Outside company/branch/department scope"}

        visibility_ok = self._visibility_match(payload)
        if not visibility_ok:
            return {"allowed": False, "reason": "Blocked by self/downline visibility mode"}

        if any(not x.is_allowed for x in matched):
            return {"allowed": False, "reason": "Denied by role/override"}
        return {"allowed": True, "reason": "Allowed", "scope_mode": self._profile_mode(payload.user_id)}

    def check_access(self, payload: AccessCheckRequest):
        feature = self.db.query(WmRbacFeature).join(WmRbacModule, WmRbacModule.module_id == WmRbacFeature.module_id).filter(WmRbacModule.name == payload.module_name, WmRbacFeature.name == payload.feature_name).first()
        action = self.db.query(WmRbacAction).filter(WmRbacAction.name == payload.action_name).first()
        if not feature or not action:
            return self._access_result(payload, False, "Permission key not configured")

        permission_rows = self._resolve_user_permission_rows(payload.user_id)
        matched = [x for x in permission_rows if x.feature_id == feature.feature_id and x.action_id == action.action_id]
        if not matched:
            return self._access_result(payload, False, "No permission")

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

        if not self._scope_match_for_user(payload.user_id, payload.company_id, payload.branch_id, payload.department_id):
            return self._access_result(payload, False, "Outside company/branch/department scope")
        if not self._visibility_match(EffectiveAccessRequest(user_id=payload.user_id, module_code=payload.module_name, permission_code=payload.feature_name, company_id=payload.company_id, branch_id=payload.branch_id, department_id=payload.department_id, creator_user_id=payload.creator_user_id, assignee_user_id=payload.assignee_user_id, manager_user_id=payload.manager_user_id)):
            return self._access_result(payload, False, "Blocked by self/downline visibility mode")

        return self._access_result(payload, True, "Allowed")

    # -------- approval controls --------
    def upsert_approval_limit(self, user_id: int, payload: ApprovalLimitRequest):
        row = self.db.query(WmRbacApprovalLimit).filter(WmRbacApprovalLimit.user_id == user_id, WmRbacApprovalLimit.module_name == payload.module_name).first()
        if not row:
            row = WmRbacApprovalLimit(approval_limit_id=self._next_id(WmRbacApprovalLimit, WmRbacApprovalLimit.approval_limit_id), user_id=user_id, module_name=payload.module_name, max_amount=payload.max_amount)
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
        return {"allowed": allowed, "reason": "Allowed" if allowed else "Amount exceeds approval limit", "configured_limit": float(row.max_amount)}

    # -------- reports --------
    def reports(self):
        users = self.db.query(WmRbacUserRole.user_id).distinct().all()
        rows = [u[0] for u in users]
        return {
            "user_rights_report": [{"user_id": u, "permissions": self.list_user_permissions(u)} for u in rows],
            "role_wise_permission_report": [{"role_id": r.role_id, "permissions": self.list_role_permissions(r.role_id)} for r in self.db.query(WmRbacRole).all()],
            "module_wise_permission_matrix": self.permission_tree()["rows"],
            "user_scope_report": [self.get_user_scope(u) for u in rows],
            "sensitive_permission_holders_report": self._sensitive_holders(),
            "users_with_export_rights_report": self._users_with_feature("DOWNLOAD_DATA_IN_EXCEL"),
            "users_with_approval_rights_report": self._users_with_feature("APPROVE"),
            "permission_change_audit_report": [{"user_id": x.user_id, "module": x.module_name, "feature": x.feature_name, "allowed": x.is_allowed, "reason": x.reason, "created_on": x.created_on} for x in self.db.query(WmRbacAccessLog).order_by(WmRbacAccessLog.access_log_id.desc()).limit(500).all()],
        }

    # -------- helpers --------

    @staticmethod
    def _match_scope(scope: WmRbacPermissionScope, payload: AccessCheckRequest):
        return (
            (scope.company_id is None or scope.company_id == payload.company_id)
            and (scope.branch_id is None or scope.branch_id == payload.branch_id)
            and (scope.department_id is None or scope.department_id == payload.department_id)
        )

    def _access_result(self, payload: AccessCheckRequest, allowed: bool, reason: str):
        self.db.add(WmRbacAccessLog(access_log_id=self._next_id(WmRbacAccessLog, WmRbacAccessLog.access_log_id), user_id=payload.user_id, module_name=payload.module_name, feature_name=payload.feature_name, action_name=payload.action_name, entity_id=payload.entity_id, is_allowed=allowed, reason=reason))
        self.db.commit()
        return {"allowed": allowed, "reason": reason}

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

    def _scope_match_for_user(self, user_id: int, company_id: int | None, branch_id: int | None, department_id: int | None):
        rows = self.db.query(WmRbacUserScopeMap).filter(WmRbacUserScopeMap.user_id == user_id).all()
        if not rows:
            return True
        allowed = {"COMPANY": set(), "BRANCH": set(), "DEPARTMENT": set()}
        for r in rows:
            allowed[r.scope_type].add(r.scope_id)
        if allowed["COMPANY"] and company_id and company_id not in allowed["COMPANY"]:
            return False
        if allowed["BRANCH"] and branch_id and branch_id not in allowed["BRANCH"]:
            return False
        if allowed["DEPARTMENT"] and department_id and department_id not in allowed["DEPARTMENT"]:
            return False
        return True

    def _visibility_match(self, payload: EffectiveAccessRequest) -> bool:
        mode = self._profile_mode(payload.user_id)
        if mode == "ALL":
            return True
        if mode == "SELF_ONLY":
            if not any([payload.creator_user_id, payload.assignee_user_id, payload.manager_user_id]):
                return True
            return payload.user_id in {payload.creator_user_id, payload.assignee_user_id}
        if mode == "SELF_AND_DOWNLINE":
            if not any([payload.creator_user_id, payload.assignee_user_id, payload.manager_user_id]):
                return True
            ids = {payload.user_id} | set(self._downline(payload.user_id))
            return any(x in ids for x in {payload.creator_user_id, payload.assignee_user_id, payload.manager_user_id} if x)
        return False

    def _profile_mode(self, user_id: int) -> str:
        row = self.db.query(WmRbacUserAccessProfile).filter(WmRbacUserAccessProfile.user_id == user_id).first()
        if not row:
            return "SELF_ONLY"
        if row.entries_of_all:
            return "ALL"
        if row.entries_of_self_and_downline:
            return "SELF_AND_DOWNLINE"
        return "SELF_ONLY"

    def _downline(self, user_id: int) -> list[int]:
        return [int(r.emp_id) for r in self.db.query(RefEmployee).filter(RefEmployee.manager_id == user_id, RefEmployee.is_active.is_(True)).all()]

    def _sensitive_holders(self):
        sensitive_codes = {x.permission_code for x in self.db.query(WmRbacPermissionNode).filter(WmRbacPermissionNode.is_sensitive_flag.is_(True)).all()}
        if not sensitive_codes:
            return []
        feature_ids = {x.feature_id for x in self.db.query(WmRbacFeature).filter(WmRbacFeature.name.in_(sensitive_codes)).all()}
        perms = self.db.query(WmRbacPermission).filter(WmRbacPermission.feature_id.in_(feature_ids), WmRbacPermission.is_allowed.is_(True)).all() if feature_ids else []
        role_map = {r.role_id: r.name for r in self.db.query(WmRbacRole).all()}
        return [{"role_id": p.role_id, "role_name": role_map.get(p.role_id), "feature_id": p.feature_id} for p in perms]

    def _users_with_feature(self, feature_code: str):
        feature = self.db.query(WmRbacFeature).filter(WmRbacFeature.name == feature_code).first()
        if not feature:
            return []
        role_ids = {p.role_id for p in self.db.query(WmRbacPermission).filter(WmRbacPermission.feature_id == feature.feature_id, WmRbacPermission.is_allowed.is_(True)).all()}
        return sorted({x.user_id for x in self.db.query(WmRbacUserRole).filter(WmRbacUserRole.role_id.in_(role_ids)).all()})

    def _validate_access_profile(self, payload: UserAccessProfileRequest):
        if payload.entries_of_self_and_downline and payload.agent_level == "SELF_ONLY":
            raise HTTPException(status_code=422, detail="Downline mode requires agent_level SELF_AND_DOWNLINE or ALL")
        if payload.entries_of_all and payload.entries_of_self_only:
            raise HTTPException(status_code=422, detail="Choose one visibility mode")

    def _get_or_create_module(self, name: str):
        row = self.db.query(WmRbacModule).filter(WmRbacModule.name == name).first()
        if not row:
            row = WmRbacModule(module_id=self._next_id(WmRbacModule, WmRbacModule.module_id), name=name)
            self.db.add(row)
            self.db.flush()
        return row

    def _get_or_create_feature(self, module_id: int, name: str):
        row = self.db.query(WmRbacFeature).filter(WmRbacFeature.module_id == module_id, WmRbacFeature.name == name).first()
        if not row:
            row = WmRbacFeature(feature_id=self._next_id(WmRbacFeature, WmRbacFeature.feature_id), module_id=module_id, name=name)
            self.db.add(row)
            self.db.flush()
        return row

    def _get_or_create_action(self, name: str):
        row = self.db.query(WmRbacAction).filter(WmRbacAction.name == name).first()
        if not row:
            row = WmRbacAction(action_id=self._next_id(WmRbacAction, WmRbacAction.action_id), name=name)
            self.db.add(row)
            self.db.flush()
        return row

    def _tree_seed_rows(self):
        def module(code: str, label: str, seq: int):
            return {
                "module_code": code,
                "permission_code": code,
                "permission_label": label,
                "parent_permission_code": None,
                "permission_type": "VIEW",
                "display_sequence": seq,
                "is_module_flag": True,
                "is_action_flag": False,
                "is_sensitive_flag": False,
                "active_flag": True,
            }

        def child(module_code: str, parent: str, code: str, label: str, seq: int, ptype: str = "WORKFLOW", sensitive: bool = False):
            return {
                "module_code": module_code,
                "permission_code": code,
                "permission_label": label,
                "parent_permission_code": parent,
                "permission_type": ptype,
                "display_sequence": seq,
                "is_module_flag": False,
                "is_action_flag": True,
                "is_sensitive_flag": sensitive,
                "active_flag": True,
            }

        rows = [
            module("JOBS", "Jobs", 1),
            module("TIMESHEET", "TimeSheet", 2),
            module("MASTER_CUSTOMER", "MasterCustomer", 3),
            module("MASTER_COMPANY", "MasterCompany", 4),
            module("MASTER_BRANCH", "MasterBranch", 5),
            module("MASTER_DEPARTMENT", "MasterDepartment", 6),
            module("MASTER_EMPLOYEE", "MasterEmployee", 7),
            module("API", "API", 8),
        ]

        api_permissions = [
            ("API_VIEW_DASHBOARD", "View Dashboard", "VIEW", False),
            ("API_APPLICATIONS", "API Applications", "VIEW", False),
            ("API_ADD_APPLICATION", "Add API Application", "CREATE", False),
            ("API_EDIT_APPLICATION", "Edit API Application", "EDIT", False),
            ("API_DISABLE_APPLICATION", "Disable API Application", "EDIT", True),
            ("API_REVOKE_APPLICATION", "Revoke API Application", "DELETE", True),
            ("API_KEYS", "API Keys", "VIEW", False),
            ("API_GENERATE_KEY", "Generate API Key", "CREATE", True),
            ("API_REGENERATE_KEY", "Regenerate API Key", "EDIT", True),
            ("API_REVOKE_KEY", "Revoke API Key", "DELETE", True),
            ("API_VIEW_KEY_USAGE", "View API Key Usage", "VIEW", False),
            ("API_SCOPES", "API Scopes", "VIEW", False),
            ("API_ASSIGN_SCOPES", "Assign API Scopes", "EDIT", True),
            ("API_EDIT_SCOPE_MAPPING", "Edit API Scope Mapping", "EDIT", True),
            ("API_ENDPOINT_REGISTRY", "Endpoint Registry", "VIEW", False),
            ("API_VIEW_ENDPOINT_REGISTRY", "View Endpoint Registry", "VIEW", False),
            ("API_EDIT_ENDPOINT_METADATA", "Edit Endpoint Registry Metadata", "EDIT", True),
            ("API_MARK_ENDPOINT_DEPRECATED", "Mark Endpoint Deprecated", "EDIT", True),
            ("API_WEBHOOKS", "Webhooks", "VIEW", False),
            ("API_ADD_WEBHOOK", "Add Webhook", "CREATE", False),
            ("API_EDIT_WEBHOOK", "Edit Webhook", "EDIT", False),
            ("API_PAUSE_WEBHOOK", "Pause Webhook", "EDIT", True),
            ("API_RESUME_WEBHOOK", "Resume Webhook", "EDIT", True),
            ("API_TEST_WEBHOOK", "Test Webhook", "WORKFLOW", True),
            ("API_RETRY_FAILED_WEBHOOK", "Retry Failed Webhook", "WORKFLOW", True),
            ("API_LOGS", "API Logs", "VIEW", False),
            ("API_VIEW_LOGS", "View API Logs", "VIEW", False),
            ("API_EXPORT_LOGS", "Export API Logs", "EXPORT", True),
            ("API_VIEW_FAILED_LOGS", "View Failed API Logs", "VIEW", False),
            ("API_USAGE_RATE_LIMITS", "Usage & Rate Limits", "VIEW", False),
            ("API_VIEW_USAGE_ANALYTICS", "View Usage Analytics", "VIEW", False),
            ("API_EDIT_RATE_LIMITS", "Edit Rate Limits", "EDIT", True),
            ("API_SETTINGS", "API Settings", "VIEW", False),
            ("API_VIEW_SETTINGS", "View API Settings", "VIEW", False),
            ("API_EDIT_SETTINGS", "Edit API Settings", "EDIT", True),
            ("API_DOCUMENTATION", "API Documentation", "VIEW", False),
            ("API_VIEW_DOCUMENTATION", "View API Documentation", "VIEW", False),
            ("API_EXPORT_DOCUMENTATION", "Export API Documentation", "EXPORT", False),
            ("API_TEST_CONSOLE", "API Test Console", "WORKFLOW", True),
            ("API_RUN_TEST_REQUEST", "Run Test API Request", "WORKFLOW", True),
            ("API_SENSITIVE_SCOPE_MGMT", "Sensitive Scope Management", "SECURITY", True),
            ("API_VIEW_AUTH_FAILURES", "View Auth Failures", "VIEW", True),
            ("API_VIEW_SECURITY_EVENTS", "View Security Events", "VIEW", True),
            ("API_ROTATE_SECRETS", "Rotate Secrets", "SECURITY", True),
            ("API_MANAGE_ENVIRONMENTS", "Manage Environments", "SECURITY", True),
        ]
        for i, (code, label, ptype, sensitive) in enumerate(api_permissions, start=200):
            rows.append(child("API", "API", code, label, i, ptype, sensitive))

        jobs = [
            ("JOBS_ADD_NEW_ENTRY", "Add new entry", "CREATE", False),
            ("JOBS_EDIT_ENTRY", "Edit entry", "EDIT", False),
            ("JOBS_DELETE_ENTRY", "Delete entry", "DELETE", False),
            ("JOBS_TIME_SHEET", "Time Sheet", "WORKFLOW", False),
            ("JOBS_ADD_TIME_SHEET", "Add Time Sheet", "CREATE", False),
            ("JOBS_MANUAL_VOUCHER_NO", "Manual Voucher No", "WORKFLOW", False),
            ("JOBS_MANUAL_DATE", "Manual Date", "WORKFLOW", False),
            ("JOBS_SEND_EMAIL", "Send Email", "COMMUNICATION", False),
            ("JOBS_ATTACH_DOCUMENT", "Attach Document", "COMMUNICATION", False),
            ("JOBS_PRINT_VOUCHER", "Print voucher", "PRINT", False),
            ("JOBS_REPORTS", "Reports", "VIEW", False),
            ("JOBS_CREATE_INVOICE", "Create Invoice", "WORKFLOW", True),
            ("JOBS_CREATE_PROFORMA", "Create Proforma", "WORKFLOW", True),
            ("JOBS_VIEW_AMOUNT", "View Amount", "FINANCIAL", True),
            ("JOBS_IMPORT_EXCEL", "Import Excel", "IMPORT_EXPORT", False),
            ("JOBS_ASSIGN_MULTIJOBS_TO_EMPLOYEE", "Assign MultiJobs To Employee", "BULK", False),
            ("JOBS_DOWNLOAD_DATA_IN_EXCEL", "Dowload data in Excel", "IMPORT_EXPORT", False),
        ]
        for i, (code, label, ptype, sensitive) in enumerate(jobs, start=10):
            rows.append(child("JOBS", "JOBS", code, label, i, ptype, sensitive))

        timesheet = [
            ("TIMESHEET_ADD_NEW_ENTRY", "Add new entry"),
            ("TIMESHEET_EDIT_ENTRY", "Edit entry"),
            ("TIMESHEET_DELETE_ENTRY", "Delete entry"),
            ("TIMESHEET_MANUAL_VOUCHER_NO", "Manual Voucher No"),
            ("TIMESHEET_MANUAL_DATE", "Manual Date"),
            ("TIMESHEET_SEND_EMAIL", "Send Email"),
            ("TIMESHEET_ATTACH_DOCUMENT", "Attach Document"),
            ("TIMESHEET_PRINT_VOUCHER", "Print voucher"),
            ("TIMESHEET_REPORTS", "Reports"),
            ("TIMESHEET_DOWNLOAD_DATA_IN_EXCEL", "Dowload data in Excel"),
        ]
        for i, (code, label) in enumerate(timesheet, start=40):
            rows.append(child("TIMESHEET", "TIMESHEET", code, label, i, "WORKFLOW", False))

        customer = [
            ("MC_ADD_NEW_ENTRY", "Add new entry", False),
            ("MC_EDIT_ENTRY", "Edit entry", False),
            ("MC_ADDITIONAL_BILL_TO_ADDRESS", "Additional Bill To Address", False),
            ("MC_ADD_ADDITIONAL_BILL_TO_ADDRESS", "Add Additional Bill To Address", False),
            ("MC_EDIT_ADDITIONAL_BILL_TO_ADDRESS", "Edit Additional Bill To Address", False),
            ("MC_DELETE_ADDITIONAL_BILL_TO_ADDRESS", "Delete Additional Bill To Address", False),
            ("MC_DELETE_ENTRY", "Delete entry", False),
            ("MC_ARCHIVE_ENTRY", "Archive entry", False),
            ("MC_SEND_SMS", "Send SMS", False),
            ("MC_SERVICES", "Services", False),
            ("MC_SEND_EMAIL", "Send Email", False),
            ("MC_SERVICE_RATE", "ServiceRate", True),
            ("MC_DOWNLOAD_DATA_IN_EXCEL", "Dowload data in Excel", False),
            ("MC_LEDGER", "Ledger", True),
            ("MC_MULTI_COLUMN_REPORT", "Multi Column Report", False),
            ("MC_REPORTS", "Reports", False),
            ("MC_UPLOAD_BULK_DATA", "Upload bulk data", False),
            ("MC_PRICE_LIST", "Price List", True),
            ("MC_UPLOAD_PRICE_LIST", "Upload Price List", True),
            ("MC_DISCOUNT_LIST", "Discount List", True),
            ("MC_UPLOAD_DISCOUNT_LIST", "Upload Discount List", True),
            ("MC_CONFIRMATION_LEDGER_EMAIL", "ConfirmationLedgerEmail", True),
            ("MC_MASTER_CUSTOMER_REMARK_LIST", "MasterCustomerRemarkList", False),
        ]
        for i, (code, label, sensitive) in enumerate(customer, start=70):
            rows.append(child("MASTER_CUSTOMER", "MASTER_CUSTOMER", code, label, i, "FINANCIAL" if sensitive else "WORKFLOW", sensitive))

        common_master_children = [
            ("ADD_NEW_ENTRY", "Add new entry"),
            ("EDIT_ENTRY", "Edit entry"),
            ("DELETE_ENTRY", "Delete entry"),
            ("ARCHIVE_ENTRY", "Archive entry"),
            ("DOWNLOAD_DATA_IN_EXCEL", "Dowload data in Excel"),
        ]
        for mod, prefix, base in [("MASTER_COMPANY", "MCOMP", 110), ("MASTER_BRANCH", "MBR", 120), ("MASTER_DEPARTMENT", "MDEP", 130), ("MASTER_EMPLOYEE", "MEMP", 140)]:
            for idx, (suffix, label) in enumerate(common_master_children):
                rows.append(child(mod, mod, f"{prefix}_{suffix}", label, base + idx, "WORKFLOW", False))

        employee_sensitive = [
            ("MEMP_VIEW_SALARY", "View Salary", True),
            ("MEMP_EDIT_SALARY", "Edit Salary", True),
            ("MEMP_VIEW_SHIFT", "View Shift", False),
            ("MEMP_EDIT_SHIFT", "Edit Shift", False),
            ("MEMP_VIEW_MANAGER_MAPPING", "View Manager Mapping", False),
            ("MEMP_EDIT_MANAGER_MAPPING", "Edit Manager Mapping", False),
            ("MEMP_VIEW_HOLIDAY_MAPPING", "View Holiday Mapping", False),
            ("MEMP_EDIT_HOLIDAY_MAPPING", "Edit Holiday Mapping", False),
        ]
        for i, (code, label, sensitive) in enumerate(employee_sensitive, start=150):
            rows.append(child("MASTER_EMPLOYEE", "MASTER_EMPLOYEE", code, label, i, "FINANCIAL" if sensitive else "WORKFLOW", sensitive))
        return rows


    def _next_id(self, model, col):
        return int((self.db.query(func.max(col)).scalar() or 0) + 1)
