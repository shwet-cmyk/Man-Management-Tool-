from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.modules.approval.schemas import (
    ApprovalActionRequest,
    ApprovalRuleRequest,
    ApprovalStepRequest,
    ApprovalSubmitRequest,
    ApprovalWorkflowCreateRequest,
)
from app.modules.approval.service import ApprovalService
from app.modules.rbac.schemas import RoleCreateRequest
from app.modules.rbac.service import RbacService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_sequential_and_parallel_approvals_complete_and_trigger_accounting():
    db = setup_db()
    rbac = RbacService(db)
    svc = ApprovalService(db)

    mgr_role = rbac.create_role(RoleCreateRequest(name="Manager", is_system_role=False))
    rbac.assign_user_role(2001, mgr_role["role_id"])

    wf = ApprovalWorkflowCreateRequest(
        module_name="VOUCHER",
        name="Voucher Approval",
        steps=[
            ApprovalStepRequest(step_order=1, approver_type="USER", approver_id=1001),
            ApprovalStepRequest(step_order=2, approver_type="ROLE", approver_id=mgr_role["role_id"], is_parallel=True),
            ApprovalStepRequest(step_order=2, approver_type="USER", approver_id=1002, is_parallel=True),
            ApprovalStepRequest(step_order=3, approver_type="USER", approver_id=3001),
        ],
        rules=[ApprovalRuleRequest(condition_type="AMOUNT", operator=">", value="10000")],
    )
    svc.create_workflow(wf)

    submit = svc.submit(ApprovalSubmitRequest(module_name="VOUCHER", entity_type="VOUCHER", entity_id=77, amount=50000, data={}))
    assert submit["status"] == "PENDING"
    assert submit["current_step"] == 1

    out1 = svc.action(ApprovalActionRequest(transaction_id=submit["transaction_id"], user_id=1001, action="APPROVE"))
    assert out1["current_step"] == 2

    out2 = svc.action(ApprovalActionRequest(transaction_id=submit["transaction_id"], user_id=1002, action="APPROVE"))
    assert out2["status"] == "PENDING"
    assert out2["current_step"] == 2

    out3 = svc.action(ApprovalActionRequest(transaction_id=submit["transaction_id"], user_id=2001, action="APPROVE"))
    assert out3["current_step"] == 3

    out4 = svc.action(ApprovalActionRequest(transaction_id=submit["transaction_id"], user_id=3001, action="APPROVE"))
    assert out4["status"] == "APPROVED"
    assert out4["accounting_triggered"] is True


def test_threshold_mismatch_auto_approves_without_steps():
    db = setup_db()
    svc = ApprovalService(db)
    svc.create_workflow(
        ApprovalWorkflowCreateRequest(
            module_name="DISCOUNT",
            name="Discount Approval",
            steps=[ApprovalStepRequest(step_order=1, approver_type="USER", approver_id=9901)],
            rules=[ApprovalRuleRequest(condition_type="AMOUNT", operator=">", value="20")],
        )
    )

    submit = svc.submit(ApprovalSubmitRequest(module_name="DISCOUNT", entity_type="DEAL", entity_id=991, amount=10, data={}))
    assert submit["status"] == "APPROVED"
    assert submit["accounting_triggered"] is True


def test_reject_stops_flow():
    db = setup_db()
    svc = ApprovalService(db)
    svc.create_workflow(
        ApprovalWorkflowCreateRequest(
            module_name="TASK",
            name="Task Close",
            steps=[ApprovalStepRequest(step_order=1, approver_type="USER", approver_id=7001)],
        )
    )

    submit = svc.submit(ApprovalSubmitRequest(module_name="TASK", entity_type="TASK", entity_id=11, amount=None, data={}))
    out = svc.action(ApprovalActionRequest(transaction_id=submit["transaction_id"], user_id=7001, action="REJECT", remarks="insufficient proof"))
    assert out["status"] == "REJECTED"
    assert out["accounting_triggered"] is False
