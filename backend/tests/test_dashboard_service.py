from datetime import date, datetime
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.models.wm_job import WmJob
from app.models.wm_task import WmTask
from app.models.wm_timesheet import WmTimesheet
from app.modules.dashboard.schemas import DashboardCreateRequest, WidgetAddRequest, WidgetConfig, WidgetDataRequest
from app.modules.dashboard.service import DashboardService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def seed_data(db):
    now = datetime.utcnow()
    db.add(WmJob(job_id=50021, job_no="JOB-2026-001", company_id=1, branch_id=10, department_id=20, customer_id=1001, job_name="Job 1", is_billable=True, created_by=1, execution_status="Open", billing_status="Not Billed"))
    db.add(WmTask(task_id=60015, task_no="TSK-2026-1", company_id=1, customer_id=1001, job_id=50021, title="Task A", task_type="Task", priority_code="Medium", status_code="Open", primary_owner_emp_id=101, manager_emp_id=210, billable_flag=True, billed_amount=Decimal("0"), estimated_hours=Decimal("6"), planned_start=now, due_at=now, created_by=101, source_type="MANUAL"))
    db.add(WmTimesheet(timesheet_id=90051, company_id=1, branch_id=10, department_id=20, customer_id=1001, job_id=50021, task_id=60015, emp_id=101, work_date=date(2026, 4, 10), hours=Decimal("5"), billable_hours=Decimal("5"), overtime_hours=Decimal("0"), approval_status="Approved", created_by=101))
    db.commit()


def test_create_dashboard_success():
    db = setup_db()
    result = DashboardService(db).create_dashboard(DashboardCreateRequest(name="CEO Dashboard", user_id=1, is_default=True))
    assert result["status"] == "SUCCESS"


def test_add_widget_success_and_visible():
    db = setup_db()
    seed_data(db)
    service = DashboardService(db)
    dash = service.create_dashboard(DashboardCreateRequest(name="Ops", user_id=1))
    widget = service.add_widget(
        WidgetAddRequest(
            dashboard_id=dash["dashboard_id"],
            widget_type="CHART",
            title="Hours by Employee",
            config=WidgetConfig(data_source="TIMESHEET", dimension="emp_id", measure="hours", aggregation="SUM"),
        )
    )
    loaded = service.get_dashboard(dash["dashboard_id"])
    assert widget["widget_id"] == loaded["widgets"][0]["widget_id"]


def test_apply_filter_updates_data():
    db = setup_db()
    seed_data(db)
    service = DashboardService(db)
    dash = service.create_dashboard(DashboardCreateRequest(name="Ops", user_id=1))
    widget = service.add_widget(
        WidgetAddRequest(
            dashboard_id=dash["dashboard_id"],
            widget_type="CHART",
            title="Hours by Employee",
            config=WidgetConfig(data_source="TIMESHEET", dimension="emp_id", measure="hours", aggregation="SUM"),
        )
    )
    data = service.get_widget_data(WidgetDataRequest(widget_id=widget["widget_id"], filters={"company_id": 1}))
    assert data["data"][0]["y"] == 5


def test_drilldown_grouping_payload_shape():
    db = setup_db()
    seed_data(db)
    service = DashboardService(db)
    dash = service.create_dashboard(DashboardCreateRequest(name="Ops", user_id=1))
    widget = service.add_widget(
        WidgetAddRequest(
            dashboard_id=dash["dashboard_id"],
            widget_type="TABLE",
            title="Task Count by Manager",
            config=WidgetConfig(data_source="TASK", dimension="manager_emp_id", measure="task_id", aggregation="COUNT"),
        )
    )
    data = service.get_widget_data(WidgetDataRequest(widget_id=widget["widget_id"], filters={}))
    assert {"x", "y"}.issubset(set(data["data"][0].keys()))


def test_role_restriction_like_scope_filter_hides_other_company_data():
    db = setup_db()
    seed_data(db)
    db.add(WmTimesheet(timesheet_id=90052, company_id=2, branch_id=11, department_id=21, customer_id=1002, job_id=50021, task_id=60015, emp_id=102, work_date=date(2026, 4, 10), hours=Decimal("7"), billable_hours=Decimal("7"), overtime_hours=Decimal("0"), approval_status="Approved", created_by=102))
    db.commit()

    service = DashboardService(db)
    dash = service.create_dashboard(DashboardCreateRequest(name="Ops", user_id=1))
    widget = service.add_widget(
        WidgetAddRequest(
            dashboard_id=dash["dashboard_id"],
            widget_type="KPI",
            title="Hours KPI",
            config=WidgetConfig(data_source="TIMESHEET", dimension=None, measure="hours", aggregation="SUM"),
        )
    )
    data = service.get_widget_data(WidgetDataRequest(widget_id=widget["widget_id"], filters={"company_id": 1}))
    assert data["data"][0]["y"] == 5


def test_invalid_dimension_fails():
    db = setup_db()
    service = DashboardService(db)
    dash = service.create_dashboard(DashboardCreateRequest(name="Ops", user_id=1))
    with pytest.raises(HTTPException):
        service.add_widget(
            WidgetAddRequest(
                dashboard_id=dash["dashboard_id"],
                widget_type="CHART",
                title="Bad",
                config=WidgetConfig(data_source="TASK", dimension="bad_field", measure="task_id", aggregation="COUNT"),
            )
        )
