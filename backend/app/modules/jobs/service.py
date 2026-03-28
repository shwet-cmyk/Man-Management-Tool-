from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ref_employee import RefEmployee
from app.models.task_audit_log import TaskAuditLog
from app.models.wm_holiday_calendar import WmHolidayCalendar
from app.models.wm_job import WmJob
from app.models.wm_shift_master import WmShiftMaster
from app.models.wm_task import WmTask
from app.models.wm_task_child_item import WmTaskChildItem
from app.models.wm_timesheet import WmTimesheet
from app.modules.jobs.schemas import GovernanceConfigRequest, JobCreateRequest, JobStatusTransitionRequest, TaskShellCreateRequest, TransferDecisionRequest

OVERHEAD_RATE = Decimal("0.10")


class JobGovernanceService:
    def __init__(self, db: Session):
        self.db = db
        self.monthly_working_hours = Decimal("208")
        self.strict_shift_enforcement = False

    def configure(self, payload: GovernanceConfigRequest) -> dict:
        self.monthly_working_hours = payload.monthly_working_hours
        self.strict_shift_enforcement = payload.strict_shift_enforcement
        return {"status": "SUCCESS", "monthly_working_hours": str(self.monthly_working_hours), "strict_shift_enforcement": self.strict_shift_enforcement}

    def create_task_shell(self, payload: TaskShellCreateRequest, user_id: int = 1) -> dict:
        if payload.billable_flag and not payload.client_id:
            raise HTTPException(status_code=422, detail="Billable task should have client")
        if payload.billed_amount < 0:
            raise HTTPException(status_code=422, detail="Billed amount cannot be negative")

        task = WmTask(
            task_id=self._next_task_id(),
            task_no=self._next_task_no(),
            company_id=payload.company_id,
            branch_id=payload.branch_id,
            department_id=payload.department_id,
            customer_id=payload.client_id,
            client_name=payload.client_name,
            title=payload.title,
            description=payload.description,
            product=payload.product,
            category=payload.category,
            task_type="Task",
            priority_code=payload.priority,
            status_code="Draft",
            primary_owner_emp_id=payload.task_owner_id,
            manager_emp_id=payload.manager_id,
            billable_flag=payload.billable_flag,
            billed_amount=payload.billed_amount,
            total_billed_amount=payload.billed_amount,
            estimated_hours=payload.planned_hours or Decimal("0"),
            planned_start=payload.start_date or datetime.utcnow(),
            due_at=payload.end_date or datetime.utcnow(),
            source_type=payload.source_type,
            source_ticket_id=payload.source_ticket_id,
            remarks=payload.remarks,
            created_by=user_id,
            created_on=datetime.utcnow(),
            financial_status="Billable Pending" if payload.billable_flag else "Not Billable",
        )
        self.db.add(task)
        self.db.flush()
        self._audit("task_creation", task.task_id, user_id, f"title={payload.title}")
        self.db.commit()
        return {"status": "SUCCESS", "task_id": task.task_id, "task_no": task.task_no}

    def create_job(self, payload: JobCreateRequest, user_id: int = 1) -> dict:
        task = self._task(payload.parent_task_id)
        self._validate_employee(payload.assigned_employee_id)
        if payload.billed_amount < 0:
            raise HTTPException(status_code=422, detail="Billed amount cannot be negative")
        if payload.billable_flag is True and not payload.client_id:
            raise HTTPException(status_code=422, detail="Billable task should have client")

        job = WmJob(
            job_id=self._next_job_id(),
            job_no=self._next_job_no(),
            parent_task_id=payload.parent_task_id,
            company_id=payload.company_id,
            branch_id=payload.branch_id,
            department_id=payload.department_id,
            customer_id=payload.client_id or task.customer_id or 0,
            client_name=payload.client_name,
            job_name=payload.title,
            description=payload.description,
            assigned_employee_id=payload.assigned_employee_id,
            assigned_employee_name=payload.assigned_employee_name,
            assigned_manager_id=payload.assigned_manager_id,
            assigned_manager_name=payload.assigned_manager_name,
            priority=payload.priority,
            start_date=payload.start_date,
            due_date=payload.due_date,
            planned_hours=payload.planned_hours,
            estimated_amount=payload.estimated_amount,
            is_billable=task.billable_flag if payload.billable_flag is None else payload.billable_flag,
            billed_amount=payload.billed_amount,
            manager_id=payload.assigned_manager_id or task.manager_emp_id,
            execution_status="Blocked" if payload.dependency_job_id else "Ready to Start",
            dependency_job_id=payload.dependency_job_id,
            dependency_mode=payload.dependency_mode,
            dependency_type=payload.dependency_mode,
            dependency_completion_required=payload.dependency_completion_required,
            dependency_mandatory_flag=payload.dependency_completion_required,
            dependency_status="Pending" if payload.dependency_job_id else "Not Required",
            transfer_required=payload.transfer_required,
            acceptance_required=payload.acceptance_required,
            transfer_status="Pending" if payload.dependency_job_id else "Not Required",
            remarks=payload.remarks,
            created_by=user_id,
            created_on=datetime.utcnow(),
        )
        self._validate_dependency_chain(job)
        self.db.add(job)
        self.db.flush()
        self._audit("job_creation", job.job_id, user_id, f"task_id={task.task_id};dependency_job_id={payload.dependency_job_id}")
        self.recalculate_task_rollups(task.task_id, user_id=user_id)
        self.db.commit()
        return {"status": "SUCCESS", "job_id": job.job_id, "job_no": job.job_no, "job_status": job.execution_status}

    def transition_job_status(self, job_id: int, payload: JobStatusTransitionRequest) -> dict:
        job = self._job(job_id)
        if payload.status == "In Progress" and job.acceptance_required and job.transfer_status in {"Pending", "Awaiting Acceptance", "Rejected"}:
            raise HTTPException(status_code=422, detail="Acceptance required before starting job")
        if payload.status == "Completed":
            self._validate_job_completion(job, payload)
            job.completed_at = datetime.utcnow()
            job.completed_by = payload.changed_by
            self._trigger_dependents(job, payload.changed_by)
        if payload.status == "Reopened":
            job.completed_at = None
            job.completed_by = None

        old_status = job.execution_status
        job.execution_status = payload.status
        if payload.status == "Critical":
            job.critical_flag = True
        job.updated_by = payload.changed_by
        job.updated_on = datetime.utcnow()
        self._audit("job_status_change", job.job_id, payload.changed_by, f"old={old_status};new={payload.status};remarks={payload.remarks}")
        self.recalculate_costs_for_job(job.job_id)
        self.recalculate_task_rollups(job.parent_task_id, user_id=payload.changed_by)
        self.db.commit()
        return {"status": "SUCCESS", "job_id": job_id, "old_status": old_status, "new_status": job.execution_status}

    def decide_transfer(self, job_id: int, payload: TransferDecisionRequest) -> dict:
        job = self._job(job_id)
        if not job.transfer_required:
            raise HTTPException(status_code=422, detail="Transfer is not required")
        if job.transfer_to_employee_id and job.transfer_to_employee_id != payload.employee_id:
            raise HTTPException(status_code=403, detail="Transfer decision can only be taken by successor employee")

        if payload.decision == "ACCEPT":
            job.transfer_status = "Accepted"
            job.transfer_accepted_at = datetime.utcnow()
            job.dependency_status = "Completed"
            if job.execution_status in {"Blocked", "Awaiting Acceptance"}:
                job.execution_status = "Ready to Start"
            event = "transfer_accepted"
        else:
            if not payload.reason:
                raise HTTPException(status_code=422, detail="rejection reason mandatory")
            job.transfer_status = "Rejected"
            job.transfer_rejected_at = datetime.utcnow()
            job.transfer_rejection_reason = payload.reason
            event = "transfer_rejected"

        self._audit(event, job.job_id, payload.employee_id, payload.reason or payload.decision)
        self.recalculate_task_rollups(job.parent_task_id, user_id=payload.employee_id)
        self.db.commit()
        return {"status": "SUCCESS", "job_id": job.job_id, "transfer_status": job.transfer_status}

    def recalculate_costs_for_job(self, job_id: int) -> dict:
        job = self._job(job_id)
        direct = Decimal("0")
        spent = Decimal("0")
        timesheets = self.db.query(WmTimesheet).filter(WmTimesheet.job_id == job_id, WmTimesheet.is_active.is_(True)).all()
        for ts in timesheets:
            hourly = self._employee_hourly_cost(ts.emp_id)
            direct += Decimal(str(ts.hours or 0)) * hourly
            spent += Decimal(str(ts.hours or 0))

        job.spent_hours = spent
        job.cost_to_company = direct.quantize(Decimal("0.01"))
        # Overhead is intentionally computed once at job level for job reporting; task applies overhead at task level only.
        job.overhead_amount = (direct * OVERHEAD_RATE).quantize(Decimal("0.01"))
        job.final_cost_to_company = (job.cost_to_company + job.overhead_amount).quantize(Decimal("0.01"))
        job.profit_or_loss = (Decimal(str(job.billed_amount or 0)) - job.final_cost_to_company).quantize(Decimal("0.01"))
        self.db.flush()
        return {"status": "SUCCESS", "job_id": job_id, "direct_cost": str(job.cost_to_company)}

    def recalculate_task_rollups(self, task_id: int, user_id: int = 1) -> dict:
        task = self._task(task_id)
        jobs = self.db.query(WmJob).filter(WmJob.parent_task_id == task_id, WmJob.is_active.is_(True)).all()
        if jobs:
            starts = [j.start_date for j in jobs if j.start_date]
            ends = [j.due_date for j in jobs if j.due_date]
            if starts:
                task.planned_start = datetime.combine(min(starts), datetime.min.time())
            if ends:
                task.due_at = datetime.combine(max(ends), datetime.min.time())

        direct = Decimal("0")
        actual_hours = Decimal("0")
        total_billed = Decimal(str(task.billed_amount or 0))
        completed = 0
        blocked = 0
        pending = 0
        rollover = 0

        for job in jobs:
            self.recalculate_costs_for_job(job.job_id)
            direct += Decimal(str(job.cost_to_company or 0))
            actual_hours += Decimal(str(job.spent_hours or 0))
            total_billed += Decimal(str(job.billed_amount or 0))
            rollover += int(job.rollover_count or 0)
            if job.execution_status == "Completed":
                completed += 1
            elif job.execution_status == "Blocked":
                blocked += 1
            elif job.execution_status not in {"Closed", "Cancelled"}:
                pending += 1

        task.total_job_count = len(jobs)
        task.completed_job_count = completed
        task.blocked_job_count = blocked
        task.pending_job_count = pending
        task.rollover_count_rollup = rollover
        task.actual_hours_rollup = actual_hours.quantize(Decimal("0.01"))
        task.total_direct_cost = direct.quantize(Decimal("0.01"))
        task.total_overhead_amount = (direct * OVERHEAD_RATE).quantize(Decimal("0.01"))
        task.total_cost_to_company = (task.total_direct_cost + task.total_overhead_amount).quantize(Decimal("0.01"))
        task.total_cost_with_overhead = task.total_cost_to_company
        task.total_billed_amount = total_billed.quantize(Decimal("0.01"))
        task.total_profit_or_loss = (task.total_billed_amount - task.total_cost_to_company).quantize(Decimal("0.01"))
        task.progress_percent = Decimal("0.00") if len(jobs) == 0 else (Decimal(completed) * Decimal("100") / Decimal(len(jobs))).quantize(Decimal("0.01"))
        task.critical_flag = blocked > 0 or rollover >= 3
        task.status_code = self._derive_task_status(task, jobs)
        task.financial_status = self._derive_financial_status(task)
        task.updated_by = user_id
        task.updated_on = datetime.utcnow()
        self._audit("task_profitability_change", task.task_id, user_id, f"cost={task.total_cost_to_company};billed={task.total_billed_amount};pnl={task.total_profit_or_loss}")
        self.db.flush()
        return {"status": "SUCCESS", "task_id": task.task_id, "financial_status": task.financial_status}

    def dashboard_metrics(self) -> dict:
        jobs = self.db.query(WmJob).filter(WmJob.is_active.is_(True)).all()
        tasks = self.db.query(WmTask).filter(WmTask.is_active.is_(True)).all()
        return {
            "total_tasks": len(tasks),
            "active_tasks": sum(1 for t in tasks if t.status_code in {"Active", "In Progress", "Partially Complete"}),
            "total_jobs": len(jobs),
            "pending_jobs": sum(1 for j in jobs if j.execution_status in {"Ready to Start", "In Progress", "Blocked", "Awaiting Acceptance"}),
            "critical_jobs": sum(1 for j in jobs if j.critical_flag),
            "awaiting_acceptance_jobs": sum(1 for j in jobs if j.transfer_status == "Awaiting Acceptance"),
            "tasks_in_loss": sum(1 for t in tasks if Decimal(str(t.total_profit_or_loss or 0)) < 0),
            "profitable_tasks": sum(1 for t in tasks if Decimal(str(t.total_profit_or_loss or 0)) > 0),
            "non_billable_cost": str(sum((Decimal(str(t.total_cost_to_company or 0)) for t in tasks if not t.billable_flag), Decimal("0"))),
            "total_billable_amount": str(sum((Decimal(str(t.total_billed_amount or 0)) for t in tasks if t.billable_flag), Decimal("0"))),
            "total_cost_to_company": str(sum((Decimal(str(t.total_cost_to_company or 0)) for t in tasks), Decimal("0"))),
            "total_profit": str(sum((max(Decimal("0"), Decimal(str(t.total_profit_or_loss or 0))) for t in tasks), Decimal("0"))),
            "total_loss": str(sum((abs(min(Decimal("0"), Decimal(str(t.total_profit_or_loss or 0)))) for t in tasks), Decimal("0"))),
        }

    def report_registers(self) -> dict:
        tasks = self.db.query(WmTask).filter(WmTask.is_active.is_(True)).all()
        jobs = self.db.query(WmJob).filter(WmJob.is_active.is_(True)).all()
        timesheets = self.db.query(WmTimesheet).filter(WmTimesheet.is_active.is_(True)).all()
        return {
            "task_register": [
                {
                    "task_id": t.task_id,
                    "task_no": t.task_no,
                    "status": t.status_code,
                    "financial_status": t.financial_status,
                    "total_jobs": t.total_job_count,
                    "blocked_jobs": t.blocked_job_count,
                    "profit_or_loss": str(t.total_profit_or_loss),
                    "source_type": t.source_type,
                }
                for t in tasks
            ],
            "job_register": [
                {
                    "job_id": j.job_id,
                    "job_no": j.job_no,
                    "task_id": j.parent_task_id,
                    "status": j.execution_status,
                    "dependency_job_id": j.dependency_job_id,
                    "dependency_status": j.dependency_status,
                    "transfer_status": j.transfer_status,
                    "cost_to_company": str(j.cost_to_company),
                    "billed_amount": str(j.billed_amount),
                    "profit_or_loss": str(j.profit_or_loss),
                }
                for j in jobs
            ],
            "timesheet_report": [
                {
                    "timesheet_id": ts.timesheet_id,
                    "task_id": ts.task_id,
                    "job_id": ts.job_id,
                    "employee_id": ts.emp_id,
                    "date": ts.work_date.isoformat(),
                    "hours": str(ts.hours),
                    "expense_total": str(ts.expense_total),
                    "reimbursement_total": str(ts.reimbursement_total),
                    "approval_status": ts.approval_status,
                }
                for ts in timesheets
            ],
        }

    def _task(self, task_id: int) -> WmTask:
        task = self.db.query(WmTask).filter(WmTask.task_id == task_id, WmTask.is_active.is_(True)).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    def _job(self, job_id: int) -> WmJob:
        job = self.db.query(WmJob).filter(WmJob.job_id == job_id, WmJob.is_active.is_(True)).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job

    def _validate_employee(self, emp_id: int) -> None:
        employee = self.db.query(RefEmployee).filter(RefEmployee.emp_id == emp_id, RefEmployee.is_active.is_(True)).first()
        if not employee:
            raise HTTPException(status_code=422, detail="employee must exist in employee master")
        if employee.shift_id:
            exists_shift = self.db.query(func.count(WmShiftMaster.shift_id)).filter(WmShiftMaster.shift_id == employee.shift_id).scalar() or 0
            if exists_shift == 0:
                raise HTTPException(status_code=422, detail="shift / holiday mapping must be valid")
        if employee.holiday_calendar_id:
            exists_cal = self.db.query(func.count(WmHolidayCalendar.holiday_calendar_id)).filter(WmHolidayCalendar.holiday_calendar_id == employee.holiday_calendar_id).scalar() or 0
            if exists_cal == 0:
                raise HTTPException(status_code=422, detail="shift / holiday mapping must be valid")

    def _validate_dependency_chain(self, new_job: WmJob) -> None:
        if not new_job.dependency_job_id:
            return
        if new_job.dependency_job_id == new_job.job_id:
            raise HTTPException(status_code=422, detail="one job cannot depend on itself")

        cursor = new_job.dependency_job_id
        visited = set()
        while cursor:
            if cursor in visited:
                raise HTTPException(status_code=422, detail="dependency loops should be prevented")
            visited.add(cursor)
            dep = self.db.query(WmJob).filter(WmJob.job_id == cursor, WmJob.is_active.is_(True)).first()
            if not dep:
                raise HTTPException(status_code=422, detail="Dependency job not found")
            if dep.parent_task_id != new_job.parent_task_id:
                raise HTTPException(status_code=422, detail="Dependency must belong to same task")
            cursor = dep.dependency_job_id

    def _validate_job_completion(self, job: WmJob, payload: JobStatusTransitionRequest) -> None:
        if job.dependency_job_id and job.dependency_completion_required:
            dep = self._job(job.dependency_job_id)
            if dep.execution_status != "Completed":
                raise HTTPException(status_code=422, detail="a Job with dependency cannot complete before predecessor completion")
            if job.acceptance_required and job.transfer_status != "Accepted":
                raise HTTPException(status_code=422, detail="if acceptance_required = true, successor job cannot start before acceptance")

        timesheet_count = self.db.query(func.count(WmTimesheet.timesheet_id)).filter(WmTimesheet.job_id == job.job_id, WmTimesheet.is_active.is_(True)).scalar() or 0
        if timesheet_count == 0:
            raise HTTPException(status_code=422, detail="timesheet required before job completion if enabled")
        if not payload.remarks:
            raise HTTPException(status_code=422, detail="mandatory remarks are required before completion")

        open_child_items = self.db.query(func.count(WmTaskChildItem.child_item_id)).filter(
            WmTaskChildItem.parent_task_id == job.parent_task_id,
            WmTaskChildItem.assignee_emp_id == job.assigned_employee_id,
            WmTaskChildItem.status_code != "Done",
        ).scalar() or 0
        if open_child_items > 0:
            raise HTTPException(status_code=422, detail="all job tasks/checklist complete")

    def _trigger_dependents(self, predecessor: WmJob, user_id: int) -> None:
        dependents = self.db.query(WmJob).filter(WmJob.dependency_job_id == predecessor.job_id, WmJob.is_active.is_(True)).all()
        for job in dependents:
            job.dependency_status = "Completed"
            if job.transfer_required:
                job.transfer_status = "Awaiting Acceptance"
                job.transfer_from_employee_id = predecessor.assigned_employee_id
                job.transfer_to_employee_id = job.assigned_employee_id
                job.transfer_requested_at = datetime.utcnow()
                job.execution_status = "Awaiting Acceptance"
                self._audit("transfer_triggered", job.job_id, user_id, f"from={job.transfer_from_employee_id};to={job.transfer_to_employee_id}")
            else:
                job.transfer_status = "Not Required"
                job.execution_status = "Ready to Start"

    def _derive_task_status(self, task: WmTask, jobs: list[WmJob]) -> str:
        if task.critical_flag:
            return "Critical"
        if not jobs:
            return "Planned" if task.planned_start else "Draft"
        if all(j.execution_status in {"Completed", "Closed"} for j in jobs):
            return "Completed"
        if any(j.execution_status == "Blocked" for j in jobs):
            return "Waiting"
        if any(j.execution_status in {"In Progress", "Ready to Start", "Awaiting Acceptance"} for j in jobs):
            return "Active"
        if any(j.execution_status in {"Submitted", "Reviewed"} for j in jobs):
            return "Under Review"
        return "Partially Complete"

    def _derive_financial_status(self, task: WmTask) -> str:
        if not task.billable_flag:
            return "Not Billable"
        if Decimal(str(task.total_billed_amount or 0)) <= 0:
            return "Billable Pending"
        if Decimal(str(task.total_billed_amount or 0)) < Decimal(str(task.total_cost_to_company or 0)):
            return "Loss"
        if Decimal(str(task.total_billed_amount or 0)) == Decimal(str(task.total_cost_to_company or 0)):
            return "Break Even"
        return "Profit"

    def _employee_hourly_cost(self, emp_id: int) -> Decimal:
        emp = self.db.query(RefEmployee).filter(RefEmployee.emp_id == emp_id, RefEmployee.is_active.is_(True)).first()
        if not emp:
            raise HTTPException(status_code=422, detail=f"Unknown employee for costing: {emp_id}")
        if emp.hourly_cost is not None:
            return Decimal(str(emp.hourly_cost))
        return (Decimal(str(emp.monthly_ctc or 0)) / self.monthly_working_hours).quantize(Decimal("0.01"))

    def _next_task_no(self) -> str:
        count = self.db.query(func.count(WmTask.task_id)).scalar() or 0
        return f"TSK-{count + 1:05d}"

    def _next_job_no(self) -> str:
        count = self.db.query(func.count(WmJob.job_id)).scalar() or 0
        return f"JOB-{count + 1:05d}"

    def _next_task_id(self) -> int:
        return int((self.db.query(func.max(WmTask.task_id)).scalar() or 0) + 1)

    def _next_job_id(self) -> int:
        return int((self.db.query(func.max(WmJob.job_id)).scalar() or 0) + 1)

    def _audit(self, action: str, entity_id: int, user_id: int, details: str) -> None:
        self.db.add(TaskAuditLog(entity_name="task_job_engine", entity_id=entity_id, action=action.upper(), details=details, created_by=user_id))
