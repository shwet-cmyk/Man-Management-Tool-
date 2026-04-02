from __future__ import annotations

import json
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.wm_approval_log import WmApprovalLog
from app.models.wm_approval_rule import WmApprovalRule
from app.models.wm_approval_step import WmApprovalStep
from app.models.wm_approval_transaction import WmApprovalTransaction
from app.models.wm_approval_workflow import WmApprovalWorkflow
from app.models.wm_rbac_user_role import WmRbacUserRole
from app.modules.approval.schemas import ApprovalActionRequest, ApprovalSubmitRequest, ApprovalWorkflowCreateRequest


class ApprovalService:
    def __init__(self, db: Session):
        self.db = db

    def create_workflow(self, payload: ApprovalWorkflowCreateRequest):
        wf = WmApprovalWorkflow(module_name=payload.module_name, name=payload.name, is_active=payload.is_active)
        self.db.add(wf)
        self.db.flush()
        for step in payload.steps:
            self.db.add(
                WmApprovalStep(
                    approval_workflow_id=wf.approval_workflow_id,
                    step_order=step.step_order,
                    approver_type=step.approver_type.upper(),
                    approver_id=step.approver_id,
                    is_parallel=step.is_parallel,
                    dependency_step_id=step.dependency_step_id,
                    condition_json=json.dumps(step.condition),
                )
            )
        for rule in payload.rules:
            self.db.add(
                WmApprovalRule(
                    approval_workflow_id=wf.approval_workflow_id,
                    condition_type=rule.condition_type.upper(),
                    operator=rule.operator,
                    value=rule.value,
                    field_name=rule.field_name,
                )
            )
        self.db.commit()
        return {"workflow_id": wf.approval_workflow_id, "module_name": wf.module_name}

    def submit(self, payload: ApprovalSubmitRequest):
        wf = (
            self.db.query(WmApprovalWorkflow)
            .filter(WmApprovalWorkflow.module_name == payload.module_name, WmApprovalWorkflow.is_active.is_(True))
            .order_by(WmApprovalWorkflow.approval_workflow_id.desc())
            .first()
        )
        if not wf:
            raise HTTPException(status_code=404, detail="Approval workflow not found")

        steps = self.db.query(WmApprovalStep).filter(WmApprovalStep.approval_workflow_id == wf.approval_workflow_id).all()
        if not steps:
            raise HTTPException(status_code=422, detail="Approval workflow has no steps")
        rules = self.db.query(WmApprovalRule).filter(WmApprovalRule.approval_workflow_id == wf.approval_workflow_id).all()

        required = self._evaluate_rules(rules, payload.amount, payload.data)
        snapshot = {
            "workflow_id": wf.approval_workflow_id,
            "steps": [
                {
                    "approval_step_id": s.approval_step_id,
                    "step_order": int(s.step_order),
                    "approver_type": s.approver_type,
                    "approver_id": int(s.approver_id),
                    "is_parallel": bool(s.is_parallel),
                    "dependency_step_id": int(s.dependency_step_id) if s.dependency_step_id is not None else None,
                    "condition": json.loads(s.condition_json or "{}"),
                }
                for s in steps
            ],
            "rules": [
                {
                    "condition_type": r.condition_type,
                    "operator": r.operator,
                    "value": r.value,
                    "field_name": r.field_name,
                }
                for r in rules
            ],
        }

        txn = WmApprovalTransaction(
            entity_type=payload.entity_type,
            entity_id=payload.entity_id,
            approval_workflow_id=wf.approval_workflow_id,
            status="APPROVED" if not required else "PENDING",
            current_step=None if not required else min(x["step_order"] for x in snapshot["steps"]),
            snapshot_json=json.dumps(snapshot),
            accounting_triggered=not required,
            completed_on=datetime.utcnow() if not required else None,
        )
        self.db.add(txn)
        self.db.commit()
        self.db.refresh(txn)
        return {
            "transaction_id": txn.approval_transaction_id,
            "status": txn.status,
            "current_step": txn.current_step,
            "accounting_triggered": txn.accounting_triggered,
        }

    def action(self, payload: ApprovalActionRequest):
        txn = self.db.query(WmApprovalTransaction).filter(WmApprovalTransaction.approval_transaction_id == payload.transaction_id).first()
        if not txn:
            raise HTTPException(status_code=404, detail="Approval transaction not found")
        if txn.status != "PENDING":
            raise HTTPException(status_code=422, detail="Transaction is not pending")

        action = payload.action.upper()
        if action not in {"APPROVE", "REJECT"}:
            raise HTTPException(status_code=422, detail="Action must be APPROVE or REJECT")

        step = self._current_step_for_user(txn, payload.user_id)
        if not step:
            raise HTTPException(status_code=403, detail="User is not eligible for current approval step")

        self.db.add(
            WmApprovalLog(
                approval_transaction_id=txn.approval_transaction_id,
                approval_step_id=step["approval_step_id"],
                user_id=payload.user_id,
                action="APPROVED" if action == "APPROVE" else "REJECTED",
                remarks=payload.remarks,
            )
        )

        if action == "REJECT":
            txn.status = "REJECTED"
            txn.completed_on = datetime.utcnow()
            self.db.commit()
            return {"transaction_id": txn.approval_transaction_id, "status": txn.status, "accounting_triggered": False}

        self._advance_if_step_complete(txn)
        self.db.commit()
        return {
            "transaction_id": txn.approval_transaction_id,
            "status": txn.status,
            "current_step": txn.current_step,
            "accounting_triggered": txn.accounting_triggered,
        }

    def status_by_entity(self, entity_id: int):
        rows = (
            self.db.query(WmApprovalTransaction)
            .filter(WmApprovalTransaction.entity_id == entity_id)
            .order_by(WmApprovalTransaction.approval_transaction_id.desc())
            .all()
        )
        return [
            {
                "transaction_id": x.approval_transaction_id,
                "entity_id": x.entity_id,
                "status": x.status,
                "current_step": x.current_step,
                "accounting_triggered": x.accounting_triggered,
            }
            for x in rows
        ]

    def _evaluate_rules(self, rules: list[WmApprovalRule], amount: float | None, data: dict):
        if not rules:
            return True
        return any(self._evaluate_rule(x, amount, data) for x in rules)

    def _evaluate_rule(self, rule: WmApprovalRule, amount: float | None, data: dict):
        if rule.condition_type == "AMOUNT":
            left = amount
        elif rule.condition_type == "FIELD":
            left = data.get(rule.field_name or "")
        else:
            return False
        right: float | str
        try:
            right = float(rule.value)
        except ValueError:
            right = rule.value
        return self._compare(left, rule.operator, right)

    def _current_step_for_user(self, txn: WmApprovalTransaction, user_id: int):
        snapshot = json.loads(txn.snapshot_json)
        current_steps = [x for x in snapshot.get("steps", []) if x["step_order"] == txn.current_step]
        logs = self.db.query(WmApprovalLog).filter(WmApprovalLog.approval_transaction_id == txn.approval_transaction_id).all()
        acted_step_ids = {x.approval_step_id for x in logs}
        pending_steps = [x for x in current_steps if x["approval_step_id"] not in acted_step_ids]
        for step in pending_steps:
            if step["approver_type"] == "USER" and int(step["approver_id"]) == int(user_id):
                return step
            if step["approver_type"] == "ROLE":
                has_role = (
                    self.db.query(WmRbacUserRole)
                    .filter(WmRbacUserRole.user_id == user_id, WmRbacUserRole.role_id == int(step["approver_id"]))
                    .first()
                )
                if has_role:
                    return step
        return None

    def _advance_if_step_complete(self, txn: WmApprovalTransaction):
        snapshot = json.loads(txn.snapshot_json)
        steps = snapshot.get("steps", [])
        logs = self.db.query(WmApprovalLog).filter(WmApprovalLog.approval_transaction_id == txn.approval_transaction_id).all()
        approved_step_ids = {x.approval_step_id for x in logs if x.action == "APPROVED"}

        current_steps = [x for x in steps if x["step_order"] == txn.current_step]
        if not all(s["approval_step_id"] in approved_step_ids for s in current_steps):
            return

        next_orders = sorted({x["step_order"] for x in steps if x["step_order"] > txn.current_step})
        for order in next_orders:
            order_steps = [x for x in steps if x["step_order"] == order]
            deps_ok = True
            for st in order_steps:
                dep = st.get("dependency_step_id")
                if dep and dep not in approved_step_ids:
                    deps_ok = False
                    break
                if st.get("condition") and not self._evaluate_inline_condition(st["condition"], txn):
                    deps_ok = False
                    break
            if deps_ok:
                txn.current_step = order
                return

        txn.status = "APPROVED"
        txn.accounting_triggered = True
        txn.completed_on = datetime.utcnow()

    def _evaluate_inline_condition(self, condition: dict, txn: WmApprovalTransaction):
        if not condition:
            return True
        # snapshot-level contextual checks (ex: discount percent thresholds)
        if condition.get("field") == "entity_type":
            return self._compare(txn.entity_type, condition.get("operator", "="), condition.get("value"))
        return True

    @staticmethod
    def _compare(left, op: str, right):
        if op == "=":
            return left == right
        if op == "!=":
            return left != right
        if op == ">":
            return left is not None and left > right
        if op == "<":
            return left is not None and left < right
        if op == ">=":
            return left is not None and left >= right
        if op == "<=":
            return left is not None and left <= right
        return False
