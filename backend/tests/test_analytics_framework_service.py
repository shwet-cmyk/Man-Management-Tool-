from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.models.ref_employee import RefEmployee
from app.models.wm_job import WmJob
from app.models.wm_man_approval import WmManApproval
from app.models.wm_task import WmTask
from app.models.wm_ticket import WmTicket
from app.models.wm_timesheet import WmTimesheet
from app.modules.analytics_framework.schemas import AnalyticsFilter, DrilldownRequest, TrendQueryRequest, WidgetQueryRequest
from app.modules.analytics_framework.service import DashboardAggregationService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def seed_data(db):
    db.add(RefEmployee(emp_id=100, employee_name="E1", company_id=1, monthly_ctc=Decimal("80000"), hourly_cost=Decimal("500"), is_active=True, last_synced_at=datetime.utcnow()))
    db.add(RefEmployee(emp_id=101, employee_name="E2", company_id=1, monthly_ctc=Decimal("90000"), hourly_cost=Decimal("550"), is_active=True, last_synced_at=datetime.utcnow()))
    db.add(WmTicket(ticket_id=1, ticket_no="T1", subject="Issue", description="Issue", priority="HIGH", status="OPEN", created_by=1, company_id=1, customer_id=10, created_on=datetime.utcnow()))
    db.add(WmTask(task_id=1, task_no="TSK-1", company_id=1, title="Task", task_type="Task", priority_code="High", status_code="Active", primary_owner_emp_id=100, billable_flag=True, billed_amount=Decimal("1000"), estimated_hours=Decimal("5"), planned_start=datetime.utcnow(), due_at=datetime.utcnow() + timedelta(days=1), created_by=1))
    db.add(WmJob(job_id=1, job_no="JOB-1", job_name="Job1", company_id=1, customer_id=10, start_date=date.today()-timedelta(days=3), due_date=date.today()-timedelta(days=1), is_billable=True, assigned_employee_id=100, manager_id=101, planned_hours=Decimal("5"), planned_minutes=0, spent_hours=Decimal("6"), cost_to_company=Decimal("1200"), overhead_amount=Decimal("120"), final_cost_to_company=Decimal("1320"), billed_amount=Decimal("1600"), profit_or_loss=Decimal("280"), execution_status="In Progress", billing_status="Blocked", critical_flag=True, rollover_count=4, transfer_status="Rejected", created_by=1))
    db.add(WmJob(job_id=2, job_no="JOB-2", job_name="Job2", company_id=1, customer_id=11, start_date=date.today(), due_date=date.today()+timedelta(days=2), is_billable=False, assigned_employee_id=101, manager_id=101, planned_hours=Decimal("3"), planned_minutes=30, spent_hours=Decimal("2"), cost_to_company=Decimal("500"), overhead_amount=Decimal("50"), final_cost_to_company=Decimal("550"), billed_amount=Decimal("0"), profit_or_loss=Decimal("-550"), execution_status="Completed", billing_status="Not Billable", critical_flag=False, rollover_count=0, transfer_status="Awaiting Acceptance", created_by=1))
    db.add(WmTimesheet(timesheet_id=1, company_id=1, job_id=1, task_id=1, emp_id=100, work_date=date.today(), hours=Decimal("2"), billable_hours=Decimal("2"), approval_status="Pending", expense_total=Decimal("100"), reimbursement_total=Decimal("20"), created_by=1))
    db.add(WmTimesheet(timesheet_id=2, company_id=1, job_id=2, task_id=1, emp_id=101, work_date=date.today(), hours=Decimal("1"), billable_hours=Decimal("0"), approval_status="Approved", expense_total=Decimal("50"), reimbursement_total=Decimal("10"), created_by=1))
    db.add(WmManApproval(approval_id=1, entity_type="TIMESHEET", entity_id=1, approval_type="TIMESHEET", current_status="Pending", requested_by=1))
    db.commit()


def test_catalog_and_summary_cards():
    db = setup_db()
    seed_data(db)
    svc = DashboardAggregationService(db)
    cat = svc.metric_catalog()
    assert "job_count" in cat["metrics"]
    cards = svc.summary_cards(AnalyticsFilter(company_id=1))["data"]
    assert cards["job_count"] >= 2


def test_widget_dataset_and_matrix_and_leaderboard():
    db = setup_db()
    seed_data(db)
    svc = DashboardAggregationService(db)
    widget = svc.widget_dataset(WidgetQueryRequest(widget_type="grouped_bar", metric_code="total_cost_to_company", group_by=["employee"], filters=AnalyticsFilter(company_id=1)))
    assert widget["rows"]
    matrix = svc.matrix("total_actual_hours", "employee", "client", AnalyticsFilter(company_id=1), top_n=10)
    assert matrix["rows"]
    leaderboard = svc.leaderboard("total_cost_to_company", "manager", AnalyticsFilter(company_id=1), top_n=5)
    assert leaderboard["leaderboard"]


def test_trend_and_drilldown():
    db = setup_db()
    seed_data(db)
    svc = DashboardAggregationService(db)
    trend = svc.trend_dataset(TrendQueryRequest(metric_code="job_count", grain="month", filters=AnalyticsFilter(company_id=1)))
    assert trend["series"]
    drill = svc.drilldown(DrilldownRequest(entity_type="job", metric_code="job_count", filters=AnalyticsFilter(company_id=1)))
    assert len(drill["rows"]) == 2


def test_comparison_and_filter_support():
    db = setup_db()
    seed_data(db)
    svc = DashboardAggregationService(db)
    cmp = svc.comparison("job_count", AnalyticsFilter(company_id=1, employee_id=100), AnalyticsFilter(company_id=1, employee_id=101))
    assert "delta" in cmp
    filtered = svc.widget_dataset(WidgetQueryRequest(widget_type="summary_card", metric_code="critical_count", group_by=["manager"], filters=AnalyticsFilter(company_id=1, critical_flag=True)))
    assert filtered["rows"]
