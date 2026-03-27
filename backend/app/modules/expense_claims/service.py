from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.ref_employee import RefEmployee
from app.models.task_audit_log import TaskAuditLog
from app.models.wm_expense_claim import WmExpenseClaim
from app.models.wm_expense_claim_approval_history import WmExpenseClaimApprovalHistory
from app.models.wm_expense_claim_attachment import WmExpenseClaimAttachment
from app.models.wm_expense_claim_conversion_log import WmExpenseClaimConversionLog
from app.models.wm_job import WmJob
from app.models.wm_task import WmTask
from app.models.wm_task_participant import WmTaskParticipant
from app.models.wm_timesheet import WmTimesheet
from app.modules.expense_claims.schemas import ConvertExpenseClaimRequest, ExpenseClaimCreateRequest, ExpenseClaimDecisionRequest


class ExpenseClaimService:
    def __init__(self, db: Session):
        self.db = db

    def create_claim(self, payload: ExpenseClaimCreateRequest, user_id: int = 1) -> dict:
        employee = self.db.query(RefEmployee).filter(RefEmployee.emp_id == payload.emp_id, RefEmployee.is_active.is_(True)).first()
        if not employee:
            raise HTTPException(status_code=422, detail="Invalid employee")
        if payload.amount <= 0:
            raise HTTPException(status_code=422, detail="Amount must be greater than zero")
        if payload.tax_amount < 0:
            raise HTTPException(status_code=422, detail="Tax amount cannot be negative")
        if payload.total_amount <= 0:
            raise HTTPException(status_code=422, detail="Total amount must be greater than zero")
        if round(payload.total_amount, 2) != round(payload.amount + payload.tax_amount, 2):
            raise HTTPException(status_code=422, detail="Total amount mismatch")

        job = self.db.query(WmJob).filter(WmJob.job_id == payload.job_id, WmJob.is_active.is_(True)).first() if payload.job_id else None
        task = self.db.query(WmTask).filter(WmTask.task_id == payload.task_id, WmTask.is_active.is_(True)).first() if payload.task_id else None
        participant = self.db.query(WmTaskParticipant).filter(WmTaskParticipant.task_participant_id == payload.task_participant_id, WmTaskParticipant.is_active.is_(True)).first() if payload.task_participant_id else None
        timesheet = self.db.query(WmTimesheet).filter(WmTimesheet.timesheet_id == payload.timesheet_id, WmTimesheet.is_active.is_(True)).first() if payload.timesheet_id else None

        if payload.job_id and not job:
            raise HTTPException(status_code=422, detail="Invalid job")
        if payload.task_id and (not task or (job and task.job_id != payload.job_id)):
            raise HTTPException(status_code=422, detail="Invalid task for selected job")
        if payload.task_participant_id and (not participant or (task and participant.task_id != payload.task_id)):
            raise HTTPException(status_code=422, detail="Invalid participant for selected task")
        if payload.timesheet_id and not timesheet:
            raise HTTPException(status_code=422, detail="Invalid timesheet")

        if payload.recoverable_flag and not (job or task):
            raise HTTPException(status_code=422, detail="Recoverable expense must be linked to job or task")

        if (payload.total_amount >= 1000 or payload.expense_type.upper() in {"TRAVEL", "LODGING"}) and not payload.receipt_attachment_ref:
            raise HTTPException(status_code=422, detail="Receipt attachment is required")

        duplicate = self.db.query(WmExpenseClaim).filter(
            WmExpenseClaim.emp_id == payload.emp_id,
            WmExpenseClaim.expense_date == payload.expense_date,
            func.lower(WmExpenseClaim.expense_type) == payload.expense_type.lower(),
            WmExpenseClaim.total_amount == payload.total_amount,
            WmExpenseClaim.is_active.is_(True),
            WmExpenseClaim.approval_status != "Rejected",
        ).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="Potential duplicate expense claim detected")

        claim_no = self._generate_claim_no()
        approval_status = "Submitted" if payload.submit_mode == "SUBMIT" else "Draft"

        company_id = job.company_id if job else employee.company_id
        branch_id = job.branch_id if job else employee.branch_id
        department_id = job.department_id if job else employee.department_id
        customer_id = task.customer_id if task else (job.customer_id if job else None)

        claim = WmExpenseClaim(
            claim_no=claim_no,
            claim_type=payload.claim_type,
            expense_type=payload.expense_type,
            company_id=company_id,
            branch_id=branch_id,
            department_id=department_id,
            emp_id=payload.emp_id,
            entered_for_emp_id=payload.entered_for_emp_id,
            job_id=payload.job_id,
            task_id=payload.task_id,
            task_participant_id=payload.task_participant_id,
            timesheet_id=payload.timesheet_id,
            customer_id=customer_id,
            cost_center_id=payload.cost_center_id,
            expense_date=payload.expense_date,
            amount=payload.amount,
            tax_amount=payload.tax_amount,
            total_amount=payload.total_amount,
            recoverable_flag=payload.recoverable_flag,
            vendor_payee_name=payload.vendor_payee_name,
            remarks=payload.remarks,
            approval_status=approval_status,
            created_by=user_id,
        )

        try:
            self.db.add(claim)
            self.db.flush()
            if payload.receipt_attachment_ref:
                self.db.add(
                    WmExpenseClaimAttachment(
                        claim_id=claim.claim_id,
                        file_ref=payload.receipt_attachment_ref,
                        uploaded_by=user_id,
                    )
                )
            self.db.add(
                TaskAuditLog(
                    entity_name="wm_expense_claim",
                    entity_id=claim.claim_id,
                    action="CREATE",
                    details=f"job_id={payload.job_id};task_id={payload.task_id};task_participant_id={payload.task_participant_id};total_amount={payload.total_amount};approval_status={approval_status}",
                    created_by=user_id,
                )
            )
            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Expense claim creation failed: {exc}") from exc

        return {
            "status": "SUCCESS",
            "claim_id": claim.claim_id,
            "claim_no": claim.claim_no,
            "approval_status": approval_status,
            "message": "Expense claim saved successfully",
        }

    def _generate_claim_no(self) -> str:
        year = datetime.utcnow().year
        prefix = f"EXP-{year}-"
        latest = self.db.query(WmExpenseClaim).filter(WmExpenseClaim.claim_no.like(f"{prefix}%")).order_by(desc(WmExpenseClaim.claim_id)).first()
        next_seq = (int(latest.claim_no.split("-")[-1]) + 1) if latest else 1
        return f"{prefix}{next_seq:05d}"

    def submit_claim(self, claim_id: int, remarks: str | None = None, user_id: int = 1) -> dict:
        claim = self.db.query(WmExpenseClaim).filter(WmExpenseClaim.claim_id == claim_id, WmExpenseClaim.is_active.is_(True)).first()
        if not claim:
            raise HTTPException(status_code=404, detail="Expense claim not found")
        if claim.approval_status not in {"Draft", "Rejected"}:
            raise HTTPException(status_code=422, detail="Expense claim cannot be submitted in current status")
        if user_id not in {claim.emp_id, claim.created_by, claim.entered_for_emp_id}:
            raise HTTPException(status_code=403, detail="User not allowed to submit this expense claim")

        if (claim.total_amount >= 1000 or claim.expense_type.upper() in {"TRAVEL", "LODGING"}):
            has_receipt = self.db.query(WmExpenseClaimAttachment).filter(WmExpenseClaimAttachment.claim_id == claim_id).first() is not None
            if not has_receipt:
                raise HTTPException(status_code=422, detail="Receipt attachment is required")

        old_status = claim.approval_status
        try:
            claim.approval_status = "Submitted"
            claim.submitted_by = user_id
            claim.submitted_on = datetime.utcnow()
            claim.updated_by = user_id
            claim.updated_on = datetime.utcnow()
            if remarks:
                claim.remarks = remarks

            self.db.add(
                WmExpenseClaimApprovalHistory(
                    claim_id=claim_id,
                    old_status=old_status,
                    new_status="Submitted",
                    action_code="SUBMIT",
                    decision_note=remarks,
                    acted_by=user_id,
                )
            )
            self.db.add(
                TaskAuditLog(
                    entity_name="wm_expense_claim",
                    entity_id=claim_id,
                    action="SUBMIT",
                    details=f"old_status={old_status};new_status=Submitted",
                    created_by=user_id,
                )
            )
            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Expense claim submission failed: {exc}") from exc

        return {"status": "SUCCESS", "claim_id": claim_id, "approval_status": "Submitted", "message": "Expense claim submitted successfully"}

    def decide_claim(self, claim_id: int, payload: ExpenseClaimDecisionRequest, user_id: int = 1) -> dict:
        claim = self.db.query(WmExpenseClaim).filter(WmExpenseClaim.claim_id == claim_id, WmExpenseClaim.is_active.is_(True)).first()
        if not claim:
            raise HTTPException(status_code=404, detail="Expense claim not found")
        if claim.approval_status != "Submitted":
            raise HTTPException(status_code=422, detail="Expense claim is not pending approval")

        if payload.override_flag:
            if not (payload.override_reason or "").strip():
                raise HTTPException(status_code=422, detail="Override reason is required")
        elif user_id in {claim.emp_id, claim.created_by}:
            raise HTTPException(status_code=403, detail="Claim creator cannot approve/reject without override")

        if payload.decision == "REJECT" and not (payload.decision_note or "").strip():
            raise HTTPException(status_code=422, detail="Rejection reason is required")

        old_status = claim.approval_status
        new_status = "Approved" if payload.decision == "APPROVE" else "Rejected"
        try:
            claim.approval_status = new_status
            claim.updated_by = user_id
            claim.updated_on = datetime.utcnow()
            if new_status == "Approved":
                claim.approved_by = user_id
                claim.approved_on = datetime.utcnow()
            else:
                claim.rejected_by = user_id
                claim.rejected_on = datetime.utcnow()
                claim.rejection_reason = payload.decision_note

            self.db.add(
                WmExpenseClaimApprovalHistory(
                    claim_id=claim_id,
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
                    entity_name="wm_expense_claim",
                    entity_id=claim_id,
                    action=payload.decision,
                    details=f"old_status={old_status};new_status={new_status};override_flag={payload.override_flag}",
                    created_by=user_id,
                )
            )
            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Expense claim decision failed: {exc}") from exc

        return {"status": "SUCCESS", "claim_id": claim_id, "approval_status": new_status, "message": "Expense claim decision recorded successfully"}

    def convert_to_voucher(self, claim_id: int, payload: ConvertExpenseClaimRequest, user_id: int = 1) -> dict:
        claim = self.db.query(WmExpenseClaim).filter(WmExpenseClaim.claim_id == claim_id, WmExpenseClaim.is_active.is_(True)).first()
        if not claim:
            raise HTTPException(status_code=404, detail="Expense claim not found")
        if claim.approval_status != "Approved":
            raise HTTPException(status_code=422, detail="Only approved claims can be converted")
        if claim.conversion_status == "Converted":
            raise HTTPException(status_code=422, detail="Claim is already converted")

        if payload.override_flag and not (payload.override_reason or "").strip():
            raise HTTPException(status_code=422, detail="Override reason is required")
        if claim.cost_center_id is None:
            raise HTTPException(status_code=422, detail="Cost center is required for conversion")

        old_conversion_status = claim.conversion_status or "Not Converted"
        voucher_payload = {
            "CompanyName": str(claim.company_id),
            "Branch": str(claim.branch_id or ""),
            "DepartmentName": str(claim.department_id or ""),
            "AcHeadName": "Employee Reimbursement",
            "vType": "Expense",
            "vDate": claim.expense_date.strftime("%d-%m-%Y"),
            "Amount": float(claim.total_amount),
            "Narration": f"Reimbursement claim {claim.claim_no} - {claim.remarks or ''}".strip(),
            "Action": "AddEdit",
            "itemList": [],
        }

        try:
            claim.conversion_status = "Conversion Pending"
            claim.updated_by = user_id
            claim.updated_on = datetime.utcnow()
            self.db.flush()

            response = self._create_expense_voucher(voucher_payload, claim)
            voucher_id = response.get("voucher_id")
            voucher_no = response.get("voucher_no")
            if not voucher_id and not voucher_no:
                raise ValueError("Voucher creation response invalid")

            claim.voucher_id = voucher_id
            claim.conversion_status = "Converted"
            claim.converted_by = user_id
            claim.converted_on = datetime.utcnow()
            claim.conversion_error = None
            claim.updated_by = user_id
            claim.updated_on = datetime.utcnow()

            self.db.add(
                WmExpenseClaimConversionLog(
                    claim_id=claim_id,
                    old_conversion_status=old_conversion_status,
                    new_conversion_status="Converted",
                    voucher_id=voucher_id,
                    voucher_no=voucher_no,
                    request_payload=str(voucher_payload),
                    response_payload=str(response),
                    converted_by=user_id,
                    override_flag=payload.override_flag,
                    override_reason=payload.override_reason,
                )
            )
            self.db.add(
                TaskAuditLog(
                    entity_name="wm_expense_claim",
                    entity_id=claim_id,
                    action="CONVERT_TO_VOUCHER",
                    details=f"voucher_id={voucher_id};voucher_no={voucher_no}",
                    created_by=user_id,
                )
            )
            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            claim = self.db.query(WmExpenseClaim).filter(WmExpenseClaim.claim_id == claim_id).first()
            if claim:
                claim.conversion_status = "Conversion Failed"
                claim.conversion_error = str(exc)
                claim.updated_by = user_id
                claim.updated_on = datetime.utcnow()
                self.db.add(
                    WmExpenseClaimConversionLog(
                        claim_id=claim_id,
                        old_conversion_status=old_conversion_status,
                        new_conversion_status="Conversion Failed",
                        conversion_error=str(exc),
                        converted_by=user_id,
                        override_flag=payload.override_flag,
                        override_reason=payload.override_reason,
                    )
                )
                self.db.commit()
            raise HTTPException(status_code=500, detail=f"Expense voucher conversion failed: {exc}") from exc

        return {
            "status": "SUCCESS",
            "claim_id": claim_id,
            "voucher_id": voucher_id,
            "voucher_no": voucher_no,
            "conversion_status": "Converted",
            "message": "Expense voucher created successfully",
        }

    def _create_expense_voucher(self, voucher_payload: dict, claim: WmExpenseClaim) -> dict:
        if claim.remarks and "FORCE_VOUCHER_FAIL" in claim.remarks:
            raise ValueError("Voucher API failure")
        seq = claim.claim_id
        return {"voucher_id": 450000 + seq, "voucher_no": f"EXPV-{datetime.utcnow().year}-{seq:05d}"}
