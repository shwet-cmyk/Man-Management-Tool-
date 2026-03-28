from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.wm_sla_log import WmSlaLog
from app.models.wm_sla_rule import WmSlaRule
from app.models.wm_webhook_log import WmWebhookLog
from app.models.wm_workflow import WmWorkflow
from app.models.wm_workflow_approval import WmWorkflowApproval
from app.models.wm_workflow_edge import WmWorkflowEdge
from app.models.wm_workflow_instance import WmWorkflowInstance
from app.models.wm_workflow_log import WmWorkflowLog
from app.models.wm_workflow_node import WmWorkflowNode
from app.modules.workflows.schemas import (
    TriggerWorkflowRequest,
    WorkflowApprovalDecisionRequest,
    WorkflowCreateRequest,
    WorkflowEdgeRequest,
    WorkflowNodeRequest,
    WorkflowUpdateRequest,
)


class WorkflowService:
    def __init__(self, db: Session):
        self.db = db

    def create_workflow(self, payload: WorkflowCreateRequest):
        row = WmWorkflow(name=payload.name, module=payload.module, trigger_event=payload.trigger_event, is_active=payload.is_active)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return {"workflow_id": row.workflow_id, "name": row.name}

    def list_workflows(self):
        rows = self.db.query(WmWorkflow).order_by(WmWorkflow.workflow_id.asc()).all()
        return [{"workflow_id": x.workflow_id, "name": x.name, "module": x.module, "trigger_event": x.trigger_event, "is_active": x.is_active, "version": x.version} for x in rows]

    def update_workflow(self, workflow_id: int, payload: WorkflowUpdateRequest):
        row = self.db.query(WmWorkflow).filter(WmWorkflow.workflow_id == workflow_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Workflow not found")
        if payload.name is not None:
            row.name = payload.name
        if payload.module is not None:
            row.module = payload.module
        if payload.trigger_event is not None:
            row.trigger_event = payload.trigger_event
        if payload.is_active is not None:
            row.is_active = payload.is_active
        row.version += 1
        self.db.commit()
        return {"workflow_id": row.workflow_id, "version": row.version}

    def delete_workflow(self, workflow_id: int):
        row = self.db.query(WmWorkflow).filter(WmWorkflow.workflow_id == workflow_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Workflow not found")
        row.is_active = False
        row.version += 1
        self.db.commit()
        return {"status": "SUCCESS", "workflow_id": workflow_id}

    def add_node(self, workflow_id: int, payload: WorkflowNodeRequest):
        row = WmWorkflowNode(workflow_id=workflow_id, node_type=payload.node_type.upper(), name=payload.name, sequence_no=payload.sequence_no, config_json=json.dumps(payload.config))
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return {"node_id": row.node_id}

    def add_edge(self, workflow_id: int, payload: WorkflowEdgeRequest):
        row = WmWorkflowEdge(workflow_id=workflow_id, from_node_id=payload.from_node_id, to_node_id=payload.to_node_id, edge_condition=payload.edge_condition)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return {"edge_id": row.edge_id}

    def add_sla_rule(self, workflow_id: int, time_limit_minutes: int, escalation_user_id: int):
        row = WmSlaRule(workflow_id=workflow_id, time_limit_minutes=time_limit_minutes, escalation_user_id=escalation_user_id)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return {"sla_rule_id": row.sla_rule_id}

    def trigger_workflow(self, payload: TriggerWorkflowRequest):
        workflows = self.db.query(WmWorkflow).filter(WmWorkflow.module == payload.module, WmWorkflow.trigger_event == payload.event_name, WmWorkflow.is_active.is_(True)).all()
        if not workflows:
            return {"instances": [], "message": "No matching workflow"}

        results = []
        for wf in workflows:
            graph_snapshot = self._build_graph_snapshot(wf.workflow_id)
            instance = WmWorkflowInstance(
                workflow_id=wf.workflow_id,
                workflow_version=wf.version,
                entity_type=payload.entity_type,
                entity_id=payload.entity_id,
                status="RUNNING",
                context_json=json.dumps({"runtime_context": payload.context, "workflow_graph": graph_snapshot}),
            )
            self.db.add(instance)
            self.db.flush()

            sla = self.db.query(WmSlaRule).filter(WmSlaRule.workflow_id == wf.workflow_id).first()
            if sla:
                self.db.add(WmSlaLog(instance_id=instance.instance_id, start_time=datetime.utcnow(), breach_time=datetime.utcnow() + timedelta(minutes=int(sla.time_limit_minutes)), status="RUNNING"))

            start_node = self._get_start_node_from_snapshot(graph_snapshot) or self._get_start_node(wf.workflow_id)
            self._log(instance.instance_id, start_node.node_id if start_node else None, "TRIGGER", "SUCCESS", "Workflow triggered")
            self._execute_from_node(instance, start_node, payload.context, hop_limit=100)
            results.append({"workflow_id": wf.workflow_id, "workflow_version": wf.version, "instance_id": instance.instance_id})

        self.db.commit()
        return {"instances": results}

    def approve(self, payload: WorkflowApprovalDecisionRequest):
        approval = self.db.query(WmWorkflowApproval).filter(WmWorkflowApproval.approval_id == payload.approval_id).first()
        if not approval:
            raise HTTPException(status_code=404, detail="Approval not found")
        if approval.approver_user_id != payload.decided_by:
            raise HTTPException(status_code=403, detail="Only assigned approver can approve")
        if approval.status != "PENDING":
            raise HTTPException(status_code=422, detail="Approval already decided")

        approval.status = "APPROVED"
        approval.remarks = payload.remarks
        approval.decided_on = datetime.utcnow()

        instance = self.db.query(WmWorkflowInstance).filter(WmWorkflowInstance.instance_id == approval.instance_id).first()
        node = self.db.query(WmWorkflowNode).filter(WmWorkflowNode.node_id == approval.node_id).first()
        graph = self._get_graph_snapshot(instance)
        node_snapshot = self._get_snapshot_node(graph, approval.node_id)
        cfg = node_snapshot.get("config", {}) if node_snapshot else json.loads(node.config_json or "{}")
        mode = str(cfg.get("approval_mode", "ALL")).upper()
        min_approvals = int(cfg.get("min_approvals", 1))
        same_node = self.db.query(WmWorkflowApproval).filter(WmWorkflowApproval.instance_id == approval.instance_id, WmWorkflowApproval.node_id == approval.node_id).all()
        approved_count = len([x for x in same_node if x.status == "APPROVED"])
        pending = [x for x in same_node if x.status == "PENDING"]

        should_continue = False
        if mode == "ANY" and approved_count >= 1:
            should_continue = True
        elif approved_count >= min_approvals and approved_count >= 1 and (mode == "THRESHOLD" or not pending):
            should_continue = True
        elif mode == "ALL" and not pending:
            should_continue = True

        if should_continue:
            for p in pending:
                p.status = "SKIPPED"
            instance.status = "RUNNING"
            self._log(instance.instance_id, approval.node_id, "APPROVE", "SUCCESS", payload.remarks)
            next_node = self._next_node(instance, approval.node_id, "APPROVED")
            self._execute_from_node(instance, next_node, self._get_runtime_context(instance), hop_limit=100)
        else:
            self._log(instance.instance_id, approval.node_id, "APPROVE_PARTIAL", "PENDING", f"approved={approved_count}")

        self.db.commit()
        return {"status": "SUCCESS", "approval_id": approval.approval_id}

    def reject(self, payload: WorkflowApprovalDecisionRequest):
        if not payload.remarks:
            raise HTTPException(status_code=422, detail="Rejection remarks required")
        approval = self.db.query(WmWorkflowApproval).filter(WmWorkflowApproval.approval_id == payload.approval_id).first()
        if not approval:
            raise HTTPException(status_code=404, detail="Approval not found")
        if approval.approver_user_id != payload.decided_by:
            raise HTTPException(status_code=403, detail="Only assigned approver can reject")
        approval.status = "REJECTED"
        approval.remarks = payload.remarks
        approval.decided_on = datetime.utcnow()

        instance = self.db.query(WmWorkflowInstance).filter(WmWorkflowInstance.instance_id == approval.instance_id).first()
        instance.status = "REJECTED"
        instance.completed_on = datetime.utcnow()
        others = self.db.query(WmWorkflowApproval).filter(WmWorkflowApproval.instance_id == approval.instance_id, WmWorkflowApproval.node_id == approval.node_id, WmWorkflowApproval.status == "PENDING").all()
        for row in others:
            row.status = "CANCELLED"
        self._log(instance.instance_id, approval.node_id, "REJECT", "SUCCESS", payload.remarks)
        self.db.commit()
        return {"status": "SUCCESS", "approval_id": approval.approval_id}

    def pause_sla(self, instance_id: int):
        row = self.db.query(WmSlaLog).filter(WmSlaLog.instance_id == instance_id, WmSlaLog.status == "RUNNING").first()
        if not row:
            raise HTTPException(status_code=404, detail="Active SLA not found")
        row.status = "PAUSED"
        row.paused_on = datetime.utcnow()
        self.db.commit()
        return {"status": "PAUSED", "instance_id": instance_id}

    def resume_sla(self, instance_id: int):
        row = self.db.query(WmSlaLog).filter(WmSlaLog.instance_id == instance_id, WmSlaLog.status == "PAUSED").first()
        if not row or not row.paused_on:
            raise HTTPException(status_code=404, detail="Paused SLA not found")
        paused_seconds = int((datetime.utcnow() - row.paused_on).total_seconds())
        row.total_pause_seconds += paused_seconds
        row.breach_time = row.breach_time + timedelta(seconds=paused_seconds)
        row.paused_on = None
        row.status = "RUNNING"
        self.db.commit()
        return {"status": "RUNNING", "instance_id": instance_id}

    def process_sla_breaches(self):
        now = datetime.utcnow()
        breached = self.db.query(WmSlaLog).filter(WmSlaLog.status == "RUNNING", WmSlaLog.breach_time <= now).all()
        count = 0
        for row in breached:
            row.status = "BREACHED"
            instance = self.db.query(WmWorkflowInstance).filter(WmWorkflowInstance.instance_id == row.instance_id).first()
            instance.status = "ESCALATED"
            self._log(instance.instance_id, None, "SLA_BREACH", "ESCALATED", "SLA breached and escalated")
            count += 1
        self.db.commit()
        return {"breached_instances": count}

    def get_execution_status(self, instance_id: int):
        instance = self.db.query(WmWorkflowInstance).filter(WmWorkflowInstance.instance_id == instance_id).first()
        if not instance:
            raise HTTPException(status_code=404, detail="Workflow execution not found")
        approvals = self.db.query(WmWorkflowApproval).filter(WmWorkflowApproval.instance_id == instance_id).all()
        logs = self.db.query(WmWorkflowLog).filter(WmWorkflowLog.instance_id == instance_id).order_by(WmWorkflowLog.workflow_log_id.asc()).all()
        return {
            "instance_id": instance.instance_id,
            "workflow_id": instance.workflow_id,
            "workflow_version": instance.workflow_version,
            "entity_type": instance.entity_type,
            "entity_id": instance.entity_id,
            "status": instance.status,
            "created_on": instance.created_on,
            "completed_on": instance.completed_on,
            "approvals": [
                {
                    "approval_id": x.approval_id,
                    "node_id": x.node_id,
                    "approver_user_id": x.approver_user_id,
                    "status": x.status,
                    "remarks": x.remarks,
                }
                for x in approvals
            ],
            "logs": [
                {
                    "workflow_log_id": x.workflow_log_id,
                    "node_id": x.node_id,
                    "action": x.action,
                    "status": x.status,
                    "remarks": x.remarks,
                    "created_on": x.created_on,
                }
                for x in logs
            ],
        }

    def _execute_from_node(self, instance: WmWorkflowInstance, node: WmWorkflowNode | None, context: dict, hop_limit: int):
        hops = 0
        current = node
        while current and hops < hop_limit:
            hops += 1
            cfg = json.loads(current.config_json or "{}")

            if current.node_type == "EVENT":
                self._log(instance.instance_id, current.node_id, "EVENT", "SUCCESS", current.name)
                current = self._next_node(instance, current.node_id, None)
                continue

            if current.node_type == "CONDITION":
                decision = self._evaluate_condition(cfg, context)
                self._log(instance.instance_id, current.node_id, "CONDITION", "SUCCESS", f"result={decision}")
                current = self._next_node(instance, current.node_id, "TRUE" if decision else "FALSE")
                continue

            if current.node_type == "ACTION":
                action_code = str(cfg.get("action", "UNKNOWN")).upper()
                self._perform_action(action_code, instance, current, cfg, context)
                current = self._next_node(instance, current.node_id, None)
                continue

            if current.node_type == "APPROVAL":
                self._create_approvals(instance, current, cfg)
                instance.status = "WAITING_APPROVAL"
                self._log(instance.instance_id, current.node_id, "APPROVAL_REQUEST", "PENDING", json.dumps(cfg))
                return

            if current.node_type == "DELAY":
                self._log(instance.instance_id, current.node_id, "DELAY", "SUCCESS", json.dumps(cfg))
                current = self._next_node(instance, current.node_id, None)
                continue

            self._log(instance.instance_id, current.node_id, "UNKNOWN_NODE", "FAILED", current.node_type)
            break

        if hops >= hop_limit:
            instance.status = "FAILED"
            self._log(instance.instance_id, current.node_id if current else None, "LOOP_GUARD", "FAILED", "Workflow hop limit exceeded")
        elif instance.status == "RUNNING":
            instance.status = "COMPLETED"
            instance.completed_on = datetime.utcnow()
            self._log(instance.instance_id, None, "WORKFLOW_COMPLETE", "SUCCESS", "Completed")

    def _create_approvals(self, instance: WmWorkflowInstance, node: WmWorkflowNode, cfg: dict):
        approver_list = cfg.get("approver_user_ids") or ([] if cfg.get("approver_user_id") is None else [cfg.get("approver_user_id")])
        if not approver_list:
            raise HTTPException(status_code=422, detail="Approval node requires approver_user_ids or approver_user_id")
        decision_group = str(uuid.uuid4())
        for user_id in approver_list:
            self.db.add(WmWorkflowApproval(instance_id=instance.instance_id, node_id=node.node_id, approver_user_id=int(user_id), status="PENDING", decision_group=decision_group))

    def _perform_action(self, action_code: str, instance: WmWorkflowInstance, node: WmWorkflowNode, cfg: dict, context: dict):
        if action_code in {"SEND_EMAIL", "SEND_WHATSAPP", "CREATE_TASK", "UPDATE_STATUS", "ADD_COMMENT", "ATTACH_DOCUMENT"}:
            self._log(instance.instance_id, node.node_id, f"ACTION:{action_code}", "SUCCESS", json.dumps(cfg))
            return
        if action_code in {"CALL_API", "CALL_WEBHOOK"}:
            self.db.add(WmWebhookLog(webhook_id=0, event_name=f"WORKFLOW_{action_code}", payload=json.dumps({"instance_id": instance.instance_id, "node_id": node.node_id, "cfg": cfg, "context": context}, default=str), status="QUEUED"))
            self._log(instance.instance_id, node.node_id, f"ACTION:{action_code}", "QUEUED", json.dumps(cfg))
            return
        self._log(instance.instance_id, node.node_id, f"ACTION:{action_code}", "SKIPPED", "Unknown action")

    def _get_start_node(self, workflow_id: int):
        return self.db.query(WmWorkflowNode).filter(WmWorkflowNode.workflow_id == workflow_id).order_by(WmWorkflowNode.sequence_no.asc(), WmWorkflowNode.node_id.asc()).first()

    def _next_node(self, instance: WmWorkflowInstance, node_id: int, branch_condition: str | None):
        graph = self._get_graph_snapshot(instance)
        if graph:
            edges = [x for x in graph.get("edges", []) if int(x.get("from_node_id", -1)) == int(node_id)]
            if not edges:
                return None
            chosen = None
            if branch_condition:
                chosen = next((x for x in edges if str(x.get("edge_condition") or "").upper() == branch_condition.upper()), None)
            if not chosen:
                chosen = next((x for x in edges if not x.get("edge_condition")), edges[0])
            target = int(chosen.get("to_node_id"))
            node = self._get_snapshot_node(graph, target)
            if node:
                return WmWorkflowNode(
                    node_id=int(node["node_id"]),
                    workflow_id=int(node["workflow_id"]),
                    node_type=str(node["node_type"]),
                    name=str(node["name"]),
                    sequence_no=int(node["sequence_no"]),
                    config_json=json.dumps(node.get("config", {})),
                )

        edges = self.db.query(WmWorkflowEdge).filter(WmWorkflowEdge.workflow_id == instance.workflow_id, WmWorkflowEdge.from_node_id == node_id).all()
        if not edges:
            return None
        chosen = None
        if branch_condition:
            chosen = next((x for x in edges if (x.edge_condition or "").upper() == branch_condition.upper()), None)
        if not chosen:
            chosen = next((x for x in edges if not x.edge_condition), edges[0])
        return self.db.query(WmWorkflowNode).filter(WmWorkflowNode.node_id == chosen.to_node_id).first()

    def _build_graph_snapshot(self, workflow_id: int):
        nodes = self.db.query(WmWorkflowNode).filter(WmWorkflowNode.workflow_id == workflow_id).all()
        edges = self.db.query(WmWorkflowEdge).filter(WmWorkflowEdge.workflow_id == workflow_id).all()
        return {
            "workflow_id": workflow_id,
            "nodes": [
                {
                    "node_id": int(n.node_id),
                    "workflow_id": int(n.workflow_id),
                    "node_type": n.node_type,
                    "name": n.name,
                    "sequence_no": int(n.sequence_no),
                    "config": json.loads(n.config_json or "{}"),
                }
                for n in nodes
            ],
            "edges": [
                {
                    "edge_id": int(e.edge_id),
                    "from_node_id": int(e.from_node_id),
                    "to_node_id": int(e.to_node_id),
                    "edge_condition": e.edge_condition,
                }
                for e in edges
            ],
        }

    def _get_graph_snapshot(self, instance: WmWorkflowInstance):
        payload = json.loads(instance.context_json or "{}")
        graph = payload.get("workflow_graph")
        return graph if isinstance(graph, dict) else None

    def _get_runtime_context(self, instance: WmWorkflowInstance):
        payload = json.loads(instance.context_json or "{}")
        runtime_context = payload.get("runtime_context")
        if isinstance(runtime_context, dict):
            return runtime_context
        if isinstance(payload, dict):
            return payload
        return {}

    def _get_snapshot_node(self, graph: dict | None, node_id: int):
        if not graph:
            return None
        return next((n for n in graph.get("nodes", []) if int(n.get("node_id", -1)) == int(node_id)), None)

    def _get_start_node_from_snapshot(self, graph: dict | None):
        if not graph:
            return None
        nodes = graph.get("nodes", [])
        if not nodes:
            return None
        start = sorted(nodes, key=lambda n: (int(n.get("sequence_no", 1)), int(n.get("node_id", 0))))[0]
        return WmWorkflowNode(
            node_id=int(start["node_id"]),
            workflow_id=int(start["workflow_id"]),
            node_type=str(start["node_type"]),
            name=str(start["name"]),
            sequence_no=int(start["sequence_no"]),
            config_json=json.dumps(start.get("config", {})),
        )

    def _evaluate_condition(self, cfg: dict, context: dict):
        if "rules" in cfg:
            logic = str(cfg.get("logic", "AND")).upper()
            vals = [self._evaluate_condition(rule, context) for rule in cfg.get("rules", [])]
            return all(vals) if logic == "AND" else any(vals)
        field = cfg.get("field")
        op = cfg.get("operator", "=")
        value = cfg.get("value")
        left = context.get(field)
        if op == "=":
            return left == value
        if op == "!=":
            return left != value
        if op == ">":
            return left is not None and left > value
        if op == "<":
            return left is not None and left < value
        if op == ">=":
            return left is not None and left >= value
        if op == "<=":
            return left is not None and left <= value
        return False

    def _log(self, instance_id: int, node_id: int | None, action: str, status: str, remarks: str | None):
        self.db.add(WmWorkflowLog(instance_id=instance_id, node_id=node_id, action=action, status=status, remarks=remarks))
