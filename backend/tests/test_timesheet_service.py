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
from app.models.wm_timesheet_approval_history import WmTimesheetApprovalHistory
from app.models.wm_timesheet import WmTimesheet
from app.modules.timesheets.schemas import TimesheetCreateRequest, TimesheetDecisionRequest
from app.modules.timesheets.service import TimesheetService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def seed_employee(db, emp_id: int):
    db.add(
        RefEmployee(
            emp_id=emp_id,
            employee_name=f"Emp {emp_id}",
            company_id=1,
            monthly_ctc=Decimal("100000"),
            hourly_cost=Decimal("625"),
            is_active=True,
            last_synced_at=datetime.utcnow(),
        )
    )


def seed_job(db, job_id: int = 50021):
    db.add(
        WmJob(
            job_id=job_id,
            job_no="JOB-2026-001",
            company_id=1,
            branch_id=10,
            department_id=20,
            customer_id=30,
            job_name="Compliance job",
            is_billable=True,
            created_by=1,
            execution_status="Open",
            billing_status="Not Billed",
        )
    )


def seed_task(db, task_id: int = 60015, job_id: int = 50021):
    now = datetime.utcnow()
    db.add(
        WmTask(
            task_id=task_id,
            task_no="TSK-2026-000001",
            company_id=1,
            customer_id=30,
            job_id=job_id,
            title="Prepare reconciliation",
            task_type="Task",
            priority_code="Medium",
            status_code="Open",
            primary_owner_emp_id=210,
            billable_flag=True,
            billed_amount=Decimal("0"),
            estimated_hours=Decimal("8"),
            planned_start=now,
            due_at=now + timedelta(days=2),
            created_by=210,
            source_type="MANUAL",
        )
    )


def seed_participant(db, participant_id: int = 70011, task_id: int = 60015, emp_id: int = 210):
    now = datetime.utcnow()
    db.add(
        WmTaskParticipant(
            task_participant_id=participant_id,
            task_id=task_id,
            emp_id=emp_id,
            role_code="EXECUTOR",
            planned_start=now,
            planned_due=now + timedelta(days=1),
            submission_required=True,
            acceptance_required=False,
            is_mandatory=True,
            participant_status="Planned",
            created_by=1,
        )
    )


def seed_base(db):
    seed_employee(db, 210)
    seed_employee(db, 211)
    seed_job(db)
    seed_task(db)
    seed_participant(db)
    db.commit()


def test_create_valid_timesheet_success():
    db = setup_db()
    seed_base(db)
    response = TimesheetService(db).create_timesheet(
        TimesheetCreateRequest(
            emp_id=210,
            job_id=50021,
            task_id=60015,
            task_participant_id=70011,
            work_date=date(2026, 4, 2),
            start_time=datetime(2026, 4, 2, 10, 0, 0),
            end_time=datetime(2026, 4, 2, 13, 30, 0),
            hours=Decimal("3.5"),
            billable_hours=Decimal("3"),
            overtime_hours=Decimal("0"),
            activity_type="Task Work",
            submit_mode="SUBMIT",
        ),
        user_id=210,
    )
    assert response["status"] == "SUCCESS"
    assert response["approval_status"] == "Submitted"


def test_participant_mismatch_fails():
    db = setup_db()
    seed_base(db)
    with pytest.raises(HTTPException):
        TimesheetService(db).create_timesheet(
            TimesheetCreateRequest(
                emp_id=211,
                job_id=50021,
                task_id=60015,
                task_participant_id=70011,
                work_date=date(2026, 4, 2),
                hours=Decimal("2"),
                billable_hours=Decimal("2"),
            ),
            user_id=211,
        )


def test_invalid_hours_fails():
    db = setup_db()
    seed_base(db)
    with pytest.raises(HTTPException):
        TimesheetService(db).create_timesheet(
            TimesheetCreateRequest(
                emp_id=210,
                job_id=50021,
                work_date=date(2026, 4, 2),
                hours=Decimal("0"),
            ),
            user_id=210,
        )


def test_billable_exceeds_hours_fails():
    db = setup_db()
    seed_base(db)
    with pytest.raises(HTTPException):
        TimesheetService(db).create_timesheet(
            TimesheetCreateRequest(
                emp_id=210,
                job_id=50021,
                work_date=date(2026, 4, 2),
                hours=Decimal("2"),
                billable_hours=Decimal("3"),
            ),
            user_id=210,
        )


def test_overlapping_timesheet_fails():
    db = setup_db()
    seed_base(db)
    service = TimesheetService(db)
    service.create_timesheet(
        TimesheetCreateRequest(
            emp_id=210,
            job_id=50021,
            work_date=date(2026, 4, 2),
            start_time=datetime(2026, 4, 2, 10, 0, 0),
            end_time=datetime(2026, 4, 2, 11, 0, 0),
            hours=Decimal("1"),
        ),
        user_id=210,
    )

    with pytest.raises(HTTPException):
        service.create_timesheet(
            TimesheetCreateRequest(
                emp_id=210,
                job_id=50021,
                work_date=date(2026, 4, 2),
                start_time=datetime(2026, 4, 2, 10, 30, 0),
                end_time=datetime(2026, 4, 2, 11, 30, 0),
                hours=Decimal("1"),
            ),
            user_id=210,
        )


