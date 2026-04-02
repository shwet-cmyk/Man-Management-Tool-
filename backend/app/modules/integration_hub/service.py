from __future__ import annotations

import json
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.wm_api_key import WmApiKey
from app.models.wm_api_log import WmApiLog
from app.models.wm_expense_claim import WmExpenseClaim
from app.models.wm_job import WmJob
from app.models.wm_task import WmTask
from app.models.wm_timesheet import WmTimesheet
from app.models.wm_webhook import WmWebhook
from app.models.wm_webhook_log import WmWebhookLog
from app.modules.integration_hub.schemas import (
    ApiKeyCreateRequest,
    IntegrationExpensePushRequest,
    IntegrationTaskCreateRequest,
    IntegrationTaskUpdateRequest,
    IntegrationTimesheetPushRequest,
    TransactionPushRequest,
    WebhookCreateRequest,
)


class IntegrationHubService:
    def __init__(self, db: Session):
        self.db = db

    def create_api_key(self, payload: ApiKeyCreateRequest):
        row = WmApiKey(
            client_name=payload.client_name,
            api_key=payload.api_key,
            rate_limit_per_minute=payload.rate_limit_per_minute,
            is_active=True,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return {"api_key_id": row.api_key_id, "client_name": row.client_name}

    def validate_key(self, api_key: str) -> WmApiKey:
        key = self.db.query(WmApiKey).filter(WmApiKey.api_key == api_key, WmApiKey.is_active.is_(True)).first()
        if not key:
            raise HTTPException(status_code=401, detail="Invalid API key")

        window_start = datetime.utcnow() - timedelta(minutes=1)
        recent = (
            self.db.query(func.count(WmApiLog.log_id))
            .filter(WmApiLog.api_key_id == key.api_key_id, WmApiLog.created_on >= window_start)
            .scalar()
            or 0
        )
        if recent >= key.rate_limit_per_minute:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        return key

    def register_webhook(self, payload: WebhookCreateRequest):
        row = WmWebhook(event_name=payload.event_name, url=payload.url, secret=payload.secret, is_active=True)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return {"webhook_id": row.webhook_id, "event_name": row.event_name}

    def create_task(self, payload: IntegrationTaskCreateRequest, api_key_id: int):
        task_no = f"INT-{int(datetime.utcnow().timestamp())}"
        owner = payload.assigned_users[0] if payload.assigned_users else payload.created_by
        task = WmTask(
            task_no=task_no,
            company_id=payload.company_id,
            job_id=payload.job_id,
            customer_id=None,
            title=payload.title,
            task_type="Task",
            priority_code="Medium",
            status_code="Open",
            primary_owner_emp_id=owner,
            manager_emp_id=payload.created_by,
            billable_flag=True,
            estimated_hours=0,
            planned_start=datetime.utcnow(),
            due_at=payload.deadline,
            created_by=payload.created_by,
            source_type="API",
        )
        self.db.add(task)
        self.db.flush()
        self._trigger_webhook("TASK_CREATED", {"task_id": task.task_id, "title": task.title})
        self._log(api_key_id, "/wm/integrations/task", payload.model_dump(mode="json"), {"task_id": task.task_id}, 200)
        self.db.commit()
        return {"task_id": task.task_id, "task_no": task.task_no}

    def update_task(self, task_id: int, payload: IntegrationTaskUpdateRequest, api_key_id: int):
        task = self.db.query(WmTask).filter(WmTask.task_id == task_id, WmTask.is_active.is_(True)).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if payload.title is not None:
            task.title = payload.title
        if payload.status_code is not None:
            task.status_code = payload.status_code
        if payload.manager_emp_id is not None:
            task.manager_emp_id = payload.manager_emp_id
        task.updated_on = datetime.utcnow()
        self._trigger_webhook("TASK_UPDATED", {"task_id": task.task_id, "status_code": task.status_code})
        self._log(api_key_id, f"/wm/integrations/task/{task_id}", payload.model_dump(mode="json"), {"task_id": task.task_id}, 200)
        self.db.commit()
        return {"task_id": task.task_id, "status_code": task.status_code}

    def fetch_job(self, job_id: int, api_key_id: int):
        job = self.db.query(WmJob).filter(WmJob.job_id == job_id, WmJob.is_active.is_(True)).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        task_count = self.db.query(func.count(WmTask.task_id)).filter(WmTask.job_id == job_id, WmTask.is_active.is_(True)).scalar() or 0
        out = {
            "job_id": job.job_id,
            "job_no": job.job_no,
            "job_name": job.job_name,
            "company_id": job.company_id,
            "customer_id": job.customer_id,
            "execution_status": job.execution_status,
            "billing_status": job.billing_status,
            "task_count": int(task_count),
        }
        self._log(api_key_id, f"/wm/integrations/jobs/{job_id}", {}, out, 200)
        return out

    def push_timesheet(self, payload: IntegrationTimesheetPushRequest, api_key_id: int):
        row = WmTimesheet(
            company_id=payload.company_id,
            job_id=payload.job_id,
            task_id=payload.task_id,
            emp_id=payload.emp_id,
            work_date=payload.work_date,
            hours=payload.hours,
            billable_hours=payload.billable_hours,
            overtime_hours=0,
            approval_status="Submitted",
            submitted_by=payload.created_by,
            submitted_on=datetime.utcnow(),
            created_by=payload.created_by,
        )
        self.db.add(row)
        self.db.flush()
        self._trigger_webhook("TIMESHEET_PUSHED", {"timesheet_id": row.timesheet_id, "job_id": row.job_id})
        self._log(api_key_id, "/wm/integrations/timesheets", payload.model_dump(mode="json"), {"timesheet_id": row.timesheet_id}, 200)
        self.db.commit()
        return {"timesheet_id": row.timesheet_id}

    def push_expense(self, payload: IntegrationExpensePushRequest, api_key_id: int):
        claim_no = f"INT-EXP-{int(datetime.utcnow().timestamp())}"
        total_amount = payload.amount + payload.tax_amount
        row = WmExpenseClaim(
            claim_no=claim_no,
            claim_type="REIMBURSEMENT",
            expense_type=payload.expense_type,
            company_id=payload.company_id,
            emp_id=payload.emp_id,
            job_id=payload.job_id,
            task_id=payload.task_id,
            expense_date=payload.expense_date,
            amount=payload.amount,
            tax_amount=payload.tax_amount,
            total_amount=total_amount,
            recoverable_flag=True,
            approval_status="Submitted",
            submitted_by=payload.created_by,
            submitted_on=datetime.utcnow(),
            created_by=payload.created_by,
        )
        self.db.add(row)
        self.db.flush()
        self._trigger_webhook("EXPENSE_PUSHED", {"claim_id": row.claim_id, "total_amount": str(total_amount)})
        self._log(api_key_id, "/wm/integrations/expenses", payload.model_dump(mode="json"), {"claim_id": row.claim_id}, 200)
        self.db.commit()
        return {"claim_id": row.claim_id, "claim_no": row.claim_no}

    def push_transaction(self, payload: TransactionPushRequest, api_key_id: int):
        self._trigger_webhook(f"{payload.source}_PUSHED", payload.payload)
        response = {"status": "RECEIVED", "source": payload.source, "reference_no": payload.reference_no}
        self._log(api_key_id, "/wm/integrations/finance/transactions", payload.model_dump(mode="json"), response, 202)
        self.db.commit()
        return response

    def _trigger_webhook(self, event_name: str, payload: dict):
        hooks = self.db.query(WmWebhook).filter(WmWebhook.event_name == event_name, WmWebhook.is_active.is_(True)).all()
        for hook in hooks:
            self.db.add(
                WmWebhookLog(
                    webhook_id=hook.webhook_id,
                    event_name=event_name,
                    payload=json.dumps(payload, default=str),
                    status="QUEUED",
                    http_status_code=None,
                )
            )

    def _log(self, api_key_id: int, endpoint: str, request: dict, response: dict, status_code: int):
        self.db.add(
            WmApiLog(
                api_key_id=api_key_id,
                endpoint=endpoint,
                request=json.dumps(request, default=str),
                response=json.dumps(response, default=str),
                status_code=status_code,
            )
        )
