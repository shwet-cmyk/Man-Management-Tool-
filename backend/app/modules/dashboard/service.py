from __future__ import annotations

import json
from datetime import date

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.wm_billing_document_link import WmBillingDocumentLink
from app.models.wm_dashboard import WmDashboard
from app.models.wm_dashboard_widget import WmDashboardWidget
from app.models.wm_exception_instance import WmExceptionInstance
from app.models.wm_expense_claim import WmExpenseClaim
from app.models.wm_job import WmJob
from app.models.wm_task import WmTask
from app.models.wm_task_participant import WmTaskParticipant
from app.models.wm_timesheet import WmTimesheet
from app.models.wm_widget_query import WmWidgetQuery
from app.modules.dashboard.schemas import DashboardCreateRequest, WidgetAddRequest, WidgetDataRequest


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def create_dashboard(self, payload: DashboardCreateRequest) -> dict:
        if not payload.name.strip():
            raise HTTPException(status_code=422, detail="Dashboard name is required")
        row = WmDashboard(name=payload.name.strip(), user_id=payload.user_id, role_id=payload.role_id, is_default=payload.is_default)
        self.db.add(row)
        self.db.commit()
        return {"status": "SUCCESS", "dashboard_id": row.dashboard_id, "message": "Dashboard created successfully"}

    def add_widget(self, payload: WidgetAddRequest) -> dict:
        dashboard = self.db.query(WmDashboard).filter(WmDashboard.dashboard_id == payload.dashboard_id).first()
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")

        config = payload.config.model_dump()
        if payload.widget_type == "KPI" and config.get("dimension"):
            raise HTTPException(status_code=422, detail="KPI widget cannot have dimension")

        self._validate_query_config(config)

        widget = WmDashboardWidget(
            dashboard_id=payload.dashboard_id,
            widget_type=payload.widget_type,
            title=payload.title,
            position_x=payload.position_x,
            position_y=payload.position_y,
            width=payload.width,
            height=payload.height,
            config_json=json.dumps(config),
        )
        self.db.add(widget)
        self.db.flush()

        self.db.add(
            WmWidgetQuery(
                widget_id=widget.widget_id,
                data_source=config["data_source"],
                dimension_field=config.get("dimension"),
                measure_field=config["measure"],
                aggregation=config["aggregation"],
                filter_json="{}",
            )
        )
        self.db.commit()
        return {"status": "SUCCESS", "widget_id": widget.widget_id, "message": "Widget added successfully"}

    def get_dashboard(self, dashboard_id: int) -> dict:
        row = self.db.query(WmDashboard).filter(WmDashboard.dashboard_id == dashboard_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        widgets = self.db.query(WmDashboardWidget).filter(WmDashboardWidget.dashboard_id == dashboard_id).order_by(WmDashboardWidget.position_y, WmDashboardWidget.position_x).all()
        return {
            "dashboard_id": row.dashboard_id,
            "name": row.name,
            "user_id": row.user_id,
            "role_id": row.role_id,
            "is_default": row.is_default,
            "widgets": [
                {
                    "widget_id": w.widget_id,
                    "widget_type": w.widget_type,
                    "title": w.title,
                    "position_x": w.position_x,
                    "position_y": w.position_y,
                    "width": w.width,
                    "height": w.height,
                    "config": json.loads(w.config_json),
                }
                for w in widgets
            ],
        }

    def get_widget_data(self, payload: WidgetDataRequest) -> dict:
        widget = self.db.query(WmDashboardWidget).filter(WmDashboardWidget.widget_id == payload.widget_id).first()
        if not widget:
            raise HTTPException(status_code=404, detail="Widget not found")
        config = json.loads(widget.config_json)
        rows = self._run_query(config, payload.filters or {})
        return {"status": "SUCCESS", "widget_id": payload.widget_id, "data": rows}

    def _validate_query_config(self, config: dict) -> None:
        source = config["data_source"]
        dimension = config.get("dimension")
        measure = config["measure"]

        allowed = {
            "JOB": {"dimensions": {"company_id", "branch_id", "department_id", "customer_id", "execution_status", "billing_status"}, "measures": {"job_id": "count", "planned_amount": "numeric"}},
            "TASK": {"dimensions": {"company_id", "branch_id", "department_id", "customer_id", "status_code", "priority_code", "manager_emp_id"}, "measures": {"task_id": "count", "estimated_hours": "numeric", "billed_amount": "numeric"}},
            "PARTICIPANT": {"dimensions": {"task_id", "role_code", "participant_status", "emp_id"}, "measures": {"task_participant_id": "count", "allocation_pct": "numeric"}},
            "TIMESHEET": {"dimensions": {"company_id", "branch_id", "department_id", "customer_id", "emp_id", "job_id", "task_id", "approval_status"}, "measures": {"timesheet_id": "count", "hours": "numeric", "billable_hours": "numeric", "overtime_hours": "numeric"}},
            "EXPENSE": {"dimensions": {"company_id", "branch_id", "department_id", "customer_id", "emp_id", "job_id", "task_id", "approval_status", "expense_type"}, "measures": {"claim_id": "count", "total_amount": "numeric"}},
            "BILLING": {"dimensions": {"entity_type", "job_id", "task_id", "billing_status", "billing_reference_type"}, "measures": {"billing_document_link_id": "count", "billed_amount": "numeric"}},
            "EXCEPTION": {"dimensions": {"exception_type", "severity", "entity_type", "company_id", "manager_id"}, "measures": {"exception_instance_id": "count", "days_delayed": "numeric", "exception_age_days": "numeric"}},
        }
        if source not in allowed:
            raise HTTPException(status_code=422, detail="Unsupported data source")
        if dimension and dimension not in allowed[source]["dimensions"]:
            raise HTTPException(status_code=422, detail="Invalid dimension field")
        if measure not in allowed[source]["measures"]:
            raise HTTPException(status_code=422, detail="Invalid measure field")

    def _run_query(self, config: dict, filters: dict) -> list[dict]:
        source = config["data_source"]
        dimension = config.get("dimension")
        measure = config["measure"]
        aggregation = config["aggregation"]

        table_map = {
            "JOB": WmJob,
            "TASK": WmTask,
            "PARTICIPANT": WmTaskParticipant,
            "TIMESHEET": WmTimesheet,
            "EXPENSE": WmExpenseClaim,
            "BILLING": WmBillingDocumentLink,
            "EXCEPTION": WmExceptionInstance,
        }
        model = table_map[source]
        query = self.db.query(model)

        # scope filters (role-based gate placeholder by explicit filter)
        for field in ["company_id", "branch_id", "department_id", "customer_id", "manager_id", "job_id", "task_id", "emp_id"]:
            if field in filters and hasattr(model, field):
                query = query.filter(getattr(model, field) == filters[field])

        date_from = self._parse_date(filters.get("date_from"))
        date_to = self._parse_date(filters.get("date_to"))
        date_column = self._date_column(model)
        if date_column is not None and date_from:
            query = query.filter(date_column >= date_from)
        if date_column is not None and date_to:
            query = query.filter(date_column <= date_to)

        measure_col = getattr(model, measure)
        if aggregation == "COUNT":
            agg_expr = func.count(measure_col)
        elif aggregation == "AVG":
            agg_expr = func.avg(measure_col)
        else:
            agg_expr = func.sum(measure_col)

        if dimension:
            dim_col = getattr(model, dimension)
            rows = query.with_entities(dim_col.label("x"), agg_expr.label("y")).group_by(dim_col).all()
            return [{"x": x, "y": y or 0} for x, y in rows]

        value = query.with_entities(agg_expr.label("y")).scalar() or 0
        return [{"x": "KPI", "y": value}]

    def _date_column(self, model):
        for name in ["work_date", "expense_date", "billed_date", "created_on", "last_evaluated_on"]:
            if hasattr(model, name):
                return getattr(model, name)
        return None

    def _parse_date(self, value):
        if not value:
            return None
        if isinstance(value, date):
            return value
        return date.fromisoformat(value)
