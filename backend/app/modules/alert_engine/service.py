from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ref_employee import RefEmployee
from app.models.wm_alert_log import WmAlertLog
from app.models.wm_alert_recipient_matrix import WmAlertRecipientMatrix
from app.models.wm_alert_setting import WmAlertSetting
from app.models.wm_alert_template import WmAlertTemplate
from app.models.wm_job import WmJob
from app.models.wm_man_approval import WmManApproval
from app.models.wm_task import WmTask
from app.models.wm_timesheet import WmTimesheet
from app.modules.alert_engine.schemas import (
    AlertRecipientMatrixRequest,
    AlertSettingRequest,
    AlertTemplateRequest,
    MarkReadRequest,
    ScheduledRunRequest,
    TriggerEventRequest,
)


class SmsService:
    def send(self, recipient: int | None, subject: str | None, body: str) -> tuple[str, str | None]:
        return "Sent", None


class EmailService:
    def send(self, recipient: int | None, subject: str | None, body: str) -> tuple[str, str | None]:
        return "Sent", None


class InAppNotificationService:
    def send(self, recipient: int | None, subject: str | None, body: str) -> tuple[str, str | None]:
        return "Sent", None


class RecipientMatrixService:
    def __init__(self, db: Session):
        self.db = db

    def upsert_matrix(self, payload: AlertRecipientMatrixRequest) -> dict:
        row = self.db.query(WmAlertRecipientMatrix).filter(
            WmAlertRecipientMatrix.event_code == payload.event_code,
            WmAlertRecipientMatrix.entity_type == payload.entity_type,
            WmAlertRecipientMatrix.recipient_role == payload.recipient_role,
            WmAlertRecipientMatrix.escalation_stage == payload.escalation_stage,
        ).first()
        if not row:
            matrix_id = int((self.db.query(func.max(WmAlertRecipientMatrix.matrix_id)).scalar() or 0) + 1)
            row = WmAlertRecipientMatrix(matrix_id=matrix_id, **payload.model_dump())
            self.db.add(row)
        else:
            for key, value in payload.model_dump().items():
                setattr(row, key, value)
            row.updated_at = datetime.utcnow()
        self.db.commit()
        return {"status": "success", "matrix_id": row.matrix_id}

    def resolve_roles(self, event_code: str, entity_type: str, payload: dict, escalation_stage: int = 1) -> list[dict]:
        rows = self.db.query(WmAlertRecipientMatrix).filter(
            WmAlertRecipientMatrix.event_code == event_code,
            WmAlertRecipientMatrix.entity_type == entity_type,
            WmAlertRecipientMatrix.escalation_stage <= escalation_stage,
            WmAlertRecipientMatrix.include_flag.is_(True),
            WmAlertRecipientMatrix.active_flag.is_(True),
        ).order_by(WmAlertRecipientMatrix.escalation_stage.asc(), WmAlertRecipientMatrix.sequence_no.asc()).all()

        if not rows:
            return [{"recipient_role": "Assigned Employee", "hide_downline_flag": False, "suppression_rule_id": None}]

        priority = str(payload.get("priority", "")).upper()
        resolved = []
        for row in rows:
            if row.priority_filter and row.priority_filter.upper() != priority:
                continue
            resolved.append({
                "recipient_role": row.recipient_role,
                "hide_downline_flag": bool(row.hide_downline_flag),
                "suppression_rule_id": row.suppression_rule_id,
            })
        return resolved

    def seed_default_matrix(self) -> dict:
        defaults = [
            ("task_created", "task", "Assigned Employee", 1, 1, False),
            ("task_created", "task", "Manager", 2, 1, False),
            ("task_assigned", "task", "Assigned Employee", 1, 1, False),
            ("task_assigned", "task", "Manager", 2, 1, False),
            ("task_overdue", "task", "Assigned Employee", 1, 1, False),
            ("task_overdue", "task", "Manager", 2, 2, False),
            ("task_overdue", "task", "Department Head", 3, 3, True),
            ("task_completed", "task", "Task Creator", 1, 1, False),
            ("task_completed", "task", "Manager", 2, 1, False),
            ("job_awaiting_acceptance", "job", "Assigned Employee", 1, 1, False),
            ("job_awaiting_acceptance", "job", "Manager", 2, 2, False),
            ("job_transfer_rejected", "job", "Manager", 1, 1, False),
            ("job_transfer_rejected", "job", "Task Owner", 2, 1, False),
            ("pending_approval_reminder", "approval", "Approver", 1, 1, False),
            ("pending_approval_reminder", "approval", "Reporting Manager", 2, 2, True),
            ("rollover_critical", "job", "Manager", 1, 1, False),
            ("rollover_critical", "job", "Leadership", 2, 2, False),
            ("billing_blocked", "job", "Task Owner", 1, 1, False),
            ("billing_blocked", "job", "Finance", 2, 1, False),
            ("junior_pending_approval", "approval", "Reporting Manager", 1, 1, True),
            ("daily_manager_digest", "manager", "Manager", 1, 1, False),
        ]
        created = 0
        for event_code, entity_type, role, seq, stage, hide in defaults:
            exists = self.db.query(WmAlertRecipientMatrix).filter(
                WmAlertRecipientMatrix.event_code == event_code,
                WmAlertRecipientMatrix.entity_type == entity_type,
                WmAlertRecipientMatrix.recipient_role == role,
                WmAlertRecipientMatrix.escalation_stage == stage,
            ).first()
            if exists:
                continue
            matrix_id = int((self.db.query(func.max(WmAlertRecipientMatrix.matrix_id)).scalar() or 0) + 1)
            self.db.add(WmAlertRecipientMatrix(matrix_id=matrix_id, event_code=event_code, entity_type=entity_type, recipient_role=role, sequence_no=seq, escalation_stage=stage, include_flag=True, hide_downline_flag=hide, active_flag=True))
            created += 1
        self.db.commit()
        return {"status": "success", "created": created}


