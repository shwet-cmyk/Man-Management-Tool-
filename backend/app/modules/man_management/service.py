from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ref_employee import RefEmployee
from app.models.task_audit_log import TaskAuditLog
from app.models.wm_business_holiday import WmBusinessHoliday
from app.models.wm_employee_group import WmEmployeeGroup
from app.models.wm_employee_group_member import WmEmployeeGroupMember
from app.models.wm_job import WmJob
from app.models.wm_job_task_line import WmJobTaskLine
from app.models.wm_man_approval import WmManApproval
from app.models.wm_man_management_setting import WmManManagementSetting
from app.models.wm_task import WmTask
from app.models.wm_timesheet import WmTimesheet
from app.models.wm_timesheet_expense_line import WmTimesheetExpenseLine
from app.models.wm_timesheet_reimbursement_line import WmTimesheetReimbursementLine
from app.modules.man_management.schemas import ApprovalActionRequest, BillingActionRequest, EmployeeGroupCreateRequest, HolidayCreateRequest, JobTaskLineRequest, JobTaskStatusRequest, JobUpsertRequest, SettingsUpsertRequest, TimesheetEntryRequest


class ManManagementService:
    def __init__(self, db: Session):
        self.db = db

    # ---------- Employee Group Master ----------
    def create_employee_group(self, payload: EmployeeGroupCreateRequest) -> dict:
        existing = self.db.query(WmEmployeeGroup).filter(WmEmployeeGroup.group_code == payload.group_code).first()
        if existing:
            raise HTTPException(status_code=409, detail="group_code already exists")

        group_id = int((self.db.query(func.max(WmEmployeeGroup.employee_group_id)).scalar() or 0) + 1)
        group = WmEmployeeGroup(
            employee_group_id=group_id,
            group_code=payload.group_code,
            group_name=payload.group_name,
            description=payload.description,
            active_flag=payload.active_flag,
            created_by=payload.created_by,
        )
        self.db.add(group)
        for emp_id in payload.employee_ids:
            self._validate_employee(emp_id)
            member_id = int((self.db.query(func.max(WmEmployeeGroupMember.group_member_id)).scalar() or 0) + 1)
            self.db.add(WmEmployeeGroupMember(group_member_id=member_id, employee_group_id=group_id, emp_id=emp_id, created_by=payload.created_by))
        self._audit("EMPLOYEE_GROUP_CREATE", group_id, payload.created_by, f"code={payload.group_code}")
        self.db.commit()
        return {"status": "success", "employee_group_id": group_id}

    def list_employee_groups(self, active_flag: bool | None = None, search: str | None = None) -> dict:
        query = self.db.query(WmEmployeeGroup)
        if active_flag is not None:
            query = query.filter(WmEmployeeGroup.active_flag.is_(active_flag))
        if search:
            like = f"%{search}%"
            query = query.filter((WmEmployeeGroup.group_code.like(like)) | (WmEmployeeGroup.group_name.like(like)))
        rows = query.order_by(WmEmployeeGroup.group_name.asc()).all()
        return {"status": "success", "rows": [{"employee_group_id": r.employee_group_id, "group_code": r.group_code, "group_name": r.group_name, "active_flag": r.active_flag} for r in rows]}

    # ---------- Holiday Master ----------
    def create_holiday(self, payload: HolidayCreateRequest) -> dict:
        new_id = int((self.db.query(func.max(WmBusinessHoliday.holiday_id)).scalar() or 0) + 1)
        row = WmBusinessHoliday(
            holiday_id=new_id,
            holiday_date=payload.holiday_date,
            name=payload.holiday_name,
            company_id=payload.company_id,
            branch_id=payload.branch_id,
        )
        self.db.add(row)
        self._audit("HOLIDAY_CREATE", new_id, payload.created_by, f"date={payload.holiday_date};type={payload.holiday_type};dept={payload.department_id}")
        self.db.commit()
        return {"status": "success", "holiday_id": new_id}

    def list_holidays(self, company_id: int | None = None, branch_id: int | None = None, from_date=None, to_date=None) -> dict:
        query = self.db.query(WmBusinessHoliday)
        if company_id:
            query = query.filter(WmBusinessHoliday.company_id == company_id)
        if branch_id:
            query = query.filter(WmBusinessHoliday.branch_id == branch_id)
        if from_date:
            query = query.filter(WmBusinessHoliday.holiday_date >= from_date)
        if to_date:
            query = query.filter(WmBusinessHoliday.holiday_date <= to_date)
        rows = query.order_by(WmBusinessHoliday.holiday_date.asc()).all()
        return {"status": "success", "rows": [{"holiday_id": r.holiday_id, "holiday_name": r.name, "holiday_date": r.holiday_date} for r in rows]}

    # ---------- Settings ----------
    def upsert_settings(self, payload: SettingsUpsertRequest) -> dict:
        row = self.db.query(WmManManagementSetting).filter(WmManManagementSetting.company_id == payload.company_id).first()
        if not row:
            setting_id = int((self.db.query(func.max(WmManManagementSetting.setting_id)).scalar() or 0) + 1)
            row = WmManManagementSetting(setting_id=setting_id, company_id=payload.company_id, created_by=payload.updated_by)
            self.db.add(row)
        for field, value in payload.model_dump().items():
            if field in {"updated_by"}:
                continue
            setattr(row, field, value)
        row.updated_by = payload.updated_by
        row.updated_at = datetime.utcnow()
        self.db.commit()
        return {"status": "success", "setting_id": row.setting_id}

    def _get_settings(self, company_id: int | None = None) -> WmManManagementSetting:
        row = self.db.query(WmManManagementSetting).filter(WmManManagementSetting.company_id == company_id).first()
        if row:
            return row
        return WmManManagementSetting(
            setting_id=0,
            company_id=company_id,
            timesheet_mandatory_for_completion=True,
            mandatory_task_completion_for_billing=True,
            manager_approval_mandatory_for_timesheet=False,
            job_completion_approval_required=False,
            max_attachment_size_mb=10,
            allowed_attachment_types="pdf,jpg,jpeg,png",
            overtime_allowed=True,
            multiple_timesheets_per_day=True,
            billable_amount_editable_after_completion=False,
            delete_allowed_after_timesheet_entry=False,
            expense_approval_required=False,
            reimbursement_approval_required=False,
            created_by=0,
        )

    # ---------- Job Management ----------
    def create_job(self, payload: JobUpsertRequest) -> dict:
        self._validate_job_payload(payload)
        job_id = int((self.db.query(func.max(WmJob.job_id)).scalar() or 0) + 1)
        job_no = f"JOB-{job_id:06d}"
        row = WmJob(
            job_id=job_id,
            job_no=job_no,
            job_name=payload.job_name,
            customer_id=payload.client_id or 0,
            client_name=payload.client_name,
            service_id=payload.service_id,
            company_id=payload.company_id,
            branch_id=payload.branch_id,
            department_id=payload.department_id,
            start_date=payload.start_date,
            due_date=payload.due_date,
            estimated_amount=payload.amount,
            is_billable=payload.billable_flag,
            planned_hours=payload.expected_hours,
            planned_minutes=payload.expected_minutes,
            manager_id=payload.manager_id,
            assigned_manager_id=payload.manager_id,
            assigned_manager_name=payload.manager_name,
            assigned_employee_id=payload.assigned_employee_id,
            assigned_employee_name=payload.assigned_employee_name,
            remarks=payload.remarks,
            parent_task_id=payload.parent_task_id,
            priority=payload.priority,
            execution_status="Pending",
            billing_status="Not Billable" if not payload.billable_flag else "Pending",
            created_by=payload.created_by,
        )
        self.db.add(row)
        self._audit("JOB_CREATE", row.job_id, payload.created_by, f"job_no={job_no}")
        self.db.commit()
        return {"status": "success", "job_id": row.job_id, "job_no": row.job_no}

    def edit_job(self, job_id: int, payload: JobUpsertRequest) -> dict:
        job = self._job(job_id)
        self._validate_job_payload(payload)
        immutable = {"job_no": job.job_no}
        for key, value in payload.model_dump().items():
            if key in {"created_by"}:
                continue
            mapped = {
                "client_id": "customer_id",
                "amount": "estimated_amount",
                "billable_flag": "is_billable",
                "expected_hours": "planned_hours",
                "expected_minutes": "planned_minutes",
                "job_name": "job_name",
            }.get(key, key)
            if hasattr(job, mapped):
                setattr(job, mapped, value)
        job.updated_by = payload.created_by
        job.updated_on = datetime.utcnow()
        self._audit("JOB_EDIT", job_id, payload.created_by, f"immutable={immutable}")
        self.db.commit()
        return {"status": "success", "job_id": job_id}

    def copy_job(self, job_id: int, created_by: int = 1, include_task_lines: bool = True) -> dict:
        old = self._job(job_id)
        cloned = JobUpsertRequest(
            job_name=f"{old.job_name} (Copy)",
            client_id=old.customer_id,
            client_name=old.client_name,
            service_id=old.service_id,
            priority=old.priority or "Medium",
            company_id=old.company_id,
            branch_id=old.branch_id,
            department_id=old.department_id,
            start_date=old.start_date,
            due_date=old.due_date,
            amount=Decimal(str(old.estimated_amount or 0)),
            billable_flag=bool(old.is_billable),
            expected_hours=Decimal(str(old.planned_hours or 0)),
            expected_minutes=int(old.planned_minutes or 0),
            manager_id=old.manager_id,
            manager_name=old.assigned_manager_name,
            assigned_employee_id=old.assigned_employee_id or 0,
            assigned_employee_name=old.assigned_employee_name,
            remarks=old.remarks,
            parent_task_id=old.parent_task_id,
            created_by=created_by,
        )
        new_job = self.create_job(cloned)
        if include_task_lines:
            lines = self.db.query(WmJobTaskLine).filter(WmJobTaskLine.parent_job_id == job_id).all()
            for ln in lines:
                self.add_job_task_line(
                    JobTaskLineRequest(
                        parent_job_id=new_job["job_id"],
                        task_name=ln.task_name,
                        description=ln.description,
                        assigned_employee_id=ln.assigned_employee_id,
                        planned_start_date=ln.planned_start_date,
                        planned_due_date=ln.planned_due_date,
                        priority=ln.priority,
                        remarks=ln.remarks,
                        sequence_no=ln.sequence_no,
                        dependency_task_id=ln.dependency_task_id,
                        mandatory_flag=ln.mandatory_flag,
                        created_by=created_by,
                    )
                )
        return new_job

    def delete_job(self, job_id: int, deleted_by: int = 1) -> dict:
        job = self._job(job_id)
        settings_row = self._get_settings(job.company_id)
        has_timesheets = (self.db.query(func.count(WmTimesheet.timesheet_id)).filter(WmTimesheet.job_id == job_id).scalar() or 0) > 0
        if has_timesheets and not settings_row.delete_allowed_after_timesheet_entry:
            raise HTTPException(status_code=422, detail="Delete blocked after timesheet entry")
        if job.billing_status in {"Billed", "Ready to Bill"}:
            raise HTTPException(status_code=422, detail="Delete blocked for billed or bill-ready jobs")
        job.is_active = False
        job.execution_status = "Cancelled"
        job.updated_by = deleted_by
        job.updated_on = datetime.utcnow()
        self._audit("JOB_DELETE", job_id, deleted_by, "soft_delete")
        self.db.commit()
        return {"status": "success", "job_id": job_id}

    def view_job(self, job_id: int) -> dict:
        job = self._job(job_id)
        metrics = self._job_metrics(job)
        return {"status": "success", "job": metrics}

    # ---------- Job Task Lines ----------
    def add_job_task_line(self, payload: JobTaskLineRequest) -> dict:
        self._job(payload.parent_job_id)
        line_no = int((self.db.query(func.count(WmJobTaskLine.job_task_id)).filter(WmJobTaskLine.parent_job_id == payload.parent_job_id).scalar() or 0) + 1)
        new_id = int((self.db.query(func.max(WmJobTaskLine.job_task_id)).scalar() or 0) + 1)
        row = WmJobTaskLine(
            job_task_id=new_id,
            parent_job_id=payload.parent_job_id,
            line_no=line_no,
            task_name=payload.task_name,
            description=payload.description,
            assigned_employee_id=payload.assigned_employee_id,
            planned_start_date=payload.planned_start_date,
            planned_due_date=payload.planned_due_date,
            status="Pending",
            priority=payload.priority,
            remarks=payload.remarks,
            sequence_no=payload.sequence_no,
            dependency_task_id=payload.dependency_task_id,
            mandatory_flag=payload.mandatory_flag,
            created_by=payload.created_by,
        )
        self.db.add(row)
        self._refresh_job_progress(payload.parent_job_id)
        self._audit("JOB_TASK_ADD", new_id, payload.created_by, f"job_id={payload.parent_job_id};line_no={line_no}")
        self.db.commit()
        return {"status": "success", "job_task_id": new_id}

    def update_job_task_status(self, job_task_id: int, payload: JobTaskStatusRequest) -> dict:
        row = self.db.query(WmJobTaskLine).filter(WmJobTaskLine.job_task_id == job_task_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Job task line not found")
        row.status = payload.status
        row.updated_by = payload.updated_by
        row.updated_at = datetime.utcnow()
        if payload.status == "Completed":
            row.completed_at = datetime.utcnow()
            row.completed_by = payload.updated_by
        self._refresh_job_progress(row.parent_job_id)
        self._audit("JOB_TASK_STATUS", job_task_id, payload.updated_by, f"status={payload.status}")
        self.db.commit()
        return {"status": "success", "job_task_id": job_task_id, "status_code": payload.status}

    # ---------- Timesheets + Expense + Reimbursement ----------
    def add_timesheet(self, payload: TimesheetEntryRequest) -> dict:
        job = self._job(payload.job_id)
        self._validate_employee(payload.employee_id)
        settings_row = self._get_settings(job.company_id)
        if payload.start_time and payload.end_time and payload.end_time < payload.start_time:
            raise HTTPException(status_code=422, detail="end_time cannot be before start_time")
        if payload.job_task_id:
            task_line = self.db.query(WmJobTaskLine).filter(WmJobTaskLine.job_task_id == payload.job_task_id, WmJobTaskLine.parent_job_id == payload.job_id).first()
            if not task_line:
                raise HTTPException(status_code=422, detail="Invalid job_task_id for selected job")

        if not settings_row.multiple_timesheets_per_day:
            existing = self.db.query(WmTimesheet).filter(and_(WmTimesheet.job_id == payload.job_id, WmTimesheet.emp_id == payload.employee_id, WmTimesheet.work_date == payload.date, WmTimesheet.is_active.is_(True))).first()
            if existing:
                raise HTTPException(status_code=422, detail="Multiple timesheets per day not allowed")

        total_minutes = int(Decimal(str(payload.spent_hours)) * 60) + int(payload.spent_minutes)
        if total_minutes < 0:
            raise HTTPException(status_code=422, detail="spent time cannot be negative")

        ts_id = int((self.db.query(func.max(WmTimesheet.timesheet_id)).scalar() or 0) + 1)
        ts = WmTimesheet(
            timesheet_id=ts_id,
            company_id=job.company_id,
            branch_id=job.branch_id,
            department_id=job.department_id,
            customer_id=job.customer_id,
            job_id=job.job_id,
            task_id=job.parent_task_id,
            emp_id=payload.employee_id,
            work_date=payload.date,
            start_time=payload.start_time,
            end_time=payload.end_time,
            spent_minutes=total_minutes,
            hours=(Decimal(total_minutes) / Decimal(60)).quantize(Decimal("0.01")),
            billable_hours=(Decimal(total_minutes) / Decimal(60)).quantize(Decimal("0.01")) if job.is_billable else Decimal("0"),
            remarks=payload.remarks,
            approval_status="Pending" if settings_row.manager_approval_mandatory_for_timesheet else "Approved",
            created_by=payload.created_by,
        )
        self.db.add(ts)

        expense_total = Decimal("0")
        reimbursement_total = Decimal("0")
        for line in payload.expense_lines:
            amount = Decimal(str(line.get("amount", 0)))
            if amount < 0:
                raise HTTPException(status_code=422, detail="expense amount cannot be negative")
            expense_total += amount
            new_id = int((self.db.query(func.max(WmTimesheetExpenseLine.expense_line_id)).scalar() or 0) + 1)
            self.db.add(WmTimesheetExpenseLine(expense_line_id=new_id, timesheet_id=ts_id, description=str(line.get("description", "Expense")), amount=amount, created_by=payload.created_by))

        for line in payload.reimbursement_lines:
            amount = Decimal(str(line.get("amount", 0)))
            if amount < 0:
                raise HTTPException(status_code=422, detail="reimbursement amount cannot be negative")
            reimbursement_total += amount
            new_id = int((self.db.query(func.max(WmTimesheetReimbursementLine.reimbursement_line_id)).scalar() or 0) + 1)
            self.db.add(WmTimesheetReimbursementLine(reimbursement_line_id=new_id, timesheet_id=ts_id, description=str(line.get("description", "Reimbursement")), amount=amount, created_by=payload.created_by))

        ts.expense_total = expense_total
        ts.reimbursement_total = reimbursement_total
        self._recalculate_job_costing(job.job_id)
        self._refresh_job_progress(job.job_id)
        self._audit("TIMESHEET_ADD", ts_id, payload.created_by, f"job_id={payload.job_id};minutes={total_minutes}")
        self.db.commit()
        return {"status": "success", "timesheet_id": ts_id, "approval_status": ts.approval_status}

    # ---------- Approvals ----------
    def approval_action(self, payload: ApprovalActionRequest) -> dict:
        if payload.action == "REQUEST":
            approval_id = int((self.db.query(func.max(WmManApproval.approval_id)).scalar() or 0) + 1)
            row = WmManApproval(
                approval_id=approval_id,
                entity_type=payload.entity_type,
                entity_id=payload.entity_id,
                approval_type=payload.approval_type,
                current_status="Pending",
                requested_by=payload.user_id,
                remarks=payload.remarks,
            )
            self.db.add(row)
            self._audit("APPROVAL_REQUEST", approval_id, payload.user_id, f"entity={payload.entity_type}:{payload.entity_id}")
            self.db.commit()
            return {"status": "success", "approval_id": approval_id, "current_status": "Pending"}

        row = self.db.query(WmManApproval).filter(WmManApproval.entity_type == payload.entity_type, WmManApproval.entity_id == payload.entity_id, WmManApproval.approval_type == payload.approval_type).order_by(WmManApproval.approval_id.desc()).first()
        if not row:
            raise HTTPException(status_code=404, detail="Approval request not found")

        if payload.action == "APPROVE":
            row.current_status = "Approved"
            row.approved_by = payload.user_id
            row.approved_at = datetime.utcnow()
        elif payload.action == "REJECT":
            row.current_status = "Rejected"
            row.rejected_by = payload.user_id
            row.rejected_at = datetime.utcnow()
        else:
            row.current_status = "Returned"
        row.remarks = payload.remarks
        self._audit("APPROVAL_ACTION", row.approval_id, payload.user_id, f"action={payload.action}")
        self.db.commit()
        return {"status": "success", "approval_id": row.approval_id, "current_status": row.current_status}

    # ---------- Billing Readiness + Billing ----------
    def billing_readiness(self, job_id: int) -> dict:
        job = self._job(job_id)
        settings_row = self._get_settings(job.company_id)
        reasons = []
        if not job.is_billable:
            reasons.append("billable flag = no")
        if job.is_billable and (not job.customer_id or job.customer_id == 0):
            reasons.append("client missing")
        if job.is_billable and Decimal(str(job.estimated_amount or 0)) <= 0:
            reasons.append("amount missing if required")

        if settings_row.mandatory_task_completion_for_billing:
            pending_mandatory = self.db.query(func.count(WmJobTaskLine.job_task_id)).filter(WmJobTaskLine.parent_job_id == job_id, WmJobTaskLine.mandatory_flag.is_(True), WmJobTaskLine.status != "Completed").scalar() or 0
            if pending_mandatory > 0:
                reasons.append("mandatory job tasks incomplete")

        if settings_row.timesheet_mandatory_for_completion:
            ts_count = self.db.query(func.count(WmTimesheet.timesheet_id)).filter(WmTimesheet.job_id == job_id, WmTimesheet.is_active.is_(True)).scalar() or 0
            if ts_count == 0:
                reasons.append("timesheet missing")

        if settings_row.manager_approval_mandatory_for_timesheet:
            pending_approvals = self.db.query(func.count(WmTimesheet.timesheet_id)).filter(WmTimesheet.job_id == job_id, WmTimesheet.approval_status != "Approved", WmTimesheet.is_active.is_(True)).scalar() or 0
            if pending_approvals > 0:
                reasons.append("approval pending")

        ready = len(reasons) == 0
        job.billing_status = "Ready to Bill" if ready else ("Not Billable" if not job.is_billable else "Blocked")
        self.db.commit()
        return {
            "status": "success",
            "job_id": job_id,
            "billing_ready_flag": ready,
            "billing_block_reason": None if ready else "; ".join(reasons),
        }

    def mark_billed(self, payload: BillingActionRequest) -> dict:
        job = self._job(payload.job_id)
        readiness = self.billing_readiness(payload.job_id)
        if not readiness["billing_ready_flag"]:
            raise HTTPException(status_code=422, detail="billed status cannot be set unless billing_ready_flag = true")
        if payload.billed_amount < 0:
            raise HTTPException(status_code=422, detail="amount cannot be negative")
        job.billed_amount = payload.billed_amount
        job.billing_status = "Billed"
        job.execution_status = "Billed"
        job.billed_at = datetime.utcnow()
        job.billed_by = payload.billed_by
        self._audit("JOB_BILLED", job.job_id, payload.billed_by, f"amount={payload.billed_amount}")
        self.db.commit()
        return {"status": "success", "job_id": job.job_id, "billing_status": job.billing_status}

    # ---------- Registers / Reports / Dashboards ----------
    def job_register(self, **filters) -> dict:
        jobs = self.db.query(WmJob).filter(WmJob.is_active.is_(True))
        for field in ["company_id", "branch_id", "department_id", "customer_id", "manager_id", "assigned_employee_id", "priority", "billing_status", "execution_status"]:
            value = filters.get(field)
            if value is not None:
                jobs = jobs.filter(getattr(WmJob, field) == value)
        if filters.get("billable_flag") is not None:
            jobs = jobs.filter(WmJob.is_billable.is_(bool(filters["billable_flag"])))
        if filters.get("due_from"):
            jobs = jobs.filter(WmJob.due_date >= filters["due_from"])
        if filters.get("due_to"):
            jobs = jobs.filter(WmJob.due_date <= filters["due_to"])

        rows = [self._job_metrics(x) for x in jobs.order_by(WmJob.job_id.desc()).all()]
        return {"status": "success", "rows": rows}

    def timesheet_register(self, **filters) -> dict:
        query = self.db.query(WmTimesheet).filter(WmTimesheet.is_active.is_(True))
        for field in ["company_id", "branch_id", "department_id", "emp_id", "job_id", "approval_status"]:
            value = filters.get(field)
            if value is not None:
                query = query.filter(getattr(WmTimesheet, field) == value)
        if filters.get("date_from"):
            query = query.filter(WmTimesheet.work_date >= filters["date_from"])
        if filters.get("date_to"):
            query = query.filter(WmTimesheet.work_date <= filters["date_to"])

        rows = query.order_by(WmTimesheet.timesheet_id.desc()).all()
        return {"status": "success", "rows": [{"timesheet_id": r.timesheet_id, "job_id": r.job_id, "employee_id": r.emp_id, "date": r.work_date, "total_spent_minutes": r.spent_minutes, "expense_total": r.expense_total, "reimbursement_total": r.reimbursement_total, "approval_status": r.approval_status} for r in rows]}

    def dashboard(self, manager_id: int | None = None, employee_id: int | None = None) -> dict:
        jobs = self.db.query(WmJob).filter(WmJob.is_active.is_(True))
        if manager_id:
            jobs = jobs.filter(WmJob.manager_id == manager_id)
        if employee_id:
            jobs = jobs.filter(WmJob.assigned_employee_id == employee_id)
        rows = jobs.all()
        total_expected_minutes = sum(int((Decimal(str(x.planned_hours or 0)) * 60) + Decimal(str(x.planned_minutes or 0))) for x in rows)
        total_actual_minutes = sum(int(x.spent_hours or 0) * 60 for x in rows)
        total_internal_cost = sum(Decimal(str(x.final_cost_to_company or 0)) for x in rows)
        total_billable_amount = sum(Decimal(str(x.estimated_amount or 0)) for x in rows if x.is_billable)
        total_recovery = sum(Decimal(str(x.billed_amount or 0)) for x in rows)
        return {
            "status": "success",
            "total_jobs": len(rows),
            "pending_jobs": sum(1 for x in rows if x.execution_status in {"Draft", "Pending", "In Progress"}),
            "completed_jobs": sum(1 for x in rows if x.execution_status == "Completed"),
            "billed_jobs": sum(1 for x in rows if x.billing_status == "Billed"),
            "overdue_jobs": sum(1 for x in rows if x.due_date and x.execution_status not in {"Completed", "Billed", "Closed", "Cancelled"} and x.due_date < datetime.utcnow().date()),
            "critical_jobs": sum(1 for x in rows if x.critical_flag),
            "billing_ready_jobs": sum(1 for x in rows if x.billing_status == "Ready to Bill"),
            "billing_blocked_jobs": sum(1 for x in rows if x.billing_status == "Blocked"),
            "total_expected_hours": round(total_expected_minutes / 60, 2),
            "total_actual_hours": round(total_actual_minutes / 60, 2),
            "total_internal_cost": str(total_internal_cost),
            "total_billable_amount": str(total_billable_amount),
            "total_recovery": str(total_recovery),
            "total_margin_or_loss": str(total_recovery - total_internal_cost),
        }

    # ---------- Helpers ----------
    def _job(self, job_id: int) -> WmJob:
        row = self.db.query(WmJob).filter(WmJob.job_id == job_id, WmJob.is_active.is_(True)).first()
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")
        return row

    def _validate_employee(self, emp_id: int) -> None:
        employee = self.db.query(RefEmployee).filter(RefEmployee.emp_id == emp_id, RefEmployee.is_active.is_(True)).first()
        if not employee:
            raise HTTPException(status_code=422, detail="employee required before execution")

    def _validate_job_payload(self, payload: JobUpsertRequest) -> None:
        if not payload.job_name.strip():
            raise HTTPException(status_code=422, detail="job name required")
        if payload.billable_flag and not payload.client_id:
            raise HTTPException(status_code=422, detail="client required if billable")
        if payload.company_id is None:
            raise HTTPException(status_code=422, detail="company required")
        if payload.due_date < payload.start_date:
            raise HTTPException(status_code=422, detail="due date cannot be before start date")
        if payload.amount < 0:
            raise HTTPException(status_code=422, detail="amount cannot be negative")
        self._validate_employee(payload.assigned_employee_id)

    def _refresh_job_progress(self, job_id: int) -> None:
        job = self._job(job_id)
        lines = self.db.query(WmJobTaskLine).filter(WmJobTaskLine.parent_job_id == job_id).all()
        if lines:
            completed = sum(1 for x in lines if x.status == "Completed")
            progress = (Decimal(completed) * Decimal("100") / Decimal(len(lines))).quantize(Decimal("0.01"))
            job.progress_percent = progress
            if completed == len(lines):
                settings_row = self._get_settings(job.company_id)
                if settings_row.timesheet_mandatory_for_completion:
                    ts_count = self.db.query(func.count(WmTimesheet.timesheet_id)).filter(WmTimesheet.job_id == job_id, WmTimesheet.is_active.is_(True)).scalar() or 0
                    if ts_count == 0:
                        job.execution_status = "In Progress"
                    else:
                        job.execution_status = "Completed"
                else:
                    job.execution_status = "Completed"
            else:
                job.execution_status = "In Progress" if completed > 0 else "Pending"
        else:
            job.execution_status = "Pending"
            job.progress_percent = Decimal("0")

        if job.due_date and job.execution_status not in {"Completed", "Billed", "Closed", "Cancelled"} and job.due_date < datetime.utcnow().date():
            job.critical_flag = True
            if job.execution_status == "Pending":
                job.execution_status = "Critical"

    def _recalculate_job_costing(self, job_id: int) -> None:
        job = self._job(job_id)
        ts_rows = self.db.query(WmTimesheet).filter(WmTimesheet.job_id == job_id, WmTimesheet.is_active.is_(True)).all()
        labor_cost = Decimal("0")
        expense_cost = Decimal("0")
        reimbursement_cost = Decimal("0")
        actual_minutes = 0

        for ts in ts_rows:
            emp = self.db.query(RefEmployee).filter(RefEmployee.emp_id == ts.emp_id, RefEmployee.is_active.is_(True)).first()
            hourly = Decimal(str(emp.hourly_cost if emp and emp.hourly_cost is not None else (Decimal(str(emp.monthly_ctc)) / Decimal(settings.working_hours_per_month) if emp else 0)))
            hours = Decimal(str(ts.hours or 0))
            labor_cost += hours * hourly
            expense_cost += Decimal(str(ts.expense_total or 0))
            reimbursement_cost += Decimal(str(ts.reimbursement_total or 0))
            actual_minutes += int(ts.spent_minutes or 0)

        total_internal = labor_cost + expense_cost + reimbursement_cost
        job.spent_hours = (Decimal(actual_minutes) / Decimal(60)).quantize(Decimal("0.01"))
        job.cost_to_company = labor_cost.quantize(Decimal("0.01"))
        job.overhead_amount = (labor_cost * Decimal("0.10")).quantize(Decimal("0.01"))
        job.final_cost_to_company = (total_internal + job.overhead_amount).quantize(Decimal("0.01"))
        job.profit_or_loss = (Decimal(str(job.billed_amount or 0)) - job.final_cost_to_company).quantize(Decimal("0.01"))

    def _job_metrics(self, job: WmJob) -> dict:
        expected_minutes = int((Decimal(str(job.planned_hours or 0)) * 60) + Decimal(str(job.planned_minutes or 0)))
        actual_minutes = int(Decimal(str(job.spent_hours or 0)) * 60)
        variance = actual_minutes - expected_minutes
        if variance < 0:
            variance_status = "Under"
        elif variance == 0:
            variance_status = "Equal"
        else:
            variance_status = "Over"
        return {
            "job_id": job.job_id,
            "job_no": job.job_no,
            "job_name": job.job_name,
            "status": job.execution_status,
            "billing_status": job.billing_status,
            "priority": job.priority,
            "manager_id": job.manager_id,
            "assigned_employee_id": job.assigned_employee_id,
            "billable_flag": bool(job.is_billable),
            "expected_minutes": expected_minutes,
            "actual_minutes": actual_minutes,
            "variance_minutes": variance,
            "variance_status": variance_status,
            "progress_percent": str(job.progress_percent or 0),
            "final_cost_to_company": str(job.final_cost_to_company or 0),
            "billed_amount": str(job.billed_amount or 0),
            "gross_margin": str((Decimal(str(job.billed_amount or 0)) - Decimal(str(job.final_cost_to_company or 0))).quantize(Decimal("0.01"))),
            "critical_flag": bool(job.critical_flag),
        }

    def _audit(self, action: str, entity_id: int, user_id: int, details: str):
        self.db.add(TaskAuditLog(entity_name="man_management", entity_id=entity_id, action=action, details=details, created_by=user_id))
