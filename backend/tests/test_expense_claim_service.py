from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.models.ref_employee import RefEmployee
from app.models.wm_job import WmJob
from app.models.wm_task import WmTask
from app.models.wm_task_participant import WmTaskParticipant
from app.models.wm_timesheet import WmTimesheet
from app.models.wm_expense_claim import WmExpenseClaim
from app.models.wm_expense_claim_approval_history import WmExpenseClaimApprovalHistory
from app.modules.expense_claims.schemas import ConvertExpenseClaimRequest, ExpenseClaimCreateRequest, ExpenseClaimDecisionRequest
from app.modules.expense_claims.service import ExpenseClaimService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def seed_base(db):
    now = datetime.utcnow()
    db.add(
        RefEmployee(
            emp_id=210,
            employee_name="Emp 210",
            company_id=1,
            branch_id=10,
            department_id=20,
            monthly_ctc=Decimal("100000"),
            hourly_cost=Decimal("625"),
            is_active=True,
            last_synced_at=now,
        )
    )
    db.add(
        WmJob(
            job_id=50021,
            job_no="JOB-2026-001",
            company_id=1,
            branch_id=10,
            department_id=20,
            customer_id=30,
            job_name="Compliance",
            is_billable=True,
            created_by=1,
            execution_status="Open",
            billing_status="Not Billed",
        )
    )
    db.add(
        WmTask(
            task_id=60015,
            task_no="TSK-2026-1",
            company_id=1,
            customer_id=30,
            job_id=50021,
            title="Task",
            task_type="Task",
            priority_code="Medium",
            status_code="Open",
            primary_owner_emp_id=210,
            billable_flag=True,
            billed_amount=Decimal("0"),
            estimated_hours=Decimal("5"),
            planned_start=now,
            due_at=now + timedelta(days=1),
            created_by=210,
            source_type="MANUAL",
        )
    )
    db.add(
        WmTaskParticipant(
            task_participant_id=70011,
            task_id=60015,
            emp_id=210,
            role_code="EXECUTOR",
            planned_start=now,
            planned_due=now + timedelta(days=1),
            created_by=1,
        )
    )
    db.add(
        WmTimesheet(
            timesheet_id=90051,
            company_id=1,
            branch_id=10,
            department_id=20,
            customer_id=30,
            job_id=50021,
            task_id=60015,
            task_participant_id=70011,
            emp_id=210,
            work_date=date(2026, 4, 2),
            hours=Decimal("2"),
            billable_hours=Decimal("2"),
            overtime_hours=Decimal("0"),
            approval_status="Draft",
            created_by=210,
        )
    )
    db.commit()


def test_create_valid_reimbursement_claim_success():
    db = setup_db()
    seed_base(db)
    response = ExpenseClaimService(db).create_claim(
        ExpenseClaimCreateRequest(
            claim_type="REIMBURSEMENT",
            expense_type="Travel",
            emp_id=210,
            job_id=50021,
            task_id=60015,
            task_participant_id=70011,
            timesheet_id=90051,
            expense_date=date(2026, 4, 2),
            amount=Decimal("850"),
            tax_amount=Decimal("0"),
            total_amount=Decimal("850"),
            recoverable_flag=True,
            receipt_attachment_ref="file-ref-001",
            submit_mode="SUBMIT",
        ),
        user_id=210,
    )
    assert response["status"] == "SUCCESS"
    assert response["approval_status"] == "Submitted"


def test_amount_invalid_fails():
    db = setup_db()
    seed_base(db)
    with pytest.raises(HTTPException):
        ExpenseClaimService(db).create_claim(
            ExpenseClaimCreateRequest(
                claim_type="DIRECT_EXPENSE",
                expense_type="Printing",
                emp_id=210,
                expense_date=date(2026, 4, 2),
                amount=Decimal("0"),
                tax_amount=Decimal("0"),
                total_amount=Decimal("0"),
            ),
            user_id=210,
        )


def test_invalid_mapping_fails():
    db = setup_db()
    seed_base(db)
    with pytest.raises(HTTPException):
        ExpenseClaimService(db).create_claim(
            ExpenseClaimCreateRequest(
                claim_type="REIMBURSEMENT",
                expense_type="Travel",
                emp_id=210,
                job_id=50021,
                task_id=99999,
                expense_date=date(2026, 4, 2),
                amount=Decimal("100"),
                tax_amount=Decimal("0"),
                total_amount=Decimal("100"),
                receipt_attachment_ref="file-ref-001",
            ),
            user_id=210,
        )