def test_submit_auto_starts_participant():
    db = setup_db()
    seed_base(db)
    service = TimesheetService(db)

    response = service.create_timesheet(
        TimesheetCreateRequest(
            emp_id=210,
            job_id=50021,
            task_id=60015,
            task_participant_id=70011,
            work_date=date(2026, 4, 2),
            hours=Decimal("1.5"),
            submit_mode="SUBMIT",
        ),
        user_id=210,
    )
    participant = db.query(WmTaskParticipant).filter(WmTaskParticipant.task_participant_id == 70011).first()
    assert response["participant_status_hint"] == "In Progress"
    assert participant.participant_status == "In Progress"


def test_timesheet_persisted_with_links():
    db = setup_db()
    seed_base(db)
    service = TimesheetService(db)
    service.create_timesheet(
        TimesheetCreateRequest(
            emp_id=210,
            job_id=50021,
            task_id=60015,
            task_participant_id=70011,
            work_date=date(2026, 4, 2),
            hours=Decimal("2"),
            billable_hours=Decimal("1.5"),
            overtime_hours=Decimal("0.5"),
            submit_mode="DRAFT",
        ),
        user_id=210,
    )
    row = db.query(WmTimesheet).first()
    assert row.job_id == 50021
    assert row.task_id == 60015
    assert row.task_participant_id == 70011


def test_submit_valid_draft_timesheet_success():
    db = setup_db()
    seed_base(db)
    service = TimesheetService(db)
    create_res = service.create_timesheet(
        TimesheetCreateRequest(
            emp_id=210,
            job_id=50021,
            work_date=date(2026, 4, 2),
            hours=Decimal("2"),
            submit_mode="DRAFT",
        ),
        user_id=210,
    )
    submit_res = service.submit_timesheet(create_res["timesheet_id"], remarks="Submitting", user_id=210)
    assert submit_res["approval_status"] == "Submitted"


def test_approve_valid_submitted_timesheet_success():
    db = setup_db()
    seed_base(db)
    service = TimesheetService(db)
    create_res = service.create_timesheet(
        TimesheetCreateRequest(emp_id=210, job_id=50021, work_date=date(2026, 4, 2), hours=Decimal("2")),
        user_id=210,
    )
    service.submit_timesheet(create_res["timesheet_id"], user_id=210)
    decide_res = service.decide_timesheet(
        create_res["timesheet_id"],
        TimesheetDecisionRequest(decision="APPROVE"),
        user_id=102,
    )
    assert decide_res["approval_status"] == "Approved"


def test_reject_submitted_timesheet_with_reason_success():
    db = setup_db()
    seed_base(db)
    service = TimesheetService(db)
    create_res = service.create_timesheet(
        TimesheetCreateRequest(emp_id=210, job_id=50021, work_date=date(2026, 4, 2), hours=Decimal("2")),
        user_id=210,
    )
    service.submit_timesheet(create_res["timesheet_id"], user_id=210)
    decide_res = service.decide_timesheet(
        create_res["timesheet_id"],
        TimesheetDecisionRequest(decision="REJECT", decision_note="Fix billable split"),
        user_id=102,
    )
    assert decide_res["approval_status"] == "Rejected"


def test_reject_without_reason_fails():
    db = setup_db()
    seed_base(db)
    service = TimesheetService(db)
    create_res = service.create_timesheet(
        TimesheetCreateRequest(emp_id=210, job_id=50021, work_date=date(2026, 4, 2), hours=Decimal("2")),
        user_id=210,
    )
    service.submit_timesheet(create_res["timesheet_id"], user_id=210)
    with pytest.raises(HTTPException):
        service.decide_timesheet(
            create_res["timesheet_id"],
            TimesheetDecisionRequest(decision="REJECT"),
            user_id=102,
        )


def test_approve_draft_fails():
    db = setup_db()
    seed_base(db)
    service = TimesheetService(db)
    create_res = service.create_timesheet(
        TimesheetCreateRequest(emp_id=210, job_id=50021, work_date=date(2026, 4, 2), hours=Decimal("2")),
        user_id=210,
    )
    with pytest.raises(HTTPException):
        service.decide_timesheet(create_res["timesheet_id"], TimesheetDecisionRequest(decision="APPROVE"), user_id=102)


def test_unauthorized_approver_fails():
    db = setup_db()
    seed_base(db)
    service = TimesheetService(db)
    create_res = service.create_timesheet(
        TimesheetCreateRequest(emp_id=210, job_id=50021, work_date=date(2026, 4, 2), hours=Decimal("2")),
        user_id=210,
    )
    service.submit_timesheet(create_res["timesheet_id"], user_id=210)
    with pytest.raises(HTTPException):
        service.decide_timesheet(create_res["timesheet_id"], TimesheetDecisionRequest(decision="APPROVE"), user_id=210)


def test_approval_history_written():
    db = setup_db()
    seed_base(db)
    service = TimesheetService(db)
    create_res = service.create_timesheet(
        TimesheetCreateRequest(emp_id=210, job_id=50021, work_date=date(2026, 4, 2), hours=Decimal("2")),
        user_id=210,
    )
    service.submit_timesheet(create_res["timesheet_id"], user_id=210)
    service.decide_timesheet(create_res["timesheet_id"], TimesheetDecisionRequest(decision="APPROVE"), user_id=102)
    history = db.query(WmTimesheetApprovalHistory).filter(WmTimesheetApprovalHistory.timesheet_id == create_res["timesheet_id"]).all()
    assert len(history) == 2
