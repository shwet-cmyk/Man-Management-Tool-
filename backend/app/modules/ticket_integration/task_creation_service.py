from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.wm_job import WmJob
from app.models.wm_task import WmTask
from app.models.wm_ticket import WmTicket
from app.modules.jobs.schemas import TaskShellCreateRequest
from app.modules.jobs.service import JobGovernanceService
from app.modules.ticket_integration.audit_service import IntegrationAuditService
from app.modules.ticket_integration.mappers import TicketMapperService
from app.modules.ticket_integration.schemas import IntegrationConfigRequest, TaskFromTicketRequest
from app.modules.ticket_integration.ticket_api_service import TicketApiService


class TicketTaskCreationService:
    def __init__(self, db: Session, config: IntegrationConfigRequest):
        self.db = db
        self.config = config
        self.mapper = TicketMapperService()
        self.audit = IntegrationAuditService(db)

    def create_from_ticket(self, payload: TaskFromTicketRequest) -> dict:
        ticket = self._get_ticket(payload.ticket_no, payload.use_live_fetch)
        if not ticket:
            raise HTTPException(status_code=404, detail="source ticket exists before task creation validation failed")

        dup_status, existing_task = self._duplicate_check(ticket, payload.allow_duplicate)
        if existing_task and dup_status == "blocked":
            self.audit.task_creation_log(
                ticket_no=ticket.ticket_no,
                task_no=existing_task.task_no,
                created_by=payload.triggered_by,
                mapping_status="skipped",
                duplicate_check_status="blocked",
                source_system=self.config.source_system_name,
                message="Duplicate creation blocked",
            )
            self.db.commit()
            return {
                "status": "validation_error",
                "message": "Task already exists for source ticket",
                "task_id": existing_task.task_id,
                "task_no": existing_task.task_no,
            }

        if not self.config.default_primary_owner_emp_id:
            raise HTTPException(status_code=422, detail="default_primary_owner_emp_id is required for API-based task creation")

        task_payload = self.mapper.to_task_payload(
            ticket=ticket,
            default_owner_id=self.config.default_primary_owner_emp_id,
            default_manager_id=self.config.default_manager_emp_id,
            default_billable=self.config.default_billable_flag,
        )
        task_payload = task_payload.model_copy(update={"allow_duplicate": payload.allow_duplicate, "source_type": "API", "source_reference": ticket.ticket_no})

        created = JobGovernanceService(self.db).create_task_shell(
            TaskShellCreateRequest(
                company_id=task_payload.company_id or 1,
                branch_id=task_payload.branch_id,
                department_id=task_payload.department_id,
                client_id=task_payload.customer_id,
                client_name=ticket.customer_name,
                title=task_payload.title,
                description=task_payload.description,
                product=ticket.product,
                category=ticket.category,
                priority=task_payload.priority_code,
                billable_flag=bool(task_payload.billable_flag),
                billed_amount=task_payload.billed_amount,
                task_owner_id=task_payload.primary_owner_emp_id or self.config.default_primary_owner_emp_id or 1,
                manager_id=task_payload.manager_emp_id,
                source_type="TICKET",
                source_ticket_id=ticket.ticket_id,
                remarks=ticket.remark,
            ),
            user_id=payload.triggered_by,
        )
        task = self.db.query(WmTask).filter(WmTask.task_id == created["task_id"]).first()
        task.source_ticket_id = ticket.ticket_id
        task.source_type = "TICKET"
        task.source_reference = f"{self.config.source_system_name}:{ticket.ticket_no}"

        if payload.create_first_job or self.config.auto_create_first_job:
            self._create_default_job(task, ticket, payload.triggered_by)

        self.audit.task_creation_log(
            ticket_no=ticket.ticket_no,
            task_no=task.task_no,
            created_by=payload.triggered_by,
            mapping_status="mapped",
            duplicate_check_status=dup_status,
            source_system=self.config.source_system_name,
            message="Task created from ticket",
        )
        self.db.commit()

        return {
            "status": "success",
            "task_id": task.task_id,
            "task_no": task.task_no,
            "ticket_no": ticket.ticket_no,
            "duplicate_check_status": dup_status,
        }

    def _get_ticket(self, ticket_no: str, use_live_fetch: bool) -> WmTicket | None:
        local = self.db.query(WmTicket).filter((WmTicket.ticket_no == ticket_no) | (WmTicket.external_ticket_no == ticket_no)).first()
        if local and not use_live_fetch:
            return local
        if not use_live_fetch:
            return local

        api = TicketApiService(force_mock=self.config.mock_mode)
        out = api.fetch_tickets(ticket_no=ticket_no, limit=1)
        if not out.get("success") or not out.get("tickets"):
            return local
        mapped = self.mapper.to_ticket_record(out["tickets"][0])
        existing = self.db.query(WmTicket).filter((WmTicket.ticket_no == mapped["ticket_no"]) | (WmTicket.external_ticket_no == mapped["external_ticket_no"])).first()
        if existing:
            for k, v in mapped.items():
                setattr(existing, k, v)
            return existing
        new_ticket_id = int((self.db.query(WmTicket.ticket_id).order_by(WmTicket.ticket_id.desc()).first() or (0,))[0] or 0) + 1
        ticket = WmTicket(ticket_id=new_ticket_id, **mapped)
        self.db.add(ticket)
        self.db.flush()
        return ticket

    def _duplicate_check(self, ticket: WmTicket, allow_duplicate: bool) -> tuple[str, WmTask | None]:
        existing = self.db.query(WmTask).filter(
            (WmTask.source_ticket_id == ticket.ticket_id)
            | (WmTask.source_reference == ticket.ticket_no)
            | (WmTask.source_reference == f"{self.config.source_system_name}:{ticket.ticket_no}")
        ).order_by(WmTask.task_id.desc()).first()
        if not existing:
            return "clear", None
        if allow_duplicate or self.config.duplicate_policy == "allow":
            return "allowed", existing
        if self.config.duplicate_policy == "allow_if_closed" and existing.status_code in {"Closed", "Cancelled"}:
            return "allowed", existing
        return "blocked", existing

    def _create_default_job(self, task: WmTask, ticket: WmTicket, user_id: int) -> None:
        next_id = int((self.db.query(WmJob.job_id).order_by(WmJob.job_id.desc()).first() or (0,))[0] or 0) + 1
        count = int((self.db.query(WmJob.job_id).count() or 0) + 1)
        job = WmJob(
            job_id=next_id,
            job_no=f"JOB-{count:05d}",
            parent_task_id=task.task_id,
            company_id=task.company_id or 0,
            branch_id=task.branch_id,
            department_id=task.department_id,
            customer_id=task.customer_id or 0,
            client_name=ticket.customer_name,
            job_name=f"Initial execution for {ticket.ticket_no}",
            description=ticket.description,
            assigned_employee_id=self.config.default_primary_owner_emp_id,
            manager_id=self.config.default_manager_emp_id,
            priority=task.priority_code,
            is_billable=task.billable_flag,
            execution_status="Ready to Start",
            billing_status="Not Billed",
            created_by=user_id,
        )
        self.db.add(job)
