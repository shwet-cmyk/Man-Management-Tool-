from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models.wm_rule import WmRule
from app.models.wm_rule_execution_log import WmRuleExecutionLog
from app.modules.rules.schemas import RuleCreateRequest, RuleEvaluateRequest


class RuleService:
    def __init__(self, db: Session):
        self.db = db

    def create_rule(self, payload: RuleCreateRequest):
        row = WmRule(
            module=payload.module,
            condition_json=json.dumps(payload.condition),
            action_json=json.dumps(payload.action),
            priority=payload.priority,
        )
        self.db.add(row)
        self.db.commit()
        return {"rule_id": row.rule_id}

    def evaluate(self, payload: RuleEvaluateRequest):
        rules = (
            self.db.query(WmRule)
            .filter(WmRule.module == payload.module, WmRule.status == "ACTIVE")
            .order_by(WmRule.priority.asc(), WmRule.rule_id.asc())
            .all()
        )
        results = []
        for rule in rules:
            cond = json.loads(rule.condition_json)
            matched = self._evaluate_condition(cond, payload.context)
            action = json.loads(rule.action_json) if matched else None
            results.append({"rule_id": rule.rule_id, "matched": matched, "action": action})
            self.db.add(
                WmRuleExecutionLog(
                    rule_id=rule.rule_id,
                    module=payload.module,
                    matched="YES" if matched else "NO",
                    context_json=json.dumps(payload.context),
                    result_json=json.dumps(action) if action else None,
                )
            )
        self.db.commit()
        return {"results": results}

    def _evaluate_condition(self, condition: dict, context: dict):
        if "rules" in condition:
            logic = str(condition.get("logic", "AND")).upper()
            vals = [self._evaluate_condition(x, context) for x in condition.get("rules", [])]
            return all(vals) if logic == "AND" else any(vals)
        field = condition.get("field")
        op = condition.get("operator", "=")
        value = condition.get("value")
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
