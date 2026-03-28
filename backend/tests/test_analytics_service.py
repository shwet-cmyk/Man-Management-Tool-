from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.models.ref_employee import RefEmployee
from app.models.wm_billing_configuration import WmBillingConfiguration
from app.models.wm_billing_document_link import WmBillingDocumentLink
from app.models.wm_billing_readiness import WmBillingReadiness
from app.models.wm_expense_claim import WmExpenseClaim
from app.models.wm_exception_instance import WmExceptionInstance
from app.models.wm_job import WmJob
from app.models.wm_task import WmTask
from app.models.wm_task_participant import WmTaskParticipant
from app.models.wm_task_participant_dependency import WmTaskParticipantDependency
from app.models.wm_timesheet import WmTimesheet
from app.modules.analytics.service import AnalyticsService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def seed_data(db):
    now = datetime.utcnow()
    db.add(RefEmployee(emp_id=101, employee_name="Alice", company_id=1, branch_id=10, department_id=20, monthly_ctc=Decimal("100000"), hourly_cost=Decimal("200"), is_active=True, last_synced_at=now))
    db.add(RefEmployee(emp_id=102, employee_name="Bob", company_id=1, branch_id=10, department_id=20, monthly_ctc=Decimal("100000"), hourly_cost=Decimal("0"), is_active=True, last_synced_at=now))
    db.add(WmJob(job_id=50021, job_no="JOB-2026-001", company_id=1, branch_id=10, department_id=20, customer_id=1001, job_name="GST Filing - April", is_billable=True, created_by=1, execution_status="Open", billing_status="Ready for Billing"))
    db.add(WmTask(task_id=60015, task_no="TSK-2026-1", company_id=1, customer_id=1001, job_id=50021, title="Prepare returns", task_type="Task", priority_code="Medium", status_code="In Progress", primary_owner_emp_id=101, manager_emp_id=None, billable_flag=True, billed_amount=Decimal("0"), estimated_hours=Decimal("5"), planned_start=now - timedelta(days=15), due_at=now - timedelta(days=5), created_by=101, source_type="MANUAL", last_activity_at=now - timedelta(days=10)))
    db.add(WmTask(task_id=60016, task_no="TSK-2026-2", company_id=1, customer_id=1001, job_id=50021, title="Review returns", task_type="Task", priority_code="Medium", status_code="Done", primary_owner_emp_id=101, manager_emp_id=999, billable_flag=True, billed_amount=Decimal("0"), estimated_hours=Decimal("2"), planned_start=now - timedelta(days=5), due_at=now - timedelta(days=2), completed_at=now, created_by=101, source_type="MANUAL", last_activity_at=now))

    db.add(WmTaskParticipant(task_participant_id=70011, task_id=60015, emp_id=101, role_code="EXECUTOR", planned_start=now - timedelta(days=8), planned_due=now - timedelta(days=2), created_by=1, participant_status="In Progress"))
    db.add(WmTaskParticipant(task_participant_id=70012, task_id=60015, emp_id=102, role_code="REVIEWER", planned_start=now - timedelta(days=8), planned_due=now - timedelta(days=1), created_by=1, participant_status="Planned"))
    db.add(WmTaskParticipantDependency(task_id=60015, predecessor_participant_id=70011, successor_participant_id=70012, dependency_type="FS", created_by=1))

    db.add_all([
        WmTimesheet(timesheet_id=90051, company_id=1, branch_id=10, department_id=20, customer_id=1001, job_id=50021, task_id=60015, task_participant_id=70011, emp_id=101, work_date=date.today() - timedelta(days=8), hours=Decimal("10"), billable_hours=Decimal("10"), overtime_hours=Decimal("0"), approval_status="Approved", created_by=101),
        WmTimesheet(timesheet_id=90052, company_id=1, branch_id=10, department_id=20, customer_id=1001, job_id=50021, task_id=60015, task_participant_id=70012, emp_id=102, work_date=date.today() - timedelta(days=10), hours=Decimal("2"), billable_hours=Decimal("2"), overtime_hours=Decimal("0"), approval_status="Approved", created_by=102),
        WmTimesheet(timesheet_id=90053, company_id=1, branch_id=10, department_id=20, customer_id=1001, job_id=50021, task_id=60015, task_participant_id=70011, emp_id=101, work_date=date.today() - timedelta(days=1), hours=Decimal("2"), billable_hours=Decimal("2"), overtime_hours=Decimal("0"), approval_status="Submitted", submitted_on=datetime.utcnow() - timedelta(days=4), created_by=101),
    ])

    db.add_all([
        WmExpenseClaim(claim_id=80011, claim_no="EXP-2026-00001", claim_type="REIMBURSEMENT", expense_type="Travel", company_id=1, branch_id=10, department_id=20, emp_id=101, job_id=50021, task_id=60015, customer_id=1001, expense_date=date.today() - timedelta(days=7), amount=Decimal("100"), tax_amount=Decimal("0"), total_amount=Decimal("100"), recoverable_flag=True, approval_status="Approved", created_by=101),
        WmExpenseClaim(claim_id=80012, claim_no="EXP-2026-00002", claim_type="REIMBURSEMENT", expense_type="Meals", company_id=1, branch_id=10, department_id=20, emp_id=101, job_id=50021, task_id=60015, customer_id=1001, expense_date=date.today() - timedelta(days=1), amount=Decimal("40"), tax_amount=Decimal("0"), total_amount=Decimal("40"), recoverable_flag=True, approval_status="Submitted", submitted_on=datetime.utcnow() - timedelta(days=5), created_by=101),
    ])

    db.add(WmBillingConfiguration(entity_type="TASK", job_id=50021, task_id=60015, customer_id=1001, billable_flag=True, billing_model="TIME_MATERIAL", billing_status="Ready for Billing", created_by=1))
    db.add(WmBillingReadiness(entity_type="TASK", job_id=50021, task_id=60015, ready_for_billing_flag=True, ready_for_billing_date=datetime.utcnow() - timedelta(days=4), included_billable_hours=Decimal("12"), included_recoverable_expense=Decimal("100"), billing_status="Ready for Billing", marked_by=1))
    db.commit()