class TemplateService:
    def __init__(self, db: Session):
        self.db = db

    def upsert_template(self, payload: AlertTemplateRequest) -> dict:
        row = self.db.query(WmAlertTemplate).filter(WmAlertTemplate.template_code == payload.template_code, WmAlertTemplate.channel_type == payload.channel_type, WmAlertTemplate.recipient_role_variant == payload.recipient_role_variant).first()
        if not row:
            template_id = int((self.db.query(func.max(WmAlertTemplate.template_id)).scalar() or 0) + 1)
            row = WmAlertTemplate(template_id=template_id, **payload.model_dump())
            self.db.add(row)
        else:
            for key, value in payload.model_dump().items():
                if key == "created_by":
                    continue
                setattr(row, key, value)
            row.updated_at = datetime.utcnow()
        self.db.commit()
        return {"status": "success", "template_id": row.template_id}

    def seed_templates(self, user_id: int = 1) -> dict:
        templates = self._default_templates(user_id)
        created = 0
        for payload in templates:
            exists = self.db.query(WmAlertTemplate).filter(
                WmAlertTemplate.template_code == payload["template_code"],
                WmAlertTemplate.channel_type == payload["channel_type"],
                WmAlertTemplate.recipient_role_variant == payload.get("recipient_role_variant"),
                WmAlertTemplate.language_code == payload.get("language_code", "en"),
            ).first()
            if exists:
                continue
            template_id = int((self.db.query(func.max(WmAlertTemplate.template_id)).scalar() or 0) + 1)
            self.db.add(WmAlertTemplate(template_id=template_id, **payload))
            created += 1
        self.db.commit()
        return {"status": "success", "created": created}

    def render(self, template_id: int | None, payload: dict, channel_type: str, recipient_role: str) -> tuple[str | None, str]:
        row = None
        if template_id is not None:
            row = self.db.query(WmAlertTemplate).filter(
                WmAlertTemplate.template_id == template_id,
                WmAlertTemplate.enabled_flag.is_(True),
                WmAlertTemplate.active_flag.is_(True),
            ).first()
        if row is None:
            row = self.db.query(WmAlertTemplate).filter(
                WmAlertTemplate.template_code == payload.get("trigger_event"),
                WmAlertTemplate.channel_type == channel_type,
                WmAlertTemplate.recipient_role_variant == recipient_role,
                WmAlertTemplate.enabled_flag.is_(True),
                WmAlertTemplate.active_flag.is_(True),
            ).first()
        if row is None:
            row = self.db.query(WmAlertTemplate).filter(
                WmAlertTemplate.template_code == payload.get("trigger_event"),
                WmAlertTemplate.channel_type == channel_type,
                WmAlertTemplate.recipient_role_variant.is_(None),
                WmAlertTemplate.enabled_flag.is_(True),
                WmAlertTemplate.active_flag.is_(True),
            ).first()

        if row is None:
            subject = f"{payload.get('trigger_event', 'Alert')} · {payload.get('priority', 'Info')}"
            body = f"{payload.get('entity_type', 'Entity')} update requires attention for {payload.get('task_no') or payload.get('job_no') or payload.get('approval_id') or payload.get('entity_id')}"
            return subject, self._fit_channel(body, channel_type)

        rendered_subject = self._apply(row.subject_template, payload) if row.subject_template else None
        rendered_body = self._apply(row.body_template, payload)
        return rendered_subject, self._fit_channel(rendered_body, channel_type)

    def _apply(self, template: str | None, payload: dict) -> str:
        if not template:
            return ""
        out = template
        for key, val in payload.items():
            out = out.replace(f"{{{key}}}", str(val if val is not None else "-"))
        return out

    def _fit_channel(self, body: str, channel_type: str) -> str:
        if channel_type == "SMS":
            return (body[:157] + "...") if len(body) > 160 else body
        if channel_type == "In-App":
            return (body[:197] + "...") if len(body) > 200 else body
        return body

    def _default_templates(self, user_id: int) -> list[dict]:
        return [
            {"template_code": "task_created", "template_name": "Task Created", "category": "Task Events", "channel_type": "Email", "recipient_role_variant": "Assigned Employee", "subject_template": "Task {task_no} created · {priority}", "body_template": "Task {task_no} ({task_name}) has been created for {client_name}. Due: {due_date}. Action: review scope and start execution.", "enabled_flag": True, "language_code": "en", "version_no": 1, "active_flag": True, "created_by": user_id},
            {"template_code": "task_assigned", "template_name": "Task Assigned", "category": "Task Events", "channel_type": "SMS", "recipient_role_variant": "Assigned Employee", "subject_template": None, "body_template": "Task {task_no} assigned to you. Due {due_date}. Update status today.", "enabled_flag": True, "language_code": "en", "version_no": 1, "active_flag": True, "created_by": user_id},
            {"template_code": "task_overdue", "template_name": "Task Overdue - Assignee", "category": "SLA / Delay Events", "channel_type": "In-App", "recipient_role_variant": "Assigned Employee", "subject_template": None, "body_template": "Task {task_no} is overdue by {pending_days} day(s). Action now.", "enabled_flag": True, "language_code": "en", "version_no": 1, "active_flag": True, "created_by": user_id},
            {"template_code": "task_overdue", "template_name": "Task Overdue - Manager", "category": "SLA / Delay Events", "channel_type": "Email", "recipient_role_variant": "Manager", "subject_template": "Overdue task escalation · {task_no}", "body_template": "Task {task_no} for {employee_name} is overdue by {pending_days} day(s). Current status: {status}. Manager action required.", "enabled_flag": True, "language_code": "en", "version_no": 1, "active_flag": True, "created_by": user_id},
            {"template_code": "task_completed", "template_name": "Task Completed", "category": "Task Events", "channel_type": "Email", "recipient_role_variant": "Task Creator", "subject_template": "Task completed · {task_no}", "body_template": "Task {task_no} has been completed by {employee_name}. Review closure and billing readiness.", "enabled_flag": True, "language_code": "en", "version_no": 1, "active_flag": True, "created_by": user_id},
            {"template_code": "job_awaiting_acceptance", "template_name": "Job Awaiting Acceptance", "category": "Dependency / Transfer Events", "channel_type": "Email", "recipient_role_variant": "Assigned Employee", "subject_template": "Action required: accept transfer for {job_no}", "body_template": "Job {job_no} for {client_name} is awaiting your acceptance. Due date: {due_date}. Accept or reject with remarks.", "enabled_flag": True, "language_code": "en", "version_no": 1, "active_flag": True, "created_by": user_id},
            {"template_code": "job_transfer_rejected", "template_name": "Job Transfer Rejected", "category": "Dependency / Transfer Events", "channel_type": "Email", "recipient_role_variant": "Manager", "subject_template": "Transfer rejected · {job_no}", "body_template": "Transfer for job {job_no} was rejected. Reason: {status}. Please re-route and add manager remarks.", "enabled_flag": True, "language_code": "en", "version_no": 1, "active_flag": True, "created_by": user_id},
            {"template_code": "pending_approval_reminder", "template_name": "Pending Approval Reminder", "category": "Approval Events", "channel_type": "Email", "recipient_role_variant": "Approver", "subject_template": "Pending approvals: {approval_count}", "body_template": "You have {approval_count} pending {approval_type} approval(s). Oldest item pending for {pending_days} day(s). Action required today.", "enabled_flag": True, "language_code": "en", "version_no": 1, "active_flag": True, "created_by": user_id},
            {"template_code": "rollover_critical", "template_name": "Critical Rollover Escalation", "category": "Escalation Events", "channel_type": "Email", "recipient_role_variant": "Leadership", "subject_template": "Critical rollover escalation · {job_no}", "body_template": "Job {job_no} has rolled over {rollover_count} times and remains pending. Escalation stage {escalation_stage}. Leadership attention required.", "enabled_flag": True, "language_code": "en", "version_no": 1, "active_flag": True, "created_by": user_id},
            {"template_code": "billing_blocked", "template_name": "Billing Blocked", "category": "Billing / Profitability Events", "channel_type": "Email", "recipient_role_variant": "Finance", "subject_template": "Billing blocked · {job_no}", "body_template": "Job {job_no} billing is blocked. Reason: {billing_block_reason}. Review cost {cost_to_company} vs billed {billed_amount}.", "enabled_flag": True, "language_code": "en", "version_no": 1, "active_flag": True, "created_by": user_id},
            {"template_code": "daily_manager_digest", "template_name": "Daily Manager Digest", "category": "Reminder / Digest Events", "channel_type": "Email", "recipient_role_variant": "Manager", "subject_template": "Daily team summary · {department_name}", "body_template": "Daily task summary: {pending_count} pending, {overdue_count} overdue, {critical_count} critical. Oldest pending: {oldest_pending}. Action queue updated.", "enabled_flag": True, "language_code": "en", "version_no": 1, "active_flag": True, "created_by": user_id},
            {"template_code": "junior_pending_approval", "template_name": "Junior Pending Approval Summary", "category": "Reminder / Digest Events", "channel_type": "Email", "recipient_role_variant": "Reporting Manager", "subject_template": "Junior approvals pending · {approval_count}", "body_template": "Your team has {approval_count} junior approval(s) pending for over {pending_days} day(s). Please review pending approvers and clear bottlenecks.", "enabled_flag": True, "language_code": "en", "version_no": 1, "active_flag": True, "created_by": user_id},
        ]


