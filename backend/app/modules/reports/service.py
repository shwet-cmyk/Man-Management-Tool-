from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ref_employee import RefEmployee
from app.models.wm_exception_instance import WmExceptionInstance
from app.models.wm_expense_claim import WmExpenseClaim
from app.models.wm_job import WmJob
from app.models.wm_notification_queue import WmNotificationQueue
from app.models.wm_report import WmReport
from app.models.wm_report_config import WmReportConfig
from app.models.wm_report_schedule import WmReportSchedule
from app.models.wm_task import WmTask
from app.models.wm_timesheet import WmTimesheet
from app.modules.reports.schemas import (
    CreateReportRequest,
    CreateScheduleRequest,
    ExportReportRequest,
    RunReportRequest,
    SaveReportConfigRequest,
)


class ReportsService:
    MAX_PAGE_SIZE = 1000

    def __init__(self, db: Session):
        self.db = db

    def create_report(self, payload: CreateReportRequest):
        report = WmReport(name=payload.name, created_by=payload.created_by, is_public=payload.is_public)
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return {"report_id": report.report_id, "name": report.name, "is_public": report.is_public}

    def save_config(self, payload: SaveReportConfigRequest):
        report = self.db.query(WmReport).filter(WmReport.report_id == payload.report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        self._validate_config(payload)
        record = self.db.query(WmReportConfig).filter(WmReportConfig.report_id == payload.report_id).first()
        if not record:
            record = WmReportConfig(report_id=payload.report_id, data_source=payload.data_source, columns_json="[]")

        record.data_source = payload.data_source
        record.columns_json = json.dumps(payload.columns)
        record.filters_json = json.dumps(payload.filters)
        record.group_by = ",".join(payload.group_by)
        record.aggregation = json.dumps(payload.aggregation)

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return {"config_id": record.config_id, "report_id": record.report_id, "data_source": record.data_source}

    def run_report(self, payload: RunReportRequest):
        report, config = self._get_report_and_config(payload.report_id)
        self._validate_permission(report, payload.requested_by)

        page = max(payload.page, 1)
        page_size = min(max(payload.page_size, 1), self.MAX_PAGE_SIZE)

        rows = self._query_data(config, payload.filters)
        total_rows = len(rows)
        start = (page - 1) * page_size
        end = start + page_size
        page_rows = rows[start:end]
        return {
            "report_id": report.report_id,
            "name": report.name,
            "total_rows": total_rows,
            "page": page,
            "page_size": page_size,
            "rows": page_rows,
        }

    def export_report(self, payload: ExportReportRequest):
        run = self.run_report(
            RunReportRequest(
                report_id=payload.report_id,
                requested_by=payload.requested_by,
                filters=payload.filters,
                page=1,
                page_size=self.MAX_PAGE_SIZE,
            )
        )

        if payload.export_format in {"CSV", "EXCEL"}:
            output = io.StringIO()
            rows = run["rows"]
            writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()) if rows else [])
            if rows:
                writer.writeheader()
                for row in rows:
                    writer.writerow(row)
            return {
                "report_id": payload.report_id,
                "export_format": payload.export_format,
                "content_type": "text/csv",
                "content": output.getvalue(),
            }

        return {
            "report_id": payload.report_id,
            "export_format": "PDF",
            "content_type": "application/json",
            "content": json.dumps(run, default=str),
        }

    def create_schedule(self, payload: CreateScheduleRequest):
        _, _ = self._get_report_and_config(payload.report_id)
        if not payload.recipients:
            raise HTTPException(status_code=400, detail="At least one recipient required")
        schedule = WmReportSchedule(
            report_id=payload.report_id,
            frequency=payload.frequency,
            recipients=",".join(str(x) for x in payload.recipients),
            next_run=payload.next_run,
            export_format=payload.export_format,
        )
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        return {"schedule_id": schedule.schedule_id, "next_run": schedule.next_run}

    def run_due_schedules(self):
        now = datetime.utcnow()
        due = self.db.query(WmReportSchedule).filter(WmReportSchedule.next_run <= now).all()
        processed = 0
        for schedule in due:
            report, _ = self._get_report_and_config(schedule.report_id)
            recipients = [int(x) for x in schedule.recipients.split(",") if x.strip()]
            for recipient in recipients:
                self.db.add(
                    WmNotificationQueue(
                        task_id=0,
                        recipient_emp_id=recipient,
                        channel="EMAIL",
                        status="PENDING",
                        payload=json.dumps(
                            {
                                "report_id": report.report_id,
                                "report_name": report.name,
                                "export_format": schedule.export_format,
                            }
                        ),
                    )
                )
            schedule.next_run = self._next_run(schedule.next_run, schedule.frequency)
            processed += 1
        self.db.commit()
        return {"schedules_processed": processed}

    def standard_job_profitability(self, company_id: int | None = None):
        rows = self._job_rows(company_id=company_id)
        return {"items": rows, "totals": {"count": len(rows), "profit": sum((x["profit"] for x in rows), Decimal("0"))}}

    def standard_client_profitability(self, company_id: int | None = None):
        rows = self._job_rows(company_id=company_id)
        by_client = {}
        for row in rows:
            key = row["customer_id"]
            agg = by_client.setdefault(key, {"customer_id": key, "revenue": Decimal("0"), "cost": Decimal("0"), "profit": Decimal("0")})
            agg["revenue"] += row["revenue"]
            agg["cost"] += row["cost"]
            agg["profit"] += row["profit"]
        return {"items": list(by_client.values())}

    def standard_employee_productivity(self, company_id: int | None = None):
        rows = []
        q = self.db.query(WmTimesheet).filter(WmTimesheet.is_active.is_(True))
        if company_id is not None:
            q = q.filter(WmTimesheet.company_id == company_id)
        grouped = {}
        for t in q.all():
            key = t.emp_id
            x = grouped.setdefault(key, {"emp_id": key, "hours": Decimal("0"), "billable_hours": Decimal("0")})
            x["hours"] += Decimal(str(t.hours or 0))
            x["billable_hours"] += Decimal(str(t.billable_hours or 0))
        for x in grouped.values():
            x["utilization_pct"] = (x["billable_hours"] / x["hours"] * Decimal("100")) if x["hours"] else Decimal("0")
            rows.append(x)
        return {"items": rows}

    def standard_unbilled_work(self, company_id: int | None = None):
        rows = []
        q = self.db.query(WmTask).filter(WmTask.is_active.is_(True), WmTask.billable_flag.is_(True))
        if company_id is not None:
            q = q.filter(WmTask.company_id == company_id)
        for task in q.all():
            revenue = Decimal(str(task.billed_amount or 0))
            approved_hours = Decimal(str(
                self.db.query(func.coalesce(func.sum(WmTimesheet.billable_hours), 0)).filter(
                    WmTimesheet.task_id == task.task_id,
                    WmTimesheet.approval_status == "Approved",
                    WmTimesheet.is_active.is_(True),
                ).scalar()
            ))
            if approved_hours > 0 and revenue == 0:
                rows.append({"task_id": task.task_id, "job_id": task.job_id, "customer_id": task.customer_id, "approved_billable_hours": approved_hours})
        return {"items": rows}

    def standard_overrun_analysis(self, company_id: int | None = None):
        rows = []
        q = self.db.query(WmTask).filter(WmTask.is_active.is_(True))
        if company_id is not None:
            q = q.filter(WmTask.company_id == company_id)
        for task in q.all():
            planned = Decimal(str(task.estimated_hours or 0))
            actual = Decimal(str(
                self.db.query(func.coalesce(func.sum(WmTimesheet.hours), 0)).filter(
                    WmTimesheet.task_id == task.task_id,
                    WmTimesheet.approval_status == "Approved",
                    WmTimesheet.is_active.is_(True),
                ).scalar()
            ))
            if planned and actual > planned:
                rows.append({"task_id": task.task_id, "planned_hours": planned, "actual_hours": actual, "overrun_hours": actual - planned})
        return {"items": rows}

    def standard_exception_report(self, company_id: int | None = None):
        q = self.db.query(WmExceptionInstance).filter(WmExceptionInstance.is_active.is_(True))
        if company_id is not None:
            q = q.filter(WmExceptionInstance.company_id == company_id)
        items = q.all()
        by_type = {}
        for row in items:
            by_type[row.exception_type] = by_type.get(row.exception_type, 0) + 1
        return {"items": [{"exception_type": k, "count": v} for k, v in by_type.items()], "totals": {"count": len(items)}}

    def _query_data(self, config: WmReportConfig, runtime_filters: dict):
        columns = json.loads(config.columns_json or "[]")
        base_filters = json.loads(config.filters_json or "{}")
        filters = {**base_filters, **(runtime_filters or {})}
        group_by = [x for x in (config.group_by or "").split(",") if x]
        aggregation = json.loads(config.aggregation or "{}")

        rows = self._job_rows(filters=filters) if config.data_source == "JOB" else self._employee_rows(filters=filters)

        if group_by:
            grouped = {}
            for row in rows:
                key = tuple(row.get(k) for k in group_by)
                if key not in grouped:
                    grouped[key] = {k: row.get(k) for k in group_by}
                    for col in columns:
                        if col not in grouped[key] and col not in group_by:
                            grouped[key][col] = row.get(col)
                for field, fn_name in aggregation.items():
                    value = Decimal(str(row.get(field) or 0))
                    if fn_name in {"sum", "avg"}:
                        grouped[key][field] = Decimal(str(grouped[key].get(field) or 0)) + value
                    elif fn_name == "count":
                        grouped[key][field] = int(grouped[key].get(field) or 0) + 1
                    elif fn_name == "max":
                        grouped[key][field] = value if field not in grouped[key] else max(Decimal(str(grouped[key][field])), value)
                    elif fn_name == "min":
                        grouped[key][field] = value if field not in grouped[key] else min(Decimal(str(grouped[key][field])), value)
            rows = list(grouped.values())

        if columns:
            rows = [{k: row.get(k) for k in columns if k in row} for row in rows]
        return rows

    def _job_rows(self, company_id: int | None = None, filters: dict | None = None):
        filters = filters or {}
        jobs = self.db.query(WmJob).filter(WmJob.is_active.is_(True))
        if company_id is not None:
            jobs = jobs.filter(WmJob.company_id == company_id)
        if filters.get("company_id") is not None:
            jobs = jobs.filter(WmJob.company_id == filters["company_id"])
        if filters.get("department_id") is not None:
            jobs = jobs.filter(WmJob.department_id == filters["department_id"])
        if filters.get("customer_id") is not None:
            jobs = jobs.filter(WmJob.customer_id == filters["customer_id"])

        rows = []
        for job in jobs.all():
            revenue = Decimal(str(self.db.query(func.coalesce(func.sum(WmTask.billed_amount), 0)).filter(WmTask.job_id == job.job_id, WmTask.is_active.is_(True)).scalar()))
            labor_hours = Decimal(str(self.db.query(func.coalesce(func.sum(WmTimesheet.hours), 0)).filter(WmTimesheet.job_id == job.job_id, WmTimesheet.approval_status == "Approved", WmTimesheet.is_active.is_(True)).scalar()))
            expense_total = Decimal(str(self.db.query(func.coalesce(func.sum(WmExpenseClaim.total_amount), 0)).filter(WmExpenseClaim.job_id == job.job_id, WmExpenseClaim.approval_status == "Approved", WmExpenseClaim.is_active.is_(True)).scalar()))

            avg_cost_rate = Decimal(str(self.db.query(func.coalesce(func.avg(RefEmployee.hourly_cost), 0)).filter(RefEmployee.company_id == job.company_id, RefEmployee.is_active.is_(True)).scalar() or 0))
            labor_cost = labor_hours * avg_cost_rate
            cost = labor_cost + expense_total
            approved_billable = Decimal(str(self.db.query(func.coalesce(func.sum(WmTimesheet.billable_hours), 0)).filter(WmTimesheet.job_id == job.job_id, WmTimesheet.approval_status == "Approved", WmTimesheet.is_active.is_(True)).scalar()))
            planned_hours = Decimal(str(self.db.query(func.coalesce(func.sum(WmTask.estimated_hours), 0)).filter(WmTask.job_id == job.job_id, WmTask.is_active.is_(True)).scalar()))
            actual_hours = labor_hours
            overrun_hours = max(actual_hours - planned_hours, Decimal("0"))
            exception_count = self.db.query(func.count(WmExceptionInstance.exception_instance_id)).filter(WmExceptionInstance.job_id == job.job_id, WmExceptionInstance.is_active.is_(True)).scalar() or 0

            rows.append(
                {
                    "company_id": job.company_id,
                    "branch_id": job.branch_id,
                    "department_id": job.department_id,
                    "customer_id": job.customer_id,
                    "job_id": job.job_id,
                    "job_name": job.job_name,
                    "manager_id": job.manager_id,
                    "revenue": revenue,
                    "cost": cost,
                    "profit": revenue - cost,
                    "approved_hours": labor_hours,
                    "billable_hours": approved_billable,
                    "unbilled_amount": max(approved_billable * Decimal("100") - revenue, Decimal("0")),
                    "planned_hours": planned_hours,
                    "actual_hours": actual_hours,
                    "overrun_hours": overrun_hours,
                    "exception_count": int(exception_count),
                }
            )
        return rows

    def _employee_rows(self, filters: dict | None = None):
        filters = filters or {}
        q = self.db.query(RefEmployee).filter(RefEmployee.is_active.is_(True))
        if filters.get("company_id") is not None:
            q = q.filter(RefEmployee.company_id == filters["company_id"])
        if filters.get("department_id") is not None:
            q = q.filter(RefEmployee.department_id == filters["department_id"])
        rows = []
        for emp in q.all():
            hours = Decimal(str(self.db.query(func.coalesce(func.sum(WmTimesheet.hours), 0)).filter(WmTimesheet.emp_id == emp.emp_id, WmTimesheet.approval_status == "Approved", WmTimesheet.is_active.is_(True)).scalar()))
            billable_hours = Decimal(str(self.db.query(func.coalesce(func.sum(WmTimesheet.billable_hours), 0)).filter(WmTimesheet.emp_id == emp.emp_id, WmTimesheet.approval_status == "Approved", WmTimesheet.is_active.is_(True)).scalar()))
            rows.append(
                {
                    "company_id": emp.company_id,
                    "branch_id": emp.branch_id,
                    "department_id": emp.department_id,
                    "emp_id": emp.emp_id,
                    "employee_name": emp.employee_name,
                    "hours": hours,
                    "billable_hours": billable_hours,
                    "utilization_pct": (billable_hours / hours * Decimal("100")) if hours else Decimal("0"),
                    "cost": Decimal(str(emp.hourly_cost or 0)) * hours,
                }
            )
        return rows

    def _validate_config(self, payload: SaveReportConfigRequest):
        allowed_columns = {
            "JOB": {
                "company_id", "branch_id", "department_id", "customer_id", "job_id", "job_name", "manager_id",
                "revenue", "cost", "profit", "approved_hours", "billable_hours", "unbilled_amount",
                "planned_hours", "actual_hours", "overrun_hours", "exception_count",
            },
            "EMPLOYEE": {
                "company_id", "branch_id", "department_id", "emp_id", "employee_name", "hours", "billable_hours", "utilization_pct", "cost",
            },
        }
        source_columns = allowed_columns[payload.data_source]
        if not payload.columns:
            raise HTTPException(status_code=400, detail="At least one column must be selected")
        bad = [x for x in payload.columns if x not in source_columns]
        if bad:
            raise HTTPException(status_code=400, detail=f"Unsupported columns: {', '.join(bad)}")
        bad_group = [x for x in payload.group_by if x not in source_columns]
        if bad_group:
            raise HTTPException(status_code=400, detail=f"Unsupported group_by: {', '.join(bad_group)}")
        bad_agg = [x for x in payload.aggregation if x not in source_columns]
        if bad_agg:
            raise HTTPException(status_code=400, detail=f"Unsupported aggregation fields: {', '.join(bad_agg)}")

    def _get_report_and_config(self, report_id: int):
        report = self.db.query(WmReport).filter(WmReport.report_id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        config = self.db.query(WmReportConfig).filter(WmReportConfig.report_id == report_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="Report config not found")
        return report, config

    @staticmethod
    def _validate_permission(report: WmReport, requested_by: int):
        if not report.is_public and report.created_by != requested_by:
            raise HTTPException(status_code=403, detail="Access denied")

    @staticmethod
    def _next_run(current_next_run: datetime, frequency: str):
        if frequency == "DAILY":
            return current_next_run + timedelta(days=1)
        if frequency == "WEEKLY":
            return current_next_run + timedelta(days=7)
        return current_next_run + timedelta(days=30)