def test_profitability_still_works():
    db = setup_db()
    seed_data(db)
    out = AnalyticsService(db).get_profitability(entity_type="JOB")
    assert out["items"][0]["total_cost"] >= Decimal("2100")


def test_refresh_detects_core_exceptions():
    db = setup_db()
    seed_data(db)
    db.add(WmBillingDocumentLink(entity_type="TASK", job_id=50021, task_id=60015, billing_reference_type="EXTERNAL_INVOICE", billing_reference_no="INV-LOW", billed_amount=Decimal("1000"), billed_date=date.today(), billing_status="Partially Billed", created_by=1))
    db.commit()

    result = AnalyticsService(db).refresh_exceptions(company_id=1)
    assert result["exceptions_generated"] > 0

    types = {x.exception_type for x in db.query(WmExceptionInstance).filter(WmExceptionInstance.is_active.is_(True)).all()}
    assert "ROLLED_OVER" in types
    assert "OVERRUN" in types
    assert "UNMANAGED" in types
    assert "NO_TIMESHEET" in types
    assert "BILLED_BELOW_COST" in types
    assert "APPROVAL_DELAY" in types


def test_unbilled_ready_detected_after_grace():
    db = setup_db()
    seed_data(db)
    AnalyticsService(db).refresh_exceptions(company_id=1)
    queue = AnalyticsService(db).get_exception_queue(exception_type="UNBILLED_READY", entity_type="TASK", company_id=1)
    assert queue["totals"]["count"] >= 1


def test_exception_queue_filters():
    db = setup_db()
    seed_data(db)
    AnalyticsService(db).refresh_exceptions(company_id=1)
    queue = AnalyticsService(db).get_exception_queue(exception_type="ROLLED_OVER", entity_type="TASK", company_id=1)
    assert queue["totals"]["count"] >= 1