class HierarchyVisibilityService:
    def __init__(self, db: Session):
        self.db = db

    def resolve_recipients(self, role: str, payload: dict, hide_downline_flag: bool = False) -> list[int | None]:
        employee_id = payload.get("assigned_employee_id") or payload.get("employee_id")
        manager_id = payload.get("manager_id")
        task_owner = payload.get("task_owner_id")
        job_owner = payload.get("job_owner_id") or payload.get("assigned_employee_id")
        creator_id = payload.get("created_by")
        approver_id = payload.get("approver_id")
        reporting_manager = payload.get("reporting_manager_id") or manager_id

        role_map = {
            "Assigned Employee": [employee_id],
            "Task Owner": [task_owner],
            "Job Owner": [job_owner],
            "Manager": [manager_id],
            "Reporting Manager": [reporting_manager],
            "Department Head": [payload.get("department_head_id") or self._manager_of(manager_id)],
            "Branch Head": [payload.get("branch_head_id")],
            "Leadership": self._leadership_chain(manager_id),
            "Approver": [approver_id],
            "Task Creator": [creator_id],
            "Finance": [payload.get("finance_user_id")],
            "Specific User": [payload.get("specific_user_id")],
            "Ticket Executive": [payload.get("ticket_exec_id")],
            "Client Contact": [payload.get("client_contact_user_id")],
        }
        recipients = role_map.get(role, [employee_id, manager_id, task_owner])
        recipients = [value for value in recipients if value]

        if hide_downline_flag and manager_id:
            downline = set(self._downline(manager_id))
            recipients = [value for value in recipients if value not in downline]
            recipients.append(manager_id)

        return sorted(set(recipients))

    def _downline(self, manager_id: int | None) -> list[int]:
        if not manager_id:
            return []
        return [int(row.emp_id) for row in self.db.query(RefEmployee).filter(RefEmployee.manager_id == manager_id, RefEmployee.is_active.is_(True)).all()]

    def _manager_of(self, emp_id: int | None) -> int | None:
        if not emp_id:
            return None
        row = self.db.query(RefEmployee).filter(RefEmployee.emp_id == emp_id, RefEmployee.is_active.is_(True)).first()
        return int(row.manager_id) if row and row.manager_id else None

    def _leadership_chain(self, manager_id: int | None) -> list[int]:
        if not manager_id:
            return []
        chain = []
        visited = set()
        current = manager_id
        while current and current not in visited:
            visited.add(current)
            chain.append(int(current))
            row = self.db.query(RefEmployee).filter(RefEmployee.emp_id == current, RefEmployee.is_active.is_(True)).first()
            current = row.manager_id if row else None
        return chain


