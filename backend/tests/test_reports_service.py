from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.models.ref_employee import RefEmployee
from app.models.wm_exception_instance import WmExceptionInstance
from app.models.wm_expense_claim import WmExpenseClaim
from app.models.wm_job import WmJob
from app.models.wm_notification_queue import WmNotificationQueue
from app.models.wm_task import WmTask
from app.models.wm_timesheet import WmTimesheet
from app.modules.reports.schemas import (
    CreateReportRequest,
    CreateScheduleRequest,
    ExportReportRequest,
    RunReportRequest,
    SaveReportConfigRequest,
)
from app.modules.reports.service import ReportsService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def seed_data(db):
    now = datetime.utcnow()
    db.add_all(
        [
            RefEmployee(
                emp_id=101,
                employee_name="Alice",
                company_id=1,
                branch_id=10,
                department_id=20,
                monthly_ctc=Decimal("100000"),
                hourly_cost=Decimal("200"),
                is_active=True,
                last_synced_at=now,
            ),
            RefEmployee(
                emp_id=102,
                employee_name="Bob",
                company_id=1,
                branch_id=10,
                department_id=20,
                monthly_ctc=Decimal("90000"),
                hourly_cost=Decimal("150"),
                is_active=True,
                last_synced_at=now,
            ),
            WmJob(
                job_id=50021,
                job_no="JOB-2026-001",
                company_id=1,
                branch_id=10,
                department_id=20,
                customer_id=1001,
                job_name="GST Filing - April",
                is_billable=True,
                created_by=1,
                execution_status="Open",
                billing_status="Ready for Billing",
                manager_id=9001,
            ),
            WmJob(
                job_id=50022,
                job_no="JOB-2026-002",
                company_id=1,
                branch_id=10,
                department_id=21,
                customer_id=1002,
                job_name="Audit Support",
                is_billable=True,
                created_by=1,
                execution_status="Open",
                billing_status="Not Billed",
                manager_id=9002,
            ),
        ]
    )

    db.add_all(
        [
            WmTask(
                task_id=60015,
                task_no="TSK-2026-1",
                company_id=1,
                customer_id=1001,
                job_id=50021,
                title="Prepare returns",
                task_type="Task",
                priority_code="Medium",
                status_code="In Progress",
                primary_owner_emp_id=101,
                manager_emp_id=9001,
                billable_flag=True,
                billed_amount=Decimal("1000"),
                estimated_hours=Decimal("5"),
                planned_start=now - timedelta(days=15),
                due_at=now - timedelta(days=5),
                created_by=101,
                source_type="MANUAL",
            ),
            WmTask(
                task_id=60016,
                task_no="TSK-2026-2",
                company_id=1,
                customer_id=1002,
                job_id=50022,
                title="Review workpaper",
                task_type="Task",
                priority_code="Medium",
                status_code="In Progress",
                primary_owner_emp_id=102,
                manager_emp_id=9002,
                billable_flag=True,
                billed_amount=Decimal("0"),
                estimated_hours=Decimal("2"),
                planned_start=now - timedelta(days=4),
                due_at=now + timedelta(days=1),
                created_by=102,
                source_type="MANUAL",
            ),
        ]
    )

    db.add_all(
        [
            WmTimesheet(
                timesheet_id=90051,
                company_id=1,
                branch_id=10,
                department_id=20,
                customer_id=1001,
                job_id=50021,
                task_id=60015,
                emp_id=101,
                work_date=date.today() - timedelta(days=8),
                hours=Decimal("10"),
                billable_hours=Decimal("10"),
                overtime_hours=Decimal("0"),
                approval_status="Approved",
                created_by=101,
            ),
            WmTimesheet(
                timesheet_id=90052,
                company_id=1,
                branch_id=10,
                department_id=21,
                customer_id=1002,
                job_id=50022,
                task_id=60016,
                emp_id=102,
                work_date=date.today() - timedelta(days=1),
                hours=Decimal("4"),
                billable_hours=Decimal("2"),
                overtime_hours=Decimal("0"),
                approval_status="Approved",
                created_by=102,
            ),
        ]
    )

    db.add(
        WmExpenseClaim(
            claim_id=80011,
            claim_no="EXP-2026-00001",
            claim_type="REIMBURSEMENT",
            expense_type="Travel",
            company_id=1,
            branch_id=10,
            department_id=20,
            emp_id=101,
            job_id=50021,
            task_id=60015,
            customer_id=1001,
            expense_date=date.today() - timedelta(days=7),
            amount=Decimal("100"),
            tax_amount=Decimal("0"),
            total_amount=Decimal("100"),
            recoverable_flag=True,
            approval_status="Approved",
            created_by=101,
        )
    )

    db.add(
        WmExceptionInstance(
            exception_type="OVERRUN",
            severity="HIGH",
            entity_type="TASK",
            entity_id=60015,
            company_id=1,
            job_id=50021,
            task_id=60015,
            exception_message="Overrun",
            first_detected_on=now,
            last_evaluated_on=now,
            is_active=True,
        )
    )
    db.commit()


def test_report_create_config_run_and_export():
    db = setup_db()
    seed_data(db)
    service = ReportsService(db)

    report = service.create_report(CreateReportRequest(name="Client Profitability", created_by=1, is_public=False))
    service.save_config(
        SaveReportConfigRequest(
            report_id=report["report_id"],
            data_source="JOB",
            columns=["customer_id", "revenue", "cost", "profit"],
            group_by=["customer_id"],
            aggregation={"revenue": "sum", "cost": "sum", "profit": "sum"},
        )
    )

    result = service.run_report(RunReportRequest(report_id=report["report_id"], requested_by=1, filters={"company_id": 1}, page=1, page_size=50))
    assert result["total_rows"] >= 1
    assert "customer_id" in result["rows"][0]

    export = service.export_report(
        ExportReportRequest(report_id=report["report_id"], requested_by=1, filters={"company_id": 1}, export_format="CSV")
    )
    assert export["content_type"] == "text/csv"
    assert "customer_id" in export["content"]


def test_schedule_runs_and_queues_notification():
    db = setup_db()
    seed_data(db)
    service = ReportsService(db)
    report = service.create_report(CreateReportRequest(name="MIS", created_by=1, is_public=True))
    service.save_config(
        SaveReportConfigRequest(
            report_id=report["report_id"],
            data_source="EMPLOYEE",
            columns=["emp_id", "hours", "billable_hours"],
            group_by=["emp_id"],
            aggregation={"hours": "sum", "billable_hours": "sum"},
        )
    )
    service.create_schedule(
        CreateScheduleRequest(
            report_id=report["report_id"],
            frequency="DAILY",
            recipients=[101, 102],
            next_run=datetime.utcnow() - timedelta(minutes=1),
            export_format="PDF",
        )
    )

    outcome = service.run_due_schedules()
    assert outcome["schedules_processed"] == 1
    assert db.query(WmNotificationQueue).count() == 2


def test_standard_reports_available():
    db = setup_db()
    seed_data(db)
    service = ReportsService(db)

    assert len(service.standard_job_profitability(company_id=1)["items"]) >= 1
    assert len(service.standard_client_profitability(company_id=1)["items"]) >= 1
    assert len(service.standard_employee_productivity(company_id=1)["items"]) >= 1
    assert isinstance(service.standard_unbilled_work(company_id=1)["items"], list)
    assert isinstance(service.standard_overrun_analysis(company_id=1)["items"], list)
    assert service.standard_exception_report(company_id=1)["totals"]["count"] >= 1