def test_recoverable_without_job_or_task_fails():
    db = setup_db()
    seed_base(db)
    with pytest.raises(HTTPException):
        ExpenseClaimService(db).create_claim(
            ExpenseClaimCreateRequest(
                claim_type="DIRECT_EXPENSE",
                expense_type="Courier",
                emp_id=210,
                expense_date=date(2026, 4, 2),
                amount=Decimal("100"),
                tax_amount=Decimal("0"),
                total_amount=Decimal("100"),
                recoverable_flag=True,
            ),
            user_id=210,
        )


def test_receipt_required_fails():
    db = setup_db()
    seed_base(db)
    with pytest.raises(HTTPException):
        ExpenseClaimService(db).create_claim(
            ExpenseClaimCreateRequest(
                claim_type="REIMBURSEMENT",
                expense_type="Travel",
                emp_id=210,
                job_id=50021,
                expense_date=date(2026, 4, 2),
                amount=Decimal("850"),
                tax_amount=Decimal("0"),
                total_amount=Decimal("850"),
            ),
            user_id=210,
        )


def test_duplicate_claim_detection_fails():
    db = setup_db()
    seed_base(db)
    service = ExpenseClaimService(db)
    payload = ExpenseClaimCreateRequest(
        claim_type="DIRECT_EXPENSE",
        expense_type="Courier",
        emp_id=210,
        job_id=50021,
        expense_date=date(2026, 4, 2),
        amount=Decimal("100"),
        tax_amount=Decimal("0"),
        total_amount=Decimal("100"),
        receipt_attachment_ref="file-ref-1",
    )
    service.create_claim(payload, user_id=210)
    with pytest.raises(HTTPException):
        service.create_claim(payload, user_id=210)


def test_claim_persisted_with_links():
    db = setup_db()
    seed_base(db)
    service = ExpenseClaimService(db)
    service.create_claim(
        ExpenseClaimCreateRequest(
            claim_type="REIMBURSEMENT",
            expense_type="Travel",
            emp_id=210,
            job_id=50021,
            task_id=60015,
            task_participant_id=70011,
            timesheet_id=90051,
            expense_date=date(2026, 4, 2),
            amount=Decimal("500"),
            tax_amount=Decimal("50"),
            total_amount=Decimal("550"),
            receipt_attachment_ref="file-ref-2",
        ),
        user_id=210,
    )
    row = db.query(WmExpenseClaim).first()
    assert row.job_id == 50021
    assert row.task_id == 60015
    assert row.task_participant_id == 70011
    assert row.timesheet_id == 90051


def _create_draft_claim(service: ExpenseClaimService, db):
    response = service.create_claim(
        ExpenseClaimCreateRequest(
            claim_type="REIMBURSEMENT",
            expense_type="Travel",
            emp_id=210,
            job_id=50021,
            expense_date=date(2026, 4, 2),
            amount=Decimal("500"),
            tax_amount=Decimal("0"),
            total_amount=Decimal("500"),
            receipt_attachment_ref="file-ref-3",
            submit_mode="DRAFT",
        ),
        user_id=210,
    )
    return response["claim_id"]


def test_submit_valid_draft_claim_success():
    db = setup_db()
    seed_base(db)
    service = ExpenseClaimService(db)
    claim_id = _create_draft_claim(service, db)
    res = service.submit_claim(claim_id, remarks="submit", user_id=210)
    assert res["approval_status"] == "Submitted"


def test_approve_valid_submitted_claim_success():
    db = setup_db()
    seed_base(db)
    service = ExpenseClaimService(db)
    claim_id = _create_draft_claim(service, db)
    service.submit_claim(claim_id, user_id=210)
    res = service.decide_claim(claim_id, ExpenseClaimDecisionRequest(decision="APPROVE"), user_id=102)
    assert res["approval_status"] == "Approved"


def test_reject_submitted_claim_with_reason_success():
    db = setup_db()
    seed_base(db)
    service = ExpenseClaimService(db)
    claim_id = _create_draft_claim(service, db)
    service.submit_claim(claim_id, user_id=210)
    res = service.decide_claim(claim_id, ExpenseClaimDecisionRequest(decision="REJECT", decision_note="invalid receipt"), user_id=102)
    assert res["approval_status"] == "Rejected"


def test_reject_without_reason_fails():
    db = setup_db()
    seed_base(db)
    service = ExpenseClaimService(db)
    claim_id = _create_draft_claim(service, db)
    service.submit_claim(claim_id, user_id=210)
    with pytest.raises(HTTPException):
        service.decide_claim(claim_id, ExpenseClaimDecisionRequest(decision="REJECT"), user_id=102)


