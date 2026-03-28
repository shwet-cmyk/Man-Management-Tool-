from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.models.wm_rbac_access_log import WmRbacAccessLog
from app.modules.rbac.schemas import (
    AccessCheckRequest,
    ApprovalCheckRequest,
    ApprovalLimitRequest,
    PermissionAssignRequest,
    PermissionScopeRequest,
    RoleCreateRequest,
)
from app.modules.rbac.service import RbacService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_rbac_role_permission_scope_and_access():
    db = setup_db()
    svc = RbacService(db)

    role = svc.create_role(RoleCreateRequest(name="Ops Manager", description="Operations", is_system_role=False))
    perm = svc.assign_permission(
        role["role_id"],
        PermissionAssignRequest(module_name="WORKFLOW", feature_name="TASK", action_name="APPROVE", is_allowed=True),
    )
    svc.assign_scope(perm["permission_id"], PermissionScopeRequest(company_id=1, branch_id=10, department_id=20))
    svc.assign_user_role(user_id=101, role_id=role["role_id"])

    allowed = svc.check_access(
        AccessCheckRequest(
            user_id=101,
            module_name="WORKFLOW",
            feature_name="TASK",
            action_name="APPROVE",
            company_id=1,
            branch_id=10,
            department_id=20,
        )
    )
    denied_scope = svc.check_access(
        AccessCheckRequest(
            user_id=101,
            module_name="WORKFLOW",
            feature_name="TASK",
            action_name="APPROVE",
            company_id=1,
            branch_id=11,
            department_id=20,
        )
    )

    assert allowed["allowed"] is True
    assert denied_scope["allowed"] is False


def test_rbac_deny_override_priority():
    db = setup_db()
    svc = RbacService(db)

    allow_role = svc.create_role(RoleCreateRequest(name="EditorAllow", is_system_role=False))
    deny_role = svc.create_role(RoleCreateRequest(name="EditorDeny", is_system_role=False))

    allow_perm = svc.assign_permission(
        allow_role["role_id"],
        PermissionAssignRequest(module_name="FINANCE", feature_name="INVOICE", action_name="EDIT", is_allowed=True),
    )
    deny_perm = svc.assign_permission(
        deny_role["role_id"],
        PermissionAssignRequest(module_name="FINANCE", feature_name="INVOICE", action_name="EDIT", is_allowed=False),
    )

    svc.assign_user_role(201, allow_role["role_id"])
    svc.assign_user_role(201, deny_role["role_id"])

    result = svc.check_access(
        AccessCheckRequest(user_id=201, module_name="FINANCE", feature_name="INVOICE", action_name="EDIT")
    )
    assert result["allowed"] is False

    # user override can allow this specific permission
    svc.add_user_override(user_id=201, permission_id=deny_perm["permission_id"], is_allowed=True)
    result2 = svc.check_access(
        AccessCheckRequest(user_id=201, module_name="FINANCE", feature_name="INVOICE", action_name="EDIT")
    )
    assert result2["allowed"] is True

    # keep variable used for lint friendliness in strict envs
    assert allow_perm["permission_id"] > 0


def test_rbac_access_checks_are_logged_and_approval_limits_enforced():
    db = setup_db()
    svc = RbacService(db)

    role = svc.create_role(RoleCreateRequest(name="Finance Approver", is_system_role=False))
    svc.assign_permission(
        role["role_id"],
        PermissionAssignRequest(module_name="FINANCE", feature_name="VOUCHER", action_name="APPROVE", is_allowed=True),
    )
    svc.assign_user_role(3001, role["role_id"])
    allowed = svc.check_access(AccessCheckRequest(user_id=3001, module_name="FINANCE", feature_name="VOUCHER", action_name="APPROVE", entity_id=99))
    assert allowed["allowed"] is True

    denied = svc.check_access(AccessCheckRequest(user_id=3002, module_name="FINANCE", feature_name="VOUCHER", action_name="APPROVE", entity_id=99))
    assert denied["allowed"] is False

    logs = db.query(WmRbacAccessLog).all()
    assert len(logs) == 2
    assert {x.user_id for x in logs} == {3001, 3002}

    svc.upsert_approval_limit(3001, payload=ApprovalLimitRequest(module_name="FINANCE", max_amount=100000))
    check_ok = svc.check_approval_limit(payload=ApprovalCheckRequest(user_id=3001, module_name="FINANCE", amount=100000))
    check_no = svc.check_approval_limit(payload=ApprovalCheckRequest(user_id=3001, module_name="FINANCE", amount=100001))
    assert check_ok["allowed"] is True
    assert check_no["allowed"] is False
