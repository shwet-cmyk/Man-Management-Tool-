from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.ref_employee import RefEmployee
from app.models.task_audit_log import TaskAuditLog
from app.models.wm_job import WmJob
from app.models.wm_task import WmTask
from app.models.wm_task_participant import WmTaskParticipant
from app.models.wm_timesheet import WmTimesheet
from app.models.wm_timesheet_approval_history import WmTimesheetApprovalHistory
from app.modules.timesheets.schemas import TimesheetCreateRequest, TimesheetDecisionRequest


class TimesheetService:
    def __init__(self, db: Session):
        self.db = db

    def create_timesheet(self, payload: TimesheetCreateRequest, user_id: int = 1) -> dict:
        employee = self.db.query(RefEmployee).filter(RefEmployee.emp_id == payload.emp_id, RefEmployee.is_active.is_(True)).first()
        if not employee:
            raise HTTPException(status_code=422, detail="Invalid employee")

        job = self.db.query(WmJob).filter(WmJob.job_id == payload.job_id, WmJob.is_active.is_(True)).first()
        if not job:
            raise HTTPException(status_code=422, detail="Invalid job")

        task = None
        if payload.task_id is not None:
            task = self.db.query(WmTask).filter(WmTask.task_id == payload.task_id, WmTask.is_active.is_(True)).first()
            if not task or task.job_id != payload.job_id:
                raise HTTPException(status_code=422, detail="Invalid task for selected job")
            if task.status_code in {"Closed", "Cancelled", "Archived"}:
                raise HTTPException(status_code=422, detail="Time entry not allowed on task")

        participant = None
        if payload.task_participant_id is not None:
            participant = self.db.query(WmTaskParticipant).filter(
                WmTaskParticipant.task_participant_id == payload.task_participant_id,
                WmTaskParticipant.is_active.is_(True),
            ).first()
            if not participant:
                raise HTTPException(status_code=422, detail="Invalid participant")
            if payload.task_id and participant.task_id != payload.task_id:
                raise HTTPException(status_code=422, detail="Participant does not belong to selected task")
            if participant.emp_id != payload.emp_id and not payload.override_participant_mapping:
                raise HTTPException(status_code=403, detail="Employee is not mapped to this participant stage")
            if participant.participant_status in {"Cancelled", "Completed", "Accepted"}:
                raise HTTPException(status_code=422, detail="Time entry not allowed on participant stage")

        if payload.hours <= 0:
            raise HTTPException(status_code=422, detail="Hours must be greater than zero")
        if payload.billable_hours < 0 or payload.billable_hours > payload.hours:
            raise HTTPException(status_code=422, detail="Invalid billable hours")
        if payload.overtime_hours < 0 or payload.overtime_hours > payload.hours:
            raise HTTPException(status_code=422, detail="Invalid overtime hours")
        if payload.start_time and payload.end_time and payload.end_time <= payload.start_time:
            raise HTTPException(status_code=422, detail="End time must be after start time")

        if payload.start_time and payload.end_time:
            overlap = self.db.query(WmTimesheet).filter(
                WmTimesheet.emp_id == payload.emp_id,
                WmTimesheet.work_date == payload.work_date,
                WmTimesheet.is_active.is_(True),
                WmTimesheet.start_time.is_not(None),
                WmTimesheet.end_time.is_not(None),
                and_(WmTimesheet.start_time < payload.end_time, WmTimesheet.end_time > payload.start_time),
            ).first()
            if overlap:
                raise HTTPException(status_code=409, detail="Overlapping timesheet exists")

        if (not job.is_billable or (task is not None and not task.billable_flag)) and payload.billable_hours > Decimal("0"):
            raise HTTPException(status_code=422, detail="Billable hours are not allowed on non-billable job/task")

        approval_status = "Submitted" if payload.submit_mode == "SUBMIT" else "Draft"
        timesheet = WmTimesheet(
            company_id=job.company_id,
            branch_id=job.branch_id,
            department_id=job.department_id,
            customer_id=job.customer_id,
            job_id=payload.job_id,
            task_id=payload.task_id,
            task_participant_id=payload.task_participant_id,
            emp_id=payload.emp_id,
            work_date=payload.work_date,
            start_time=payload.start_time,
            end_time=payload.end_time,
            hours=payload.hours,
            billable_hours=payload.billable_hours,
            overtime_hours=payload.overtime_hours,
            activity_type=payload.activity_type,
            remarks=payload.remarks,
            attachment_ref=payload.attachment_ref,
            expense_link_id=payload.expense_link_id,
            reimbursement_link_id=payload.reimbursement_link_id,
            approval_status=approval_status,
            entered_for_emp_id=payload.entered_for_emp_id,
            created_by=user_id,
        )

        participant_status_hint = None
        try:
            self.db.add(timesheet)
            self.db.flush()

            if payload.submit_mode == "SUBMIT":
                if participant and participant.participant_status in {"Planned", "Not Started"}:
                    participant.participant_status = "In Progress"
                    participant.updated_by = user_id
                    participant.updated_on = datetime.utcnow()
                    participant_status_hint = "In Progress"
                elif task and task.status_code in {"Open", "Draft"}:
                    task.status_code = "In Progress"
                    task.workflow_state_code = "In Progress"
                    task.updated_by = user_id
                    task.updated_on = datetime.utcnow()
                    participant_status_hint = "In Progress"

            self.db.add(
                TaskAuditLog(
                    entity_name="wm_timesheet",
                    entity_id=timesheet.timesheet_id,
                    action="CREATE",
                    details=f"job_id={payload.job_id};task_id={payload.task_id};task_participant_id={payload.task_participant_id};hours={payload.hours};approval_status={approval_status}",
                    created_by=user_id,
                )
            )
            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Timesheet creation failed: {exc}") from exc

        return {
            "status": "SUCCESS",
            "timesheet_id": timesheet.timesheet_id,
            "approval_status": approval_status,
            "participant_status_hint": participant_status_hint,
            "message": "Timesheet saved successfully",
        }

    def submit_timesheet(self, timesheet_id: int, remarks: str | None = None, user_id: int = 1) -> dict:
        ts = self.db.query(WmTimesheet).filter(WmTimesheet.timesheet_id == timesheet_id, WmTimesheet.is_active.is_(True)).first()
        if not ts:
            raise HTTPException(status_code=404, detail="Timesheet not found")
        if ts.approval_status not in {"Draft", "Rejected"}:
            raise HTTPException(status_code=422, detail="Timesheet cannot be submitted in current status")
        if user_id not in {ts.emp_id, ts.created_by, ts.entered_for_emp_id}:
            raise HTTPException(status_code=403, detail="User not allowed to submit this timesheet")

        old_status = ts.approval_status
        try:
            ts.approval_status = "Submitted"
            ts.submitted_by = user_id
            ts.submitted_on = datetime.utcnow()
            ts.updated_by = user_id
            ts.updated_on = datetime.utcnow()
            if remarks:
                ts.remarks = remarks

            self.db.add(
                WmTimesheetApprovalHistory(
                    timesheet_id=timesheet_id,
                    old_status=old_status,
                    new_status="Submitted",
                    action_code="SUBMIT",
                    decision_note=remarks,
                    acted_by=user_id,
                )
            )
            self.db.add(
                TaskAuditLog(
                    entity_name="wm_timesheet",
                    entity_id=timesheet_id,
                    action="SUBMIT",
                    details=f"old_status={old_status};new_status=Submitted",
                    created_by=user_id,
                )
            )
            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Timesheet submission failed: {exc}") from exc

        return {
            "status": "SUCCESS",
            "timesheet_id": timesheet_id,
            "approval_status": "Submitted",
            "message": "Timesheet submitted successfully",
        }

    def decide_timesheet(self, timesheet_id: int, payload: TimesheetDecisionRequest, user_id: int = 1) -> dict:
        ts = self.db.query(WmTimesheet).filter(WmTimesheet.timesheet_id == timesheet_id, WmTimesheet.is_active.is_(True)).first()
        if not ts:
            raise HTTPException(status_code=404, detail="Timesheet not found")
        if ts.approval_status != "Submitted":
            raise HTTPException(status_code=422, detail="Timesheet is not pending approval")

        is_override = bool(payload.override_flag)
        if is_override:
            if not (payload.override_reason or "").strip():
                raise HTTPException(status_code=422, detail="Override reason is required")
        else:
            if user_id == ts.emp_id:
                raise HTTPException(status_code=403, detail="Timesheet owner cannot approve/reject without override")

        if payload.decision == "REJECT" and not (payload.decision_note or "").strip():
            raise HTTPException(status_code=422, detail="Rejection reason is required")

        old_status = ts.approval_status
        new_status = "Approved" if payload.decision == "APPROVE" else "Rejected"

        try:
            ts.approval_status = new_status
            ts.updated_by = user_id
            ts.updated_on = datetime.utcnow()

            if new_status == "Approved":
                ts.approved_by = user_id
                ts.approved_on = datetime.utcnow()
            else:
                ts.rejected_by = user_id
                ts.rejected_on = datetime.utcnow()
                ts.rejection_reason = payload.decision_note

            self.db.add(
                WmTimesheetApprovalHistory(
                    timesheet_id=timesheet_id,
                    old_status=old_status,
                    new_status=new_status,
                    action_code=payload.decision,
                    decision_note=payload.decision_note,
                    acted_by=user_id,
                    override_flag=payload.override_flag,
                    override_reason=payload.override_reason,
                )
            )
            self.db.add(
                TaskAuditLog(
                    entity_name="wm_timesheet",
                    entity_id=timesheet_id,
                    action=payload.decision,
                    details=f"old_status={old_status};new_status={new_status};override_flag={payload.override_flag}",
                    created_by=user_id,
                )
            )
            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Timesheet decision failed: {exc}") from exc

        return {
            "status": "SUCCESS",
            "timesheet_id": timesheet_id,
            "approval_status": new_status,
            "message": "Timesheet decision recorded successfully",
        }