class AlertAuditService:
    def __init__(self, db: Session):
        self.db = db

    def log(self, **kwargs) -> WmAlertLog:
        new_id = int((self.db.query(func.max(WmAlertLog.alert_log_id)).scalar() or 0) + 1)
        row = WmAlertLog(alert_log_id=new_id, **kwargs)
        self.db.add(row)
        return row


class AlertSettingsService:
    def __init__(self, db: Session):
        self.db = db

    def upsert_setting(self, payload: AlertSettingRequest) -> dict:
        self._validate_setting(payload)
        row = self.db.query(WmAlertSetting).filter(WmAlertSetting.setting_code == payload.setting_code).first()
        if row and row.channel_type == payload.channel_type and row.applies_to_company_id == payload.applies_to_company_id and row.applies_to_branch_id == payload.applies_to_branch_id and row.applies_to_department_id == payload.applies_to_department_id:
            for key, value in payload.model_dump().items():
                if key == "created_by":
                    continue
                setattr(row, key, value)
            row.updated_by = payload.created_by
            row.updated_at = datetime.utcnow()
        elif row:
            raise HTTPException(status_code=409, detail="same setting should not duplicate in same scope/channel")
        else:
            setting_id = int((self.db.query(func.max(WmAlertSetting.setting_id)).scalar() or 0) + 1)
            row = WmAlertSetting(setting_id=setting_id, **payload.model_dump())
            self.db.add(row)
        self.db.commit()
        return {"status": "success", "setting_id": row.setting_id}

    def list_settings(self, category: str | None = None, active_flag: bool | None = None) -> dict:
        query = self.db.query(WmAlertSetting)
        if category:
            query = query.filter(WmAlertSetting.category == category)
        if active_flag is not None:
            query = query.filter(WmAlertSetting.active_flag.is_(active_flag))
        rows = query.order_by(WmAlertSetting.setting_id.asc()).all()
        return {"status": "success", "rows": [{"setting_id": row.setting_id, "setting_code": row.setting_code, "setting_name": row.setting_name, "category": row.category, "entity_type": row.entity_type, "trigger_type": row.trigger_type, "channel_type": row.channel_type, "recipient_scope": row.recipient_scope, "enabled_flag": row.enabled_flag, "period_type": row.period_type, "period_value": row.period_value, "escalation_level": row.escalation_level, "hide_downline_flag": row.hide_downline_flag} for row in rows]}

    def seed_defaults(self, user_id: int = 1) -> dict:
        defaults = [
            ("TASK_CREATE_SMS", "Task Create SMS", "Task Alerts", "task", "task_created", "Assigned Employee", "SMS", True, "Immediate", None, False),
            ("TASK_CREATE_EMAIL", "Task Create Email", "Task Alerts", "task", "task_created", "Assigned Employee + Manager", "Email", True, "Immediate", None, False),
            ("TASK_COMPLETED_EMAIL", "Task Completed Email", "Task Alerts", "task", "task_completed", "Manager", "Email", True, "Immediate", None, False),
            ("PENDING_TASK_SMS", "Pending Task SMS", "Reminder", "task", "pending_task_reminder", "Assigned Employee", "SMS", True, "Daily", "1", False),
            ("PENDING_TASK_EMAIL", "Pending Task Email", "Reminder", "task", "pending_task_reminder", "Assigned Employee", "Email", True, "Daily", "1", False),
            ("PENDING_APPROVALS_SMS", "Pending Approvals SMS", "Approval Alerts", "approval", "pending_approval_reminder", "Manager", "SMS", True, "Every X Hours", "12", False),
            ("PENDING_APPROVALS_EMAIL", "Pending Approvals Email", "Approval Alerts", "approval", "pending_approval_reminder", "Manager", "Email", True, "Daily", "1", False),
            ("JUNIOR_PENDING_APPROVALS_EMAIL", "Junior Pending Approvals Email", "Approval Alerts", "approval", "junior_pending_approval", "Manager", "Email", True, "Daily", "1", True),
            ("OVERDUE_JOB_EMAIL", "Overdue Job Email", "SLA / Delay Alerts", "job", "job_overdue", "Assigned Employee + Manager", "Email", True, "Daily", "1", False),
            ("ROLLOVER_3PLUS_EMAIL", "3+ Rollover Critical Email", "Rollover Alerts", "job", "rollover_critical", "Leadership", "Email", True, "Immediate", None, False),
            ("BILLING_BLOCKED_EMAIL", "Billing Blocked Email", "Billing Alerts", "job", "billing_blocked", "Manager", "Email", True, "Daily", "1", False),
            ("DAILY_MANAGER_DIGEST", "Daily Manager Digest", "Digest / Summary Alerts", "manager", "daily_manager_digest", "Manager", "Email", True, "End of Day Digest", "21:30", False),
        ]

        created = 0
        for code, name, category, entity, trigger, scope, channel, enabled, period_type, period_value, hide_downline in defaults:
            if self.db.query(WmAlertSetting).filter(WmAlertSetting.setting_code == code).first():
                continue
            setting_id = int((self.db.query(func.max(WmAlertSetting.setting_id)).scalar() or 0) + 1)
            self.db.add(WmAlertSetting(setting_id=setting_id, setting_code=code, setting_name=name, category=category, entity_type=entity, trigger_type=trigger, recipient_scope=scope, channel_type=channel, enabled_flag=enabled, period_type=period_type, period_value=period_value, hide_downline_flag=hide_downline, active_flag=True, created_by=user_id))
            created += 1
        self.db.commit()

        matrix_created = RecipientMatrixService(self.db).seed_default_matrix()["created"]
        templates_created = TemplateService(self.db).seed_templates(user_id)["created"]
        return {"status": "success", "created": created, "matrix_created": matrix_created, "templates_created": templates_created}

    def _validate_setting(self, payload: AlertSettingRequest):
        if payload.enabled_flag and not payload.channel_type:
            raise HTTPException(status_code=422, detail="channel required when enabled")
        if payload.period_type in {"Daily", "Weekly", "Monthly", "Every X Hours", "Every X Days", "End of Day Digest", "Start of Day Digest"} and not payload.period_value:
            raise HTTPException(status_code=422, detail="period required for scheduled alerts")
        if not payload.recipient_scope:
            raise HTTPException(status_code=422, detail="recipient scope required")


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.template_service = TemplateService(db)
        self.visibility = HierarchyVisibilityService(db)
        self.audit = AlertAuditService(db)
        self.matrix = RecipientMatrixService(db)
        self.sms = SmsService()
        self.email = EmailService()
        self.inapp = InAppNotificationService()

    def trigger_event(self, payload: TriggerEventRequest) -> dict:
        settings = self.db.query(WmAlertSetting).filter(
            WmAlertSetting.entity_type == payload.entity_type,
            WmAlertSetting.trigger_type == payload.trigger_event,
            WmAlertSetting.enabled_flag.is_(True),
            WmAlertSetting.active_flag.is_(True),
        ).all()
        if not settings:
            return {"status": "success", "queued": 0, "sent": 0, "failed": 0, "suppressed": 0}

        sent = failed = suppressed = queued = 0
        entity_snapshot = self._entity_snapshot(payload.entity_type, payload.entity_id)
        merged_payload = {**entity_snapshot, **payload.payload, "trigger_event": payload.trigger_event, "entity_type": payload.entity_type, "entity_id": payload.entity_id}

        for setting in settings:
            if setting.priority_filter and str(merged_payload.get("priority", "")).upper() != str(setting.priority_filter).upper():
                continue

            escalation_stage = self._escalation_stage(setting, merged_payload)
            role_targets = self.matrix.resolve_roles(payload.trigger_event, payload.entity_type, merged_payload, escalation_stage)
            if not role_targets:
                role_targets = [{"recipient_role": setting.recipient_scope, "hide_downline_flag": setting.hide_downline_flag, "suppression_rule_id": None}]

            for role_target in role_targets:
                recipient_role = role_target["recipient_role"]
                recipients = self.visibility.resolve_recipients(recipient_role, merged_payload, role_target["hide_downline_flag"])
                for recipient in recipients:
                    if not self._is_recipient_active(recipient):
                        suppressed += 1
                        self.audit.log(setting_id=setting.setting_id, entity_type=payload.entity_type, entity_id=payload.entity_id, trigger_event=payload.trigger_event, recipient_role=recipient_role, recipient_user_id=recipient, recipient_channel=setting.channel_type, message_subject=None, message_body="inactive recipient", status="Suppressed", created_at=datetime.utcnow())
                        continue

                    if self._is_duplicate_within_window(setting.setting_id, payload.entity_type, payload.entity_id, recipient, setting.channel_type, minutes=30):
                        suppressed += 1
                        self.audit.log(setting_id=setting.setting_id, entity_type=payload.entity_type, entity_id=payload.entity_id, trigger_event=payload.trigger_event, recipient_role=recipient_role, recipient_user_id=recipient, recipient_channel=setting.channel_type, message_subject=None, message_body="deduplicated", status="Suppressed", created_at=datetime.utcnow())
                        continue

                    if payload.trigger_event in {"job_overdue", "pending_task_reminder"} and self._should_suppress_resolved(payload.entity_type, payload.entity_id):
                        suppressed += 1
                        self.audit.log(setting_id=setting.setting_id, entity_type=payload.entity_type, entity_id=payload.entity_id, trigger_event=payload.trigger_event, recipient_role=recipient_role, recipient_user_id=recipient, recipient_channel=setting.channel_type, message_subject=None, message_body="resolved before dispatch", status="Suppressed", created_at=datetime.utcnow())
                        continue

                    subject, body = self.template_service.render(setting.template_id, {**merged_payload, "recipient_role": recipient_role, "escalation_stage": escalation_stage}, setting.channel_type, recipient_role)
                    queued += 1
                    status, err = self._dispatch(setting.channel_type, recipient, subject, body)
                    sent += 1 if status == "Sent" else 0
                    failed += 1 if status == "Failed" else 0
                    self.audit.log(setting_id=setting.setting_id, entity_type=payload.entity_type, entity_id=payload.entity_id, trigger_event=payload.trigger_event, recipient_role=recipient_role, recipient_user_id=recipient, recipient_channel=setting.channel_type, message_subject=subject, message_body=body, status=status, sent_at=datetime.utcnow() if status == "Sent" else None, failed_at=datetime.utcnow() if status == "Failed" else None, error_message=err, created_at=datetime.utcnow())

        self.db.commit()
        return {"status": "success", "queued": queued, "sent": sent, "failed": failed, "suppressed": suppressed}

    def alert_center(self, user_id: int, unread_only: bool = False, category: str | None = None, priority: str | None = None) -> dict:
        query = self.db.query(WmAlertLog).filter(WmAlertLog.recipient_user_id == user_id)
        if unread_only:
            query = query.filter(WmAlertLog.read_at.is_(None))
        rows = query.order_by(WmAlertLog.created_at.desc()).all()
        if category:
            setting_map = {setting.setting_id: setting.category for setting in self.db.query(WmAlertSetting).all()}
            rows = [row for row in rows if setting_map.get(row.setting_id) == category]
        if priority:
            rows = [row for row in rows if f"priority={priority}" in (row.message_body or "")]
        return {
            "status": "success",
            "unread_count": sum(1 for row in rows if row.read_at is None),
            "rows": [{"alert_log_id": row.alert_log_id, "entity_type": row.entity_type, "entity_id": row.entity_id, "trigger_event": row.trigger_event, "recipient_role": row.recipient_role, "channel": row.recipient_channel, "status": row.status, "message_subject": row.message_subject, "message_body": row.message_body, "created_at": row.created_at, "read_at": row.read_at, "redirect_url": f"/{row.entity_type}/{row.entity_id}"} for row in rows],
        }

    def mark_read(self, payload: MarkReadRequest) -> dict:
        row = self.db.query(WmAlertLog).filter(WmAlertLog.alert_log_id == payload.alert_log_id, WmAlertLog.recipient_user_id == payload.user_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Alert log not found")
        row.read_at = datetime.utcnow()
        row.status = "Read" if row.status == "Sent" else row.status
        self.db.commit()
        return {"status": "success", "alert_log_id": payload.alert_log_id}

    def reports(self) -> dict:
        rows = self.db.query(WmAlertLog).all()
        settings = {setting.setting_id: setting for setting in self.db.query(WmAlertSetting).all()}
        templates = self.db.query(WmAlertTemplate).all()
        matrix = self.db.query(WmAlertRecipientMatrix).all()

        return {
            "status": "success",
            "template_usage_report": [{"template_code": template.template_code, "channel": template.channel_type, "recipient_role_variant": template.recipient_role_variant, "enabled": template.enabled_flag} for template in templates],
            "recipient_matrix_report": [{"event_code": row.event_code, "entity_type": row.entity_type, "recipient_role": row.recipient_role, "stage": row.escalation_stage, "include": row.include_flag} for row in matrix],
            "alerts_by_recipient_role": self._count_by(rows, lambda row: row.recipient_role or "Unknown"),
            "escalation_message_report": sum(1 for row in rows if "escalation" in row.trigger_event),
            "digest_delivery_summary": sum(1 for row in rows if settings.get(row.setting_id) and settings[row.setting_id].category == "Digest / Summary Alerts"),
            "suppressed_notification_summary": sum(1 for row in rows if row.status == "Suppressed"),
            "message_failure_summary": sum(1 for row in rows if row.status == "Failed"),
            "high_noise_recipient_report": self._top_by([row for row in rows if row.status in {"Sent", "Read"}], lambda row: row.recipient_user_id),
        }

    def dashboard_widgets(self) -> dict:
        rows = self.db.query(WmAlertLog).all()
        today = datetime.utcnow().date()
        sent_today = [row for row in rows if row.created_at.date() == today and row.status == "Sent"]
        failed_today = [row for row in rows if row.created_at.date() == today and row.status == "Failed"]
        queued = [row for row in rows if row.status == "Queued"]
        critical = [row for row in rows if "critical" in row.trigger_event.lower() and row.read_at is None]
        return {
            "status": "success",
            "alerts_sent_today": len(sent_today),
            "failed_alerts_today": len(failed_today),
            "pending_alerts_queue": len(queued),
            "critical_alerts_open": len(critical),
            "digest_jobs_pending": sum(1 for row in rows if "digest" in row.trigger_event.lower() and row.status == "Queued"),
            "suppressed_alerts": sum(1 for row in rows if row.status == "Suppressed"),
            "alert_volume_by_channel": self._count_by(rows, lambda row: row.recipient_channel),
            "alert_volume_by_type": self._count_by(rows, lambda row: row.trigger_event),
            "failure_trend": self._count_by([row for row in rows if row.status == "Failed"], lambda row: row.trigger_event),
            "repeated_recipient_alert_load": self._top_by(rows, lambda row: row.recipient_user_id),
        }

    def _dispatch(self, channel: str, recipient: int | None, subject: str | None, body: str):
        if channel == "SMS":
            return self.sms.send(recipient, subject, body)
        if channel == "Email":
            return self.email.send(recipient, subject, body)
        return self.inapp.send(recipient, subject, body)

    def _entity_snapshot(self, entity_type: str, entity_id: int) -> dict:
        if entity_type == "task":
            row = self.db.query(WmTask).filter(WmTask.task_id == entity_id).first()
            if not row:
                return {}
            pending_days = max((datetime.utcnow().date() - row.due_at.date()).days, 0) if getattr(row, "due_at", None) else 0
            return {"task_no": row.task_no, "task_name": row.title, "priority": row.priority_code, "status": row.status_code, "due_date": row.due_at, "pending_days": pending_days, "task_owner_id": row.primary_owner_emp_id, "assigned_employee_id": row.primary_owner_emp_id, "manager_id": row.manager_emp_id, "client_name": row.client_name, "created_by": row.created_by}
        if entity_type == "job":
            row = self.db.query(WmJob).filter(WmJob.job_id == entity_id).first()
            if not row:
                return {}
            pending_days = max((datetime.utcnow().date() - row.due_date).days, 0) if getattr(row, "due_date", None) else 0
            return {"job_no": row.job_no, "job_name": row.job_name, "priority": row.priority, "status": row.execution_status, "due_date": row.due_date, "pending_days": pending_days, "job_owner_id": row.assigned_employee_id, "assigned_employee_id": row.assigned_employee_id, "manager_id": row.manager_id, "client_name": row.client_name, "rollover_count": row.rollover_count, "billing_block_reason": row.billing_status, "cost_to_company": row.final_cost_to_company, "billed_amount": row.billed_amount, "profit_or_loss": row.profit_or_loss, "created_by": row.created_by}
        if entity_type == "timesheet":
            row = self.db.query(WmTimesheet).filter(WmTimesheet.timesheet_id == entity_id).first()
            if not row:
                return {}
            return {"timesheet_id": row.timesheet_id, "employee_id": row.emp_id, "status": row.approval_status, "expense_total": row.expense_total, "reimbursement_total": row.reimbursement_total, "created_by": row.created_by}
        if entity_type == "approval":
            row = self.db.query(WmManApproval).filter(WmManApproval.approval_id == entity_id).first()
            if not row:
                return {}
            return {"approval_id": row.approval_id, "approval_type": row.approval_type, "approval_count": 1, "status": row.current_status, "approver_id": row.approved_by or row.requested_by, "created_by": row.requested_by}
        return {}

    def _escalation_stage(self, setting: WmAlertSetting, payload: dict) -> int:
        pending_days = int(payload.get("pending_days") or 0)
        rollover_count = int(payload.get("rollover_count") or 0)
        priority = str(payload.get("priority", "")).upper()
        base_stage = 1
        if pending_days >= 1:
            base_stage = 2
        if pending_days >= 3 or rollover_count >= 3:
            base_stage = 3
        if pending_days >= 7 or priority in {"CRITICAL", "P1"}:
            base_stage = 4
        return max(base_stage, int(setting.escalation_level or 0) + 1)

    def _is_duplicate_within_window(self, setting_id, entity_type, entity_id, recipient, channel, minutes=30):
        since = datetime.utcnow() - timedelta(minutes=minutes)
        exists = self.db.query(func.count(WmAlertLog.alert_log_id)).filter(
            WmAlertLog.setting_id == setting_id,
            WmAlertLog.entity_type == entity_type,
            WmAlertLog.entity_id == entity_id,
            WmAlertLog.recipient_user_id == recipient,
            WmAlertLog.recipient_channel == channel,
            WmAlertLog.created_at >= since,
            WmAlertLog.status.in_(["Queued", "Sent", "Read"]),
        ).scalar() or 0
        return exists > 0

    def _is_recipient_active(self, emp_id: int | None):
        if not emp_id:
            return False
        row = self.db.query(RefEmployee).filter(RefEmployee.emp_id == emp_id, RefEmployee.is_active.is_(True)).first()
        return row is not None

    def _should_suppress_resolved(self, entity_type: str, entity_id: int) -> bool:
        if entity_type == "job":
            row = self.db.query(WmJob).filter(WmJob.job_id == entity_id).first()
            return row is not None and row.execution_status in {"Completed", "Billed", "Closed", "Cancelled"}
        if entity_type == "task":
            row = self.db.query(WmTask).filter(WmTask.task_id == entity_id).first()
            return row is not None and row.status_code in {"Done", "Closed", "Completed", "Cancelled"}
        return False

    def _count_by(self, rows, key_fn):
        out = {}
        for row in rows:
            key = key_fn(row)
            out[key] = out.get(key, 0) + 1
        return out

    def _top_by(self, rows, key_fn, top_n=10):
        counts = self._count_by(rows, key_fn)
        return sorted([{"key": key, "count": value} for key, value in counts.items()], key=lambda item: item["count"], reverse=True)[:top_n]


class AutomationSchedulerService:
    def __init__(self, db: Session):
        self.db = db
        self.notification = NotificationService(db)

    def run(self, payload: ScheduledRunRequest) -> dict:
        sent = 0
        tasks = self.db.query(WmTask).filter(WmTask.status_code.in_(["Open", "In Progress", "Waiting", "Critical"]), WmTask.is_active.is_(True)).all()
        for task in tasks:
            out = self.notification.trigger_event(TriggerEventRequest(entity_type="task", entity_id=task.task_id, trigger_event="pending_task_reminder", payload={"priority": task.priority_code}, triggered_by=payload.triggered_by))
            sent += out["sent"]

        pending_approvals = self.db.query(WmManApproval).filter(WmManApproval.current_status == "Pending").all()
        for approval in pending_approvals:
            out = self.notification.trigger_event(TriggerEventRequest(entity_type="approval", entity_id=approval.approval_id, trigger_event="pending_approval_reminder", payload={"approval_count": 1}, triggered_by=payload.triggered_by))
            sent += out["sent"]

        jobs = self.db.query(WmJob).filter(WmJob.is_active.is_(True)).all()
        today = datetime.utcnow().date()
        for job in jobs:
            if job.due_date and job.due_date < today and job.execution_status not in {"Completed", "Billed", "Closed", "Cancelled"}:
                sent += self.notification.trigger_event(TriggerEventRequest(entity_type="job", entity_id=job.job_id, trigger_event="job_overdue", payload={}, triggered_by=payload.triggered_by))["sent"]
            if int(job.rollover_count or 0) >= 3:
                sent += self.notification.trigger_event(TriggerEventRequest(entity_type="job", entity_id=job.job_id, trigger_event="rollover_critical", payload={"rollover_count": job.rollover_count}, triggered_by=payload.triggered_by))["sent"]
            if job.billing_status == "Blocked":
                sent += self.notification.trigger_event(TriggerEventRequest(entity_type="job", entity_id=job.job_id, trigger_event="billing_blocked", payload={"billing_block_reason": job.billing_status}, triggered_by=payload.triggered_by))["sent"]

        return {"status": "success", "run_key": payload.run_key, "sent": sent}
