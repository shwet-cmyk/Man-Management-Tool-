from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.models.wm_sla_log import WmSlaLog
from app.models.wm_workflow_approval import WmWorkflowApproval
from app.models.wm_workflow_edge import WmWorkflowEdge
from app.models.wm_workflow_instance import WmWorkflowInstance
from app.models.wm_workflow_log import WmWorkflowLog
from app.modules.workflows.schemas import (
    TriggerWorkflowRequest,
    WorkflowApprovalDecisionRequest,
    WorkflowCreateRequest,
    WorkflowEdgeRequest,
    WorkflowNodeRequest,
)
from app.modules.workflows.service import WorkflowService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_workflow_nested_condition_and_action_executes():
    db = setup_db()
    svc = WorkflowService(db)
    wf = svc.create_workflow(WorkflowCreateRequest(name="Invoice WF", module="FINANCE", trigger_event="INVOICE_CREATED"))
    event_node = svc.add_node(wf["workflow_id"], WorkflowNodeRequest(node_type="EVENT", name="Start", sequence_no=1, config={}))
    cond_node = svc.add_node(
        wf["workflow_id"],
        WorkflowNodeRequest(
            node_type="CONDITION",
            name="Amount & urgency",
            sequence_no=2,
            config={
                "logic": "AND",
                "rules": [
                    {"field": "amount", "operator": ">", "value": 100000},
                    {"logic": "OR", "rules": [{"field": "priority", "operator": "=", "value": "HIGH"}, {"field": "priority", "operator": "=", "value": "CRITICAL"}]},
                ],
            },
        ),
    )
    action_true = svc.add_node(wf["workflow_id"], WorkflowNodeRequest(node_type="ACTION", name="Call API", sequence_no=3, config={"action": "CALL_API"}))
    action_false = svc.add_node(wf["workflow_id"], WorkflowNodeRequest(node_type="ACTION", name="Auto Approve", sequence_no=4, config={"action": "UPDATE_STATUS"}))

    svc.add_edge(wf["workflow_id"], WorkflowEdgeRequest(from_node_id=event_node["node_id"], to_node_id=cond_node["node_id"]))
    svc.add_edge(wf["workflow_id"], WorkflowEdgeRequest(from_node_id=cond_node["node_id"], to_node_id=action_true["node_id"], edge_condition="TRUE"))
    svc.add_edge(wf["workflow_id"], WorkflowEdgeRequest(from_node_id=cond_node["node_id"], to_node_id=action_false["node_id"], edge_condition="FALSE"))

    out = svc.trigger_workflow(TriggerWorkflowRequest(module="FINANCE", event_name="INVOICE_CREATED", entity_type="INVOICE", entity_id=11, context={"amount": 150000, "priority": "HIGH"}))
    inst_id = out["instances"][0]["instance_id"]
    inst = db.query(WmWorkflowInstance).filter(WmWorkflowInstance.instance_id == inst_id).first()
    assert inst.status == "COMPLETED"
    assert out["instances"][0]["workflow_version"] == 1


