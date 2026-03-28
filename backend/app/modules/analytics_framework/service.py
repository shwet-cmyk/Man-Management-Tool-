from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.wm_job import WmJob
from app.models.wm_job_task_line import WmJobTaskLine
from app.models.wm_man_approval import WmManApproval
from app.models.wm_task import WmTask
from app.models.wm_ticket import WmTicket
from app.models.wm_timesheet import WmTimesheet
from app.modules.analytics_framework.metric_catalog import METRIC_CATALOG, WIDGET_LIBRARY
from app.modules.analytics_framework.schemas import AnalyticsFilter, DrilldownRequest, TrendQueryRequest, WidgetQueryRequest


class AnalyticsEngine:
    def __init__(self, db: Session):
        self.db = db

    def metric_catalog(self) -> dict:
        return {"status": "success", "metrics": METRIC_CATALOG, "widget_library": WIDGET_LIBRARY}

    def summary_cards(self, filters: AnalyticsFilter) -> dict:
        data = {}
        for metric in WIDGET_LIBRARY["summary_cards"]:
            data[metric] = self._compute_metric(metric, filters)
        return {"status": "success", "widget_type": "summary_cards", "data": data}

    def widget_dataset(self, payload: WidgetQueryRequest) -> dict:
        rows = self._group_metric(payload.metric_code, payload.group_by, payload.filters, payload.top_n)
        return {
            "status": "success",
            "widget_type": payload.widget_type,
            "metric_code": payload.metric_code,
            "group_by": payload.group_by,
            "rows": rows,
            "drilldown": {"entity_hint": METRIC_CATALOG.get(payload.metric_code, {}).get("entity"), "filters": payload.filters.model_dump()},
        }

    def trend_dataset(self, payload: TrendQueryRequest) -> dict:
        entity = METRIC_CATALOG.get(payload.metric_code, {}).get("entity", "job")
        rows = self._entity_rows(entity, payload.filters)
        series = defaultdict(lambda: Decimal("0"))
        for row in rows:
            dt = self._entity_date(entity, row)
            if not dt:
                continue
            key = self._grain_key(dt, payload.grain)
            series[key] += Decimal(str(self._row_value(payload.metric_code, entity, row)))
        return {"status": "success", "metric_code": payload.metric_code, "grain": payload.grain, "series": [{"period": k, "value": float(v)} for k, v in sorted(series.items())]}

    def leaderboard(self, metric_code: str, group_by: str, filters: AnalyticsFilter, top_n: int = 10) -> dict:
        rows = self._group_metric(metric_code, [group_by], filters, top_n)
        return {"status": "success", "metric_code": metric_code, "leaderboard": rows}

    def comparison(self, metric_code: str, left_filters: AnalyticsFilter, right_filters: AnalyticsFilter) -> dict:
        left = self._compute_metric(metric_code, left_filters)
        right = self._compute_metric(metric_code, right_filters)
        delta = Decimal(str(left)) - Decimal(str(right))
        return {"status": "success", "metric_code": metric_code, "left": left, "right": right, "delta": float(delta)}

    def matrix(self, metric_code: str, row_dim: str, col_dim: str, filters: AnalyticsFilter, top_n: int = 20) -> dict:
        rows = self._entity_rows(METRIC_CATALOG.get(metric_code, {}).get("entity", "job"), filters)
        matrix = defaultdict(lambda: defaultdict(lambda: Decimal("0")))
        for row in rows:
            r_key = self._dimension_value(row_dim, row)
            c_key = self._dimension_value(col_dim, row)
            matrix[r_key][c_key] += Decimal(str(self._row_value(metric_code, METRIC_CATALOG.get(metric_code, {}).get("entity", "job"), row)))
        out = []
        for r, cols in matrix.items():
            out.append({"row": r, "columns": {k: float(v) for k, v in cols.items()}})
        out = sorted(out, key=lambda x: sum(x["columns"].values()), reverse=True)[:top_n]
        return {"status": "success", "metric_code": metric_code, "row_dim": row_dim, "col_dim": col_dim, "rows": out}

    def drilldown(self, payload: DrilldownRequest) -> dict:
        entity = payload.entity_type
        rows = self._entity_rows(entity, payload.filters)
        if entity == "job":
            out = [{"job_id": r.job_id, "job_no": r.job_no, "status": r.execution_status, "billing_status": r.billing_status, "employee_id": r.assigned_employee_id, "manager_id": r.manager_id, "client_id": r.customer_id} for r in rows]
        elif entity == "timesheet":
            out = [{"timesheet_id": r.timesheet_id, "job_id": r.job_id, "employee_id": r.emp_id, "date": r.work_date, "hours": float(r.hours), "approval_status": r.approval_status} for r in rows]
        elif entity == "task":
            out = [{"task_id": r.task_id, "task_no": r.task_no, "status": r.status_code, "source_type": r.source_type, "client_id": r.customer_id} for r in rows]
        elif entity == "ticket":
            out = [{"ticket_id": r.ticket_id, "ticket_no": r.ticket_no, "status": r.status, "priority": r.priority, "client_name": r.customer_name} for r in rows]
        elif entity == "approval":
            out = [{"approval_id": r.approval_id, "entity_type": r.entity_type, "entity_id": r.entity_id, "status": r.current_status} for r in rows]
        elif entity == "client":
            jobs = self._entity_rows("job", payload.filters)
            grouped = defaultdict(int)
            for j in jobs:
                grouped[j.customer_id] += 1
            out = [{"client_id": k, "job_count": v} for k, v in grouped.items()]
        else:
            ts = self._entity_rows("timesheet", payload.filters)
            grouped = defaultdict(lambda: Decimal("0"))
            for t in ts:
                grouped[t.emp_id] += Decimal(str(t.hours or 0))
            out = [{"employee_id": k, "hours": float(v)} for k, v in grouped.items()]
        return {"status": "success", "entity_type": entity, "rows": out}

    # ---- Internal helpers ----
    def _compute_metric(self, metric_code: str, filters: AnalyticsFilter):
        conf = METRIC_CATALOG.get(metric_code)
        if not conf:
            return 0
        rows = self._entity_rows(conf["entity"], filters)
        return float(sum(Decimal(str(self._row_value(metric_code, conf["entity"], row))) for row in rows))

    def _group_metric(self, metric_code: str, group_by: list[str], filters: AnalyticsFilter, top_n: int):
        conf = METRIC_CATALOG.get(metric_code, {})
        entity = conf.get("entity", "job")
        rows = self._entity_rows(entity, filters)
        buckets = defaultdict(lambda: Decimal("0"))
        record_ids = defaultdict(list)
        for row in rows:
            key = tuple(self._dimension_value(dim, row) for dim in (group_by or ["all"]))
            buckets[key] += Decimal(str(self._row_value(metric_code, entity, row)))
            rid = self._entity_id(entity, row)
            if rid is not None:
                record_ids[key].append(rid)
        out = [{"group": list(k), "value": float(v), "record_ids": record_ids[k][:100]} for k, v in buckets.items()]
        out.sort(key=lambda x: x["value"], reverse=True)
        return out[:top_n]

    def _entity_rows(self, entity: str, filters: AnalyticsFilter):
        if entity == "job":
            rows = self.db.query(WmJob).filter(WmJob.is_active.is_(True)).all()
            return [x for x in rows if self._match_job(x, filters)]
        if entity == "timesheet":
            rows = self.db.query(WmTimesheet).filter(WmTimesheet.is_active.is_(True)).all()
            return [x for x in rows if self._match_timesheet(x, filters)]
        if entity == "task":
            rows = self.db.query(WmTask).filter(WmTask.is_active.is_(True)).all()
            return [x for x in rows if self._match_task(x, filters)]
        if entity == "ticket":
            rows = self.db.query(WmTicket).all()
            return [x for x in rows if self._match_ticket(x, filters)]
        if entity == "approval":
            rows = self.db.query(WmManApproval).all()
            return [x for x in rows if self._match_approval(x, filters)]
        if entity == "job_task":
            return self.db.query(WmJobTaskLine).all()
        return []

    def _row_value(self, metric_code: str, entity: str, row):
        conf = METRIC_CATALOG.get(metric_code, {})
        if conf.get("measure") == "count":
            if not self._count_condition(conf, row):
                return 0
            return 1
        if conf.get("measure") == "sum":
            return self._field_value(conf.get("field"), entity, row)
        if conf.get("measure") == "ratio":
            num = self._field_value(conf.get("numerator"), entity, row)
            den = self._field_value(conf.get("denominator"), entity, row)
            return Decimal("0") if Decimal(str(den)) == 0 else (Decimal(str(num)) / Decimal(str(den))) * Decimal("100")
        return 0

    def _field_value(self, field: str, entity: str, row):
        if field == "expected_hours":
            return Decimal(str(row.planned_hours or 0)) + (Decimal(str(row.planned_minutes or 0)) / Decimal("60"))
        if field == "actual_hours":
            return Decimal(str(row.spent_hours or 0))
        if field == "billable_hours":
            return Decimal(str(getattr(row, "billable_hours", 0) or 0))
        if field == "non_billable_hours":
            hours = Decimal(str(getattr(row, "hours", 0) or 0))
            billable = Decimal(str(getattr(row, "billable_hours", 0) or 0))
            return max(Decimal("0"), hours - billable)
        if field == "labor_cost":
            return Decimal(str(getattr(row, "cost_to_company", 0) or 0))
        if field == "expense_total":
            return Decimal(str(getattr(row, "expense_total", 0) or 0))
        if field == "reimbursement_total":
            return Decimal(str(getattr(row, "reimbursement_total", 0) or 0))
        if field == "overhead":
            return Decimal(str(getattr(row, "overhead_amount", 0) or 0))
        if field == "total_cost_to_company":
            return Decimal(str(getattr(row, "final_cost_to_company", 0) or 0))
        if field == "billed_amount":
            return Decimal(str(getattr(row, "billed_amount", 0) or 0))
        if field == "profit_positive":
            pnl = Decimal(str(getattr(row, "profit_or_loss", 0) or 0))
            return pnl if pnl > 0 else Decimal("0")
        if field == "loss_positive":
            pnl = Decimal(str(getattr(row, "profit_or_loss", 0) or 0))
            return abs(pnl) if pnl < 0 else Decimal("0")
        if field == "profit":
            return Decimal(str(getattr(row, "profit_or_loss", 0) or 0))
        return Decimal("0")

    def _count_condition(self, conf, row):
        if conf.get("status_in") and getattr(row, "execution_status", getattr(row, "status", None)) not in conf["status_in"]:
            return False
        if conf.get("billable") is not None and bool(getattr(row, "is_billable", False)) != bool(conf["billable"]):
            return False
        if conf.get("overdue"):
            due = getattr(row, "due_date", None)
            status = getattr(row, "execution_status", "")
            if not due or due >= datetime.utcnow().date() or status in {"Completed", "Billed", "Closed", "Cancelled"}:
                return False
        if conf.get("critical") is not None and bool(getattr(row, "critical_flag", False)) != bool(conf["critical"]):
            return False
        if conf.get("billing_status_in") and getattr(row, "billing_status", None) not in conf["billing_status_in"]:
            return False
        if conf.get("rollover_gte") is not None and int(getattr(row, "rollover_count", 0) or 0) < int(conf["rollover_gte"]):
            return False
        if conf.get("transfer_status_in") and getattr(row, "transfer_status", None) not in conf["transfer_status_in"]:
            return False
        if conf.get("approval_status_in") and getattr(row, "current_status", None) not in conf["approval_status_in"]:
            return False
        return True

    def _dimension_value(self, dim, row):
        mapping = {
            "all": "ALL",
            "employee": getattr(row, "assigned_employee_id", getattr(row, "emp_id", None)),
            "manager": getattr(row, "manager_id", None),
            "task_owner": getattr(row, "primary_owner_emp_id", None),
            "company": getattr(row, "company_id", None),
            "branch": getattr(row, "branch_id", None),
            "department": getattr(row, "department_id", None),
            "client": getattr(row, "customer_id", None),
            "product": getattr(row, "product", None),
            "category": getattr(row, "category", None),
            "service": getattr(row, "service_id", None),
            "priority": getattr(row, "priority", getattr(row, "priority_code", None)),
            "status": getattr(row, "execution_status", getattr(row, "status", None)),
            "billable_flag": bool(getattr(row, "is_billable", getattr(row, "billable_flag", False))),
            "critical_flag": bool(getattr(row, "critical_flag", False)),
            "approval_status": getattr(row, "approval_status", getattr(row, "current_status", None)),
            "billing_readiness": getattr(row, "billing_status", None),
            "source_type": getattr(row, "source_type", None),
        }
        return mapping.get(dim, getattr(row, dim, None))

    def _entity_date(self, entity, row):
        if entity == "job":
            return row.start_date
        if entity == "timesheet":
            return row.work_date
        if entity == "task":
            return row.created_on.date() if row.created_on else None
        if entity == "ticket":
            return row.created_on.date() if row.created_on else None
        if entity == "approval":
            return row.requested_at.date() if row.requested_at else None
        return None

    def _grain_key(self, dt: date, grain: str):
        if grain == "day":
            return dt.isoformat()
        if grain == "week":
            y, w, _ = dt.isocalendar()
            return f"{y}-W{w:02d}"
        if grain == "month":
            return f"{dt.year}-{dt.month:02d}"
        if grain == "quarter":
            q = ((dt.month - 1) // 3) + 1
            return f"{dt.year}-Q{q}"
        return f"{dt.year}"

    def _entity_id(self, entity, row):
        return {
            "job": getattr(row, "job_id", None),
            "timesheet": getattr(row, "timesheet_id", None),
            "task": getattr(row, "task_id", None),
            "ticket": getattr(row, "ticket_id", None),
            "approval": getattr(row, "approval_id", None),
            "job_task": getattr(row, "job_task_id", None),
        }.get(entity)

    def _match_job(self, r, f: AnalyticsFilter):
        if f.company_id and r.company_id != f.company_id: return False
        if f.branch_id and r.branch_id != f.branch_id: return False
        if f.department_id and r.department_id != f.department_id: return False
        if f.employee_id and r.assigned_employee_id != f.employee_id: return False
        if f.manager_id and r.manager_id != f.manager_id: return False
        if f.client_id and r.customer_id != f.client_id: return False
        if f.priority and str(r.priority) != str(f.priority): return False
        if f.status and str(r.execution_status) != str(f.status): return False
        if f.billable_flag is not None and bool(r.is_billable) != bool(f.billable_flag): return False
        if f.critical_flag is not None and bool(r.critical_flag) != bool(f.critical_flag): return False
        if f.overdue_flag:
            if not (r.due_date and r.due_date < datetime.utcnow().date() and r.execution_status not in {"Completed", "Billed", "Closed", "Cancelled"}):
                return False
        if f.billing_readiness and str(r.billing_status) != str(f.billing_readiness): return False
        if f.date_from and r.start_date and r.start_date < f.date_from: return False
        if f.date_to and r.start_date and r.start_date > f.date_to: return False
        return True

    def _match_timesheet(self, r, f: AnalyticsFilter):
        if f.company_id and r.company_id != f.company_id: return False
        if f.branch_id and r.branch_id != f.branch_id: return False
        if f.department_id and r.department_id != f.department_id: return False
        if f.employee_id and r.emp_id != f.employee_id: return False
        if f.client_id and r.customer_id != f.client_id: return False
        if f.approval_status and str(r.approval_status) != str(f.approval_status): return False
        if f.date_from and r.work_date < f.date_from: return False
        if f.date_to and r.work_date > f.date_to: return False
        return True

    def _match_task(self, r, f):
        if f.company_id and r.company_id != f.company_id: return False
        if f.branch_id and r.branch_id != f.branch_id: return False
        if f.department_id and r.department_id != f.department_id: return False
        if f.client_id and r.customer_id != f.client_id: return False
        if f.priority and str(r.priority_code) != str(f.priority): return False
        if f.status and str(r.status_code) != str(f.status): return False
        if f.billable_flag is not None and bool(r.billable_flag) != bool(f.billable_flag): return False
        if f.source_type and str(r.source_type) != str(f.source_type): return False
        return True

    def _match_ticket(self, r, f):
        if f.company_id and r.company_id != f.company_id: return False
        if f.branch_id and r.branch_id != f.branch_id: return False
        if f.department_id and r.department_id != f.department_id: return False
        if f.client_id and r.customer_id != f.client_id: return False
        if f.priority and str(r.priority) != str(f.priority): return False
        if f.status and str(r.status) != str(f.status): return False
        return True

    def _match_approval(self, r, f):
        if f.approval_status and str(r.current_status) != str(f.approval_status): return False
        return True


# Named services for modularity and future extension.
class EmployeeAnalyticsService(AnalyticsEngine):
    pass


class ClientAnalyticsService(AnalyticsEngine):
    pass


class TaskAnalyticsService(AnalyticsEngine):
    pass


class JobAnalyticsService(AnalyticsEngine):
    pass


class TimesheetAnalyticsService(AnalyticsEngine):
    pass


class CostingAnalyticsService(AnalyticsEngine):
    pass


class ProfitabilityAnalyticsService(AnalyticsEngine):
    pass


class RolloverAnalyticsService(AnalyticsEngine):
    pass


class DependencyAnalyticsService(AnalyticsEngine):
    pass


class DashboardAggregationService(AnalyticsEngine):
    pass
