from datetime import date, datetime
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.models.ref_employee import RefEmployee
from app.models.wm_timesheet import WmTimesheet
from app.modules.jobs.schemas import JobCreateRequest, JobStatusTransitionRequest, TaskShellCreateRequest, TransferDecisionRequest
from app.modules.jobs.service import JobGovernanceService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def seed_employee(db, emp_id: int, hourly: Decimal | None = Decimal("500"), monthly: Decimal = Decimal("100000")):
    db.add(
        RefEmployee(
            emp_id=emp_id,
            employee_name=f"Emp {emp_id}",
            company_id=1,
            department_id=1,
            monthly_ctc=monthly,
            hourly_cost=hourly,
            is_active=True,
            last_synced_at=datetime.utcnow(),
        )
    )
    db.commit()


def create_task(db, billable: bool = True) -> int:
    service = JobGovernanceService(db)
    return service.create_task_shell(
        TaskShellCreateRequest(
            company_id=1,
            branch_id=1,
            department_id=1,
            client_id=10 if billable else None,
            client_name="Client A" if billable else None,
            title="Task ABC",
            billable_flag=billable,
            task_owner_id=100,
            manager_id=200,
        )
    )["task_id"]


def add_timesheet(db, task_id: int, job_id: int, emp_id: int, hours: Decimal):
    ts_id = int((db.query(func.max(WmTimesheet.timesheet_id)).scalar() or 0) + 1)
    db.add(
        WmTimesheet(
            timesheet_id=ts_id,
            company_id=1,
            branch_id=1,
            department_id=1,
            customer_id=10,
            job_id=job_id,
            task_id=task_id,
            emp_id=emp_id,
            work_date=date.today(),
            hours=hours,
            billable_hours=hours,
            created_by=emp_id,
            approval_status="Approved",
            spent_minutes=int(hours * 60),
        )
    )
    db.commit()


def test_dependency_transfer_acceptance_flow_success():
    db = setup_db()
    seed_employee(db, 100)
    seed_employee(db, 101)
    service = JobGovernanceService(db)
    task_id = create_task(db)

    j1 = service.create_job(JobCreateRequest(parent_task_id=task_id, title="Job 1", assigned_employee_id=100, company_id=1, client_id=10))
    j2 = service.create_job(JobCreateRequest(parent_task_id=task_id, title="Job 2", assigned_employee_id=101, company_id=1, client_id=10, dependency_job_id=j1["job_id"], transfer_required=True, acceptance_required=True))

    add_timesheet(db, task_id, j1["job_id"], 100, Decimal("2"))
    service.transition_job_status(j1["job_id"], JobStatusTransitionRequest(status="Completed", changed_by=100, remarks="done"))

    with pytest.raises(HTTPException):
        service.transition_job_status(j2["job_id"], JobStatusTransitionRequest(status="In Progress", changed_by=101, remarks="start"))

    decision = service.decide_transfer(j2["job_id"], TransferDecisionRequest(decision="ACCEPT", employee_id=101))
    assert decision["transfer_status"] == "Accepted"


def test_costing_and_profitability_rollups_billable_task():
    db = setup_db()
    seed_employee(db, 100, hourly=Decimal("400"))
    seed_employee(db, 101, hourly=Decimal("600"))
    service = JobGovernanceService(db)
    task_id = create_task(db, billable=True)

    j1 = service.create_job(JobCreateRequest(parent_task_id=task_id, title="Analysis", assigned_employee_id=100, company_id=1, client_id=10, billed_amount=Decimal("1000")))
    j2 = service.create_job(JobCreateRequest(parent_task_id=task_id, title="Review", assigned_employee_id=101, company_id=1, client_id=10, billed_amount=Decimal("1500")))

    add_timesheet(db, task_id, j1["job_id"], 100, Decimal("2"))
    add_timesheet(db, task_id, j2["job_id"], 101, Decimal("2"))
    service.recalculate_task_rollups(task_id)

    dashboard = service.dashboard_metrics()
    assert dashboard["profitable_tasks"] >= 1


def test_non_billable_task_treated_as_loss():
    db = setup_db()
    seed_employee(db, 100, hourly=Decimal("500"))
    service = JobGovernanceService(db)
    task_id = create_task(db, billable=False)
    j1 = service.create_job(JobCreateRequest(parent_task_id=task_id, title="Internal", assigned_employee_id=100, company_id=1, billable_flag=False))
    add_timesheet(db, task_id, j1["job_id"], 100, Decimal("2"))
    service.recalculate_task_rollups(task_id)
    metrics = service.report_registers()["task_register"]
    row = [r for r in metrics if r["task_id"] == task_id][0]
    assert row["financial_status"] == "Not Billable"


def test_transfer_rejection_requires_reason():
    db = setup_db()
    seed_employee(db, 100)
    seed_employee(db, 101)
    service = JobGovernanceService(db)
    task_id = create_task(db)
    j1 = service.create_job(JobCreateRequest(parent_task_id=task_id, title="J1", assigned_employee_id=100, company_id=1, client_id=10))
    j2 = service.create_job(JobCreateRequest(parent_task_id=task_id, title="J2", assigned_employee_id=101, company_id=1, client_id=10, dependency_job_id=j1["job_id"], transfer_required=True))
    add_timesheet(db, task_id, j1["job_id"], 100, Decimal("1"))
    service.transition_job_status(j1["job_id"], JobStatusTransitionRequest(status="Completed", changed_by=100, remarks="done"))

    with pytest.raises(HTTPException):
        service.decide_transfer(j2["job_id"], TransferDecisionRequest(decision="REJECT", employee_id=101))


def test_blocked_job_cannot_complete_before_predecessor():
    db = setup_db()
    seed_employee(db, 100)
    seed_employee(db, 101)
    service = JobGovernanceService(db)
    task_id = create_task(db)
    j1 = service.create_job(JobCreateRequest(parent_task_id=task_id, title="J1", assigned_employee_id=100, company_id=1, client_id=10))
    j2 = service.create_job(JobCreateRequest(parent_task_id=task_id, title="J2", assigned_employee_id=101, company_id=1, client_id=10, dependency_job_id=j1["job_id"], transfer_required=False, acceptance_required=False))
    add_timesheet(db, task_id, j2["job_id"], 101, Decimal("1"))

    with pytest.raises(HTTPException):
        service.transition_job_status(j2["job_id"], JobStatusTransitionRequest(status="Completed", changed_by=101, remarks="attempt"))


def test_rollover_heavy_job_makes_task_critical():
    db = setup_db()
    seed_employee(db, 100)
    service = JobGovernanceService(db)
    task_id = create_task(db)
    j1 = service.create_job(JobCreateRequest(parent_task_id=task_id, title="J1", assigned_employee_id=100, company_id=1, client_id=10))

    job = service._job(j1["job_id"])
    job.rollover_count = 4
    db.commit()
    service.recalculate_task_rollups(task_id)

    row = [r for r in service.report_registers()["task_register"] if r["task_id"] == task_id][0]
    assert row["status"] == "Critical"