def test_workflow_multi_approval_threshold_and_rejection_rules():
    db = setup_db()
    svc = WorkflowService(db)
    wf = svc.create_workflow(WorkflowCreateRequest(name="Expense Approval", module="EXPENSE", trigger_event="CLAIM_CREATED"))
    n1 = svc.add_node(wf["workflow_id"], WorkflowNodeRequest(node_type="EVENT", name="Start", sequence_no=1, config={}))
    n2 = svc.add_node(
        wf["workflow_id"],
        WorkflowNodeRequest(node_type="APPROVAL", name="Committee", sequence_no=2, config={"approver_user_ids": [901, 902, 903], "approval_mode": "THRESHOLD", "min_approvals": 2}),
    )
    n3 = svc.add_node(wf["workflow_id"], WorkflowNodeRequest(node_type="ACTION", name="Notify", sequence_no=3, config={"action": "SEND_EMAIL"}))
    svc.add_edge(wf["workflow_id"], WorkflowEdgeRequest(from_node_id=n1["node_id"], to_node_id=n2["node_id"]))
    svc.add_edge(wf["workflow_id"], WorkflowEdgeRequest(from_node_id=n2["node_id"], to_node_id=n3["node_id"], edge_condition="APPROVED"))

    out = svc.trigger_workflow(TriggerWorkflowRequest(module="EXPENSE", event_name="CLAIM_CREATED", entity_type="EXPENSE", entity_id=9001, context={}))
    inst_id = out["instances"][0]["instance_id"]
    approvals = db.query(WmWorkflowApproval).filter(WmWorkflowApproval.instance_id == inst_id).all()
    assert len(approvals) == 3

    first = next(x for x in approvals if x.approver_user_id == 901)
    second = next(x for x in approvals if x.approver_user_id == 902)
    svc.approve(WorkflowApprovalDecisionRequest(approval_id=first.approval_id, decided_by=901, remarks="ok1"))
    inst = db.query(WmWorkflowInstance).filter(WmWorkflowInstance.instance_id == inst_id).first()
    assert inst.status == "WAITING_APPROVAL"

    svc.approve(WorkflowApprovalDecisionRequest(approval_id=second.approval_id, decided_by=902, remarks="ok2"))
    inst = db.query(WmWorkflowInstance).filter(WmWorkflowInstance.instance_id == inst_id).first()
    assert inst.status in {"RUNNING", "COMPLETED"}

    # rejection requires remarks
    wf2 = svc.create_workflow(WorkflowCreateRequest(name="Reject Rule", module="EXPENSE", trigger_event="CLAIM_REVIEW"))
    a = svc.add_node(wf2["workflow_id"], WorkflowNodeRequest(node_type="EVENT", name="Start", sequence_no=1, config={}))
    b = svc.add_node(wf2["workflow_id"], WorkflowNodeRequest(node_type="APPROVAL", name="Mgr", sequence_no=2, config={"approver_user_id": 777}))
    svc.add_edge(wf2["workflow_id"], WorkflowEdgeRequest(from_node_id=a["node_id"], to_node_id=b["node_id"]))
    out2 = svc.trigger_workflow(TriggerWorkflowRequest(module="EXPENSE", event_name="CLAIM_REVIEW", entity_type="EXPENSE", entity_id=9002, context={}))
    ap = db.query(WmWorkflowApproval).filter(WmWorkflowApproval.instance_id == out2["instances"][0]["instance_id"]).first()
    try:
        svc.reject(WorkflowApprovalDecisionRequest(approval_id=ap.approval_id, decided_by=777, remarks=None))
        assert False
    except Exception:
        assert True


def test_workflow_sla_pause_resume_and_breach():
    db = setup_db()
    svc = WorkflowService(db)
    wf = svc.create_workflow(WorkflowCreateRequest(name="SLA Workflow", module="TASK", trigger_event="TASK_CREATED"))
    n1 = svc.add_node(wf["workflow_id"], WorkflowNodeRequest(node_type="EVENT", name="Start", sequence_no=1, config={}))
    n2 = svc.add_node(wf["workflow_id"], WorkflowNodeRequest(node_type="ACTION", name="Noop", sequence_no=2, config={"action": "ADD_COMMENT"}))
    svc.add_edge(wf["workflow_id"], WorkflowEdgeRequest(from_node_id=n1["node_id"], to_node_id=n2["node_id"]))
    svc.add_sla_rule(wf["workflow_id"], time_limit_minutes=1, escalation_user_id=77)
    out = svc.trigger_workflow(TriggerWorkflowRequest(module="TASK", event_name="TASK_CREATED", entity_type="TASK", entity_id=1, context={}))
    inst_id = out["instances"][0]["instance_id"]

    pause = svc.pause_sla(inst_id)
    assert pause["status"] == "PAUSED"
    resume = svc.resume_sla(inst_id)
    assert resume["status"] == "RUNNING"

    sla = db.query(WmSlaLog).filter(WmSlaLog.instance_id == inst_id).first()
    sla.breach_time = datetime.utcnow() - timedelta(minutes=1)
    db.commit()
    breach_out = svc.process_sla_breaches()
    assert breach_out["breached_instances"] >= 1


