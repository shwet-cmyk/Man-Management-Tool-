from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.wm_business_holiday import WmBusinessHoliday
from app.models.wm_rbac_user_role import WmRbacUserRole
from app.models.wm_sla_escalation import WmSlaEscalation
from app.models.wm_sla_instance import WmSlaInstance
from app.models.wm_sla_policy import WmSlaPolicy
from app.modules.sla.schemas import (
    HolidayCreateRequest,
    SlaEscalateRequest,
    SlaRuleCreateRequest,
    SlaStartRequest,
)


class SlaService:
    WORK_START_HOUR = 9
    WORK_END_HOUR = 18

    def __init__(self, db: Session):
        self.db = db

    def create_rule(self, payload: SlaRuleCreateRequest):
        multiplier = 60 if payload.unit.lower().startswith("hour") else 1
        row = WmSlaPolicy(
            module=payload.module,
            condition_json=json.dumps(payload.condition),
            response_time_minutes=payload.response_time * multiplier,
            resolution_time_minutes=payload.resolution_time * multiplier,
            escalation_config_json=json.dumps(payload.escalation_config),
            company_id=payload.company_id,
            branch_id=payload.branch_id,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return {"sla_policy_id": row.sla_policy_id}

    def add_holiday(self, payload: HolidayCreateRequest):
        row = WmBusinessHoliday(holiday_date=date.fromisoformat(payload.holiday_date), name=payload.name, company_id=payload.company_id, branch_id=payload.branch_id)
        self.db.add(row)
        self.db.commit()
        return {"holiday_id": row.holiday_id}

    def start_sla(self, payload: SlaStartRequest):
        rule = self._find_rule(payload.module, payload.company_id, payload.branch_id, payload.context)
        if not rule:
            raise HTTPException(status_code=404, detail="No SLA rule configured for module/context")
        start = datetime.utcnow()
        due = self._add_business_minutes(start, int(rule.resolution_time_minutes), payload.company_id, payload.branch_id)
        row = WmSlaInstance(
            sla_policy_id=rule.sla_policy_id,
            entity_type=payload.entity_type,
            entity_id=payload.entity_id,
            assignee_user_id=payload.assignee_user_id,
            status="RUNNING",
            start_time=start,
            due_time=due,
            timezone="UTC",
            context_json=json.dumps(payload.context),
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return {"sla_instance_id": row.sla_instance_id, "due_time": row.due_time}

    def get_status(self, entity_type: str, entity_id: int):
        rows = self.db.query(WmSlaInstance).filter(WmSlaInstance.entity_type == entity_type, WmSlaInstance.entity_id == entity_id).all()
        return [
            {
                "sla_instance_id": x.sla_instance_id,
                "status": x.status,
                "start_time": x.start_time,
                "due_time": x.due_time,
                "breach_time": x.breach_time,
            }
            for x in rows
        ]

    def pause(self, sla_instance_id: int):
        row = self._get_instance(sla_instance_id)
        if row.status != "RUNNING":
            raise HTTPException(status_code=422, detail="Only running SLA can be paused")
        row.status = "PAUSED"
        row.paused_on = datetime.utcnow()
        self.db.commit()
        return {"status": row.status}

    def resume(self, sla_instance_id: int):
        row = self._get_instance(sla_instance_id)
        if row.status != "PAUSED" or not row.paused_on:
            raise HTTPException(status_code=422, detail="Only paused SLA can be resumed")
        paused_sec = int((datetime.utcnow() - row.paused_on).total_seconds())
        row.total_pause_seconds += paused_sec
        row.due_time = row.due_time + timedelta(seconds=paused_sec)
        row.paused_on = None
        row.status = "RUNNING"
        self.db.commit()
        return {"status": row.status, "due_time": row.due_time}

    def check_and_escalate(self):
        now = datetime.utcnow()
        rows = self.db.query(WmSlaInstance).filter(WmSlaInstance.status == "RUNNING", WmSlaInstance.due_time <= now).all()
        total = 0
        for row in rows:
            row.status = "BREACHED"
            row.breach_time = now
            self._run_escalation(row)
            total += 1
        self.db.commit()
        return {"breached": total}

    def escalate(self, payload: SlaEscalateRequest):
        row = self._get_instance(payload.sla_instance_id)
        self._run_escalation(row)
        self.db.commit()
        return {"status": "ESCALATED", "sla_instance_id": row.sla_instance_id}

    def _run_escalation(self, row: WmSlaInstance):
        policy = self.db.query(WmSlaPolicy).filter(WmSlaPolicy.sla_policy_id == row.sla_policy_id).first()
        cfg = json.loads(policy.escalation_config_json or "{}")
        levels = cfg.get("levels", [])
        channels = cfg.get("notify", ["IN_APP"])

        level_no = 0
        for lvl in levels:
            level_no += 1
            target = int(lvl.get("user_id", 0))
            if target <= 0:
                continue
            # RBAC guard: escalated user must have at least one role assigned
            has_role = self.db.query(WmRbacUserRole).filter(WmRbacUserRole.user_id == target).first() is not None
            if not has_role:
                continue
            for ch in channels:
                self.db.add(WmSlaEscalation(sla_instance_id=row.sla_instance_id, escalation_level=level_no, escalated_to=target, channel=ch.upper()))
        row.status = "ESCALATED"

    def _find_rule(self, module: str, company_id: int | None, branch_id: int | None, context: dict):
        q = self.db.query(WmSlaPolicy).filter(WmSlaPolicy.module == module)
        if company_id is not None:
            q = q.filter((WmSlaPolicy.company_id == company_id) | (WmSlaPolicy.company_id.is_(None)))
        if branch_id is not None:
            q = q.filter((WmSlaPolicy.branch_id == branch_id) | (WmSlaPolicy.branch_id.is_(None)))
        for row in q.order_by(WmSlaPolicy.sla_policy_id.desc()).all():
            cond = json.loads(row.condition_json or "{}")
            if self._match(cond, context):
                return row
        return None

    def _match(self, cond: dict, ctx: dict):
        if not cond:
            return True
        for k, v in cond.items():
            if ctx.get(k) != v:
                return False
        return True

    def _is_business_time(self, dt: datetime, company_id: int | None, branch_id: int | None):
        if dt.weekday() >= 5:
            return False
        holiday = self.db.query(WmBusinessHoliday).filter(WmBusinessHoliday.holiday_date == dt.date(), (WmBusinessHoliday.company_id == company_id) | (WmBusinessHoliday.company_id.is_(None)), (WmBusinessHoliday.branch_id == branch_id) | (WmBusinessHoliday.branch_id.is_(None))).first()
        if holiday:
            return False
        return time(self.WORK_START_HOUR, 0) <= dt.time() < time(self.WORK_END_HOUR, 0)

    def _add_business_minutes(self, start: datetime, minutes: int, company_id: int | None, branch_id: int | None):
        current = start
        left = minutes
        while left > 0:
            current += timedelta(minutes=1)
            if self._is_business_time(current, company_id, branch_id):
                left -= 1
        return current

    def _get_instance(self, sla_instance_id: int):
        row = self.db.query(WmSlaInstance).filter(WmSlaInstance.sla_instance_id == sla_instance_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="SLA instance not found")
        return row
