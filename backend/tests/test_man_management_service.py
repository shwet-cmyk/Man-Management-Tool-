from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.models.ref_employee import RefEmployee
from app.modules.man_management.schemas import BillingActionRequest, EmployeeGroupCreateRequest, JobTaskLineRequest, JobTaskStatusRequest, JobUpsertRequest, SettingsUpsertRequest, TimesheetEntryRequest
from app.modules.man_management.service import ManManagementService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def seed_emp(db, emp_id=100, hourly=Decimal("500")):
    db.add(RefEmployee(emp_id=emp_id, employee_name=f"Emp {emp_id}", company_id=1, department_id=1, monthly_ctc=Decimal("100000"), hourly_cost=hourly, is_active=True, last_synced_at=datetime.utcnow()))
    db.commit()


def create_job_payload(**overrides):
    data = {
        "job_name": "Payroll Processing",
        "client_id": 10,
        "client_name": "Client A",
        "service_id": 501,
        "company_id": 1,
        "branch_id": 1,
        "department_id": 1,
        "start_date": date.today(),
        "due_date": date.today() + timedelta(days=1),
        "amount": Decimal("2000"),
        "billable_flag": True,
        "expected_hours": Decimal("5"),
        "expected_minutes": 0,
        "manager_id": 101,
        "assigned_employee_id": 100,
        "created_by": 1,
    }
    data.update(overrides)
    return JobUpsertRequest(**data)


def test_employee_group_master_create_and_list():
    db = setup_db()
    seed_emp(db, 100)
    out = ManManagementService(db).create_employee_group(EmployeeGroupCreateRequest(group_code="OPS", group_name="Operations", employee_ids=[100]))
    assert out["status"] == "success"
    rows = ManManagementService(db).list_employee_groups()["rows"]
    assert len(rows) == 1


def test_job_lifecycle_with_task_lines_and_billing_ready_rule():
    db = setup_db()
    seed_emp(db, 100)
    service = ManManagementService(db)
    service.upsert_settings(SettingsUpsertRequest(company_id=1, timesheet_mandatory_for_completion=True, mandatory_task_completion_for_billing=True, updated_by=1))
    job = service.create_job(create_job_payload())

    line1 = service.add_job_task_line(JobTaskLineRequest(parent_job_id=job["job_id"], task_name="Collect inputs", mandatory_flag=True, created_by=1))
    service.add_job_task_line(JobTaskLineRequest(parent_job_id=job["job_id"], task_name="Finalize", mandatory_flag=True, created_by=1))

    blocked = service.billing_readiness(job["job_id"])
    assert blocked["billing_ready_flag"] is False

    service.update_job_task_status(line1["job_task_id"], JobTaskStatusRequest(status="Completed", updated_by=1))
    still_blocked = service.billing_readiness(job["job_id"])
    assert still_blocked["billing_ready_flag"] is False


def test_timesheet_with_expense_reimbursement_and_cost_rollup():
    db = setup_db()
    seed_emp(db, 100, hourly=Decimal("600"))
    service = ManManagementService(db)
    job = service.create_job(create_job_payload(amount=Decimal("3000")))
    ts = service.add_timesheet(
        TimesheetEntryRequest(
            job_id=job["job_id"],
            employee_id=100,
            date=date.today(),
            spent_hours=Decimal("2"),
            expense_lines=[{"description": "Travel", "amount": "150"}],
            reimbursement_lines=[{"description": "Meal", "amount": "50"}],
            created_by=1,
        )
    )
    assert ts["status"] == "success"
    view = service.view_job(job["job_id"])
    assert Decimal(view["job"]["final_cost_to_company"]) > 0


def test_mark_billed_only_when_billing_ready():
    db = setup_db()
    seed_emp(db, 100)
    service = ManManagementService(db)
    service.upsert_settings(SettingsUpsertRequest(company_id=1, timesheet_mandatory_for_completion=False, mandatory_task_completion_for_billing=False, updated_by=1))
    job = service.create_job(create_job_payload())
    ready = service.billing_readiness(job["job_id"])
    assert ready["billing_ready_flag"] is True
    billed = service.mark_billed(BillingActionRequest(job_id=job["job_id"], billed_amount=Decimal("2200"), billed_by=99))
    assert billed["billing_status"] == "Billed"


def test_delete_blocked_after_timesheet_when_setting_disabled():
    db = setup_db()
    seed_emp(db, 100)
    service = ManManagementService(db)
    service.upsert_settings(SettingsUpsertRequest(company_id=1, delete_allowed_after_timesheet_entry=False, updated_by=1))
    job = service.create_job(create_job_payload())
    service.add_timesheet(TimesheetEntryRequest(job_id=job["job_id"], employee_id=100, date=date.today(), spent_hours=Decimal("1"), created_by=1))
    with pytest.raises(HTTPException):
        service.delete_job(job["job_id"], deleted_by=1)


def test_validation_due_date_before_start_fails():
    db = setup_db()
    seed_emp(db, 100)
    service = ManManagementService(db)
    with pytest.raises(HTTPException):
        service.create_job(create_job_payload(start_date=date.today(), due_date=date.today() - timedelta(days=1)))


def test_dashboard_and_registers():
    db = setup_db()
    seed_emp(db, 100)
    service = ManManagementService(db)
    j = service.create_job(create_job_payload())
    service.add_timesheet(TimesheetEntryRequest(job_id=j["job_id"], employee_id=100, date=date.today(), spent_hours=Decimal("1"), created_by=1))
    register = service.job_register()
    dash = service.dashboard()
    assert register["status"] == "success"
    assert dash["total_jobs"] >= 1