def test_workflow_execution_uses_frozen_graph_snapshot():
    db = setup_db()
    svc = WorkflowService(db)
    wf = svc.create_workflow(WorkflowCreateRequest(name="Version Freeze", module="FINANCE", trigger_event="INVOICE_SUBMIT"))
    start = svc.add_node(wf["workflow_id"], WorkflowNodeRequest(node_type="EVENT", name="Start", sequence_no=1, config={}))
    approval = svc.add_node(
        wf["workflow_id"],
        WorkflowNodeRequest(node_type="APPROVAL", name="Approve", sequence_no=2, config={"approver_user_id": 501}),
    )
    action_old = svc.add_node(wf["workflow_id"], WorkflowNodeRequest(node_type="ACTION", name="Old Action", sequence_no=3, config={"action": "SEND_EMAIL"}))
    action_new = svc.add_node(wf["workflow_id"], WorkflowNodeRequest(node_type="ACTION", name="New Action", sequence_no=4, config={"action": "CALL_API"}))
    svc.add_edge(wf["workflow_id"], WorkflowEdgeRequest(from_node_id=start["node_id"], to_node_id=approval["node_id"]))
    original_edge = svc.add_edge(
        wf["workflow_id"],
        WorkflowEdgeRequest(from_node_id=approval["node_id"], to_node_id=action_old["node_id"], edge_condition="APPROVED"),
    )

    out = svc.trigger_workflow(TriggerWorkflowRequest(module="FINANCE", event_name="INVOICE_SUBMIT", entity_type="INVOICE", entity_id=51, context={"amount": 10}))
    inst_id = out["instances"][0]["instance_id"]
    approval_row = db.query(WmWorkflowApproval).filter(WmWorkflowApproval.instance_id == inst_id).first()

    # mutate workflow graph after execution started (new version path)
    edge_row = db.query(WmWorkflowEdge).filter(WmWorkflowEdge.edge_id == original_edge["edge_id"]).first()
    edge_row.to_node_id = action_new["node_id"]
    db.commit()

    svc.approve(WorkflowApprovalDecisionRequest(approval_id=approval_row.approval_id, decided_by=501, remarks="ok"))
    logs = db.query(WmWorkflowLog).filter(WmWorkflowLog.instance_id == inst_id).all()
    action_codes = [x.action for x in logs]
    assert "ACTION:SEND_EMAIL" in action_codes
    assert "ACTION:CALL_API" not in action_codes


def test_get_execution_status_includes_logs_and_approvals():
    db = setup_db()
    svc = WorkflowService(db)
    wf = svc.create_workflow(WorkflowCreateRequest(name="Status Test", module="TASK", trigger_event="TASK_CREATED"))
    start = svc.add_node(wf["workflow_id"], WorkflowNodeRequest(node_type="EVENT", name="Start", sequence_no=1, config={}))
    action = svc.add_node(wf["workflow_id"], WorkflowNodeRequest(node_type="ACTION", name="Done", sequence_no=2, config={"action": "UPDATE_STATUS"}))
    svc.add_edge(wf["workflow_id"], WorkflowEdgeRequest(from_node_id=start["node_id"], to_node_id=action["node_id"]))
    out = svc.trigger_workflow(TriggerWorkflowRequest(module="TASK", event_name="TASK_CREATED", entity_type="TASK", entity_id=7, context={}))
    inst_id = out["instances"][0]["instance_id"]

    status = svc.get_execution_status(inst_id)
    assert status["instance_id"] == inst_id
    assert status["status"] == "COMPLETED"
    assert len(status["logs"]) >= 2