def test_approve_draft_fails():
    db = setup_db()
    seed_base(db)
    service = ExpenseClaimService(db)
    claim_id = _create_draft_claim(service, db)
    with pytest.raises(HTTPException):
        service.decide_claim(claim_id, ExpenseClaimDecisionRequest(decision="APPROVE"), user_id=102)


def test_unauthorized_approver_fails():
    db = setup_db()
    seed_base(db)
    service = ExpenseClaimService(db)
    claim_id = _create_draft_claim(service, db)
    service.submit_claim(claim_id, user_id=210)
    with pytest.raises(HTTPException):
        service.decide_claim(claim_id, ExpenseClaimDecisionRequest(decision="APPROVE"), user_id=210)


def test_approval_history_written():
    db = setup_db()
    seed_base(db)
    service = ExpenseClaimService(db)
    claim_id = _create_draft_claim(service, db)
    service.submit_claim(claim_id, user_id=210)
    service.decide_claim(claim_id, ExpenseClaimDecisionRequest(decision="APPROVE"), user_id=102)
    history = db.query(WmExpenseClaimApprovalHistory).filter(WmExpenseClaimApprovalHistory.claim_id == claim_id).all()
    assert len(history) == 2


def _create_approved_claim(service: ExpenseClaimService, db):
    claim_id = _create_draft_claim(service, db)
    claim = db.query(WmExpenseClaim).filter(WmExpenseClaim.claim_id == claim_id).first()
    claim.cost_center_id = 12
    db.commit()
    service.submit_claim(claim_id, user_id=210)
    service.decide_claim(claim_id, ExpenseClaimDecisionRequest(decision="APPROVE"), user_id=102)
    return claim_id


def test_convert_valid_approved_claim_success():
    db = setup_db()
    seed_base(db)
    service = ExpenseClaimService(db)
    claim_id = _create_approved_claim(service, db)
    result = service.convert_to_voucher(claim_id, ConvertExpenseClaimRequest(override_flag=False, override_reason=None), user_id=999)
    assert result["conversion_status"] == "Converted"
    row = db.query(WmExpenseClaim).filter(WmExpenseClaim.claim_id == claim_id).first()
    assert row.voucher_id is not None


def test_convert_non_approved_claim_fails():
    db = setup_db()
    seed_base(db)
    service = ExpenseClaimService(db)
    claim_id = _create_draft_claim(service, db)
    with pytest.raises(HTTPException):
        service.convert_to_voucher(claim_id, ConvertExpenseClaimRequest(override_flag=False, override_reason=None), user_id=999)


def test_convert_already_converted_fails():
    db = setup_db()
    seed_base(db)
    service = ExpenseClaimService(db)
    claim_id = _create_approved_claim(service, db)
    service.convert_to_voucher(claim_id, ConvertExpenseClaimRequest(override_flag=False, override_reason=None), user_id=999)
    with pytest.raises(HTTPException):
        service.convert_to_voucher(claim_id, ConvertExpenseClaimRequest(override_flag=False, override_reason=None), user_id=999)


def test_convert_missing_cost_center_fails():
    db = setup_db()
    seed_base(db)
    service = ExpenseClaimService(db)
    claim_id = _create_draft_claim(service, db)
    service.submit_claim(claim_id, user_id=210)
    service.decide_claim(claim_id, ExpenseClaimDecisionRequest(decision="APPROVE"), user_id=102)
    with pytest.raises(HTTPException):
        service.convert_to_voucher(claim_id, ConvertExpenseClaimRequest(override_flag=False, override_reason=None), user_id=999)


def test_convert_voucher_api_failure_logs_error_and_retry_success():
    db = setup_db()
    seed_base(db)
    service = ExpenseClaimService(db)
    claim_id = _create_approved_claim(service, db)
    claim = db.query(WmExpenseClaim).filter(WmExpenseClaim.claim_id == claim_id).first()
    claim.remarks = "FORCE_VOUCHER_FAIL"
    db.commit()

    with pytest.raises(HTTPException):
        service.convert_to_voucher(claim_id, ConvertExpenseClaimRequest(override_flag=False, override_reason=None), user_id=999)

    db.refresh(claim)
    assert claim.conversion_status == "Conversion Failed"

    claim.remarks = "retry ok"
    db.commit()
    result = service.convert_to_voucher(claim_id, ConvertExpenseClaimRequest(override_flag=False, override_reason=None), user_id=999)
    assert result["conversion_status"] == "Converted"
