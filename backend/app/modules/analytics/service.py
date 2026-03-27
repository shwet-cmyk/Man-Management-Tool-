from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ref_employee import RefEmployee
from app.models.wm_billing_configuration import WmBillingConfiguration
from app.models.wm_billing_document_link import WmBillingDocumentLink
from app.models.wm_billing_readiness import WmBillingReadiness
from app.models.wm_exception_history import WmExceptionHistory
from app.models.wm_exception_instance import WmExceptionInstance
from app.models.wm_expense_claim import WmExpenseClaim
from app.models.wm_job import WmJob
from app.models.wm_task import WmTask
from app.models.wm_task_participant import WmTaskParticipant
from app.models.wm_task_participant_dependency import WmTaskParticipantDependency
from app.models.wm_timesheet import WmTimesheet
from app.models.wm_sales_history import WmSalesHistory


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_profitability(self, **filters):
        rows = self._build_rows(**filters)
        items = [self._finalize_row(filters["entity_type"], row) for row in rows.values()]
        total_cost = sum((x["total_cost"] for x in items), Decimal("0"))
        billed_amount = sum((x["billed_amount"] for x in items), Decimal("0"))
        profit_amount = sum((x["profit_amount"] for x in items), Decimal("0"))
        return {
            "items": items,
            "totals": {
                "total_cost": total_cost,
                "billed_amount": billed_amount,
                "profit_amount": profit_amount,
            },
        }

    def get_exception_queue(self, **filters):
        q = self.db.query(WmExceptionInstance).filter(WmExceptionInstance.is_active.is_(True))
        if filters.get("exception_type"):
            q = q.filter(WmExceptionInstance.exception_type == filters["exception_type"])
        if filters.get("entity_type"):
            q = q.filter(WmExceptionInstance.entity_type == filters["entity_type"])
        if filters.get("company_id") is not None:
            q = q.filter(WmExceptionInstance.company_id == filters["company_id"])
        if filters.get("manager_id") is not None:
            q = q.filter(WmExceptionInstance.manager_id == filters["manager_id"])

        d_from = self._parse_date(filters.get("date_from"))
        d_to = self._parse_date(filters.get("date_to"))
        if d_from:
            q = q.filter(WmExceptionInstance.last_evaluated_on >= datetime.combine(d_from, datetime.min.time()))
        if d_to:
            q = q.filter(WmExceptionInstance.last_evaluated_on <= datetime.combine(d_to, datetime.max.time()))

        items = []
        for x in q.all():
            items.append(
                {
                    "exception_type": x.exception_type,
                    "severity": x.severity,
                    "entity_type": x.entity_type,
                    "entity_id": x.entity_id,
                    "entity_name": None,
                    "company_id": x.company_id,
                    "branch_id": x.branch_id,
                    "department_id": x.department_id,
                    "customer_id": x.customer_id,
                    "job_id": x.job_id,
                    "task_id": x.task_id,
                    "task_participant_id": x.task_participant_id,
                    "emp_id": x.emp_id,
                    "manager_id": x.manager_id,
                    "planned_due": x.planned_due,
                    "planned_hours": x.planned_hours,
                    "actual_hours": x.actual_hours,
                    "billed_amount": x.billed_amount,
                    "total_cost": x.total_cost,
                    "days_delayed": x.days_delayed,
                    "exception_age_days": x.exception_age_days,
                    "exception_message": x.exception_message,
                }
            )
        return {"items": items, "totals": {"count": len(items)}}

    def refresh_exceptions(self, company_id: int | None = None, entity_scope: str = "ALL", user_id: int = 1):
        items = self._detect_exceptions(company_id=company_id, entity_scope=entity_scope)
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        active_rows = self.db.query(WmExceptionInstance).filter(WmExceptionInstance.is_active.is_(True))
        if company_id is not None:
            active_rows = active_rows.filter(WmExceptionInstance.company_id == company_id)
        active_rows = active_rows.all()

        for row in active_rows:
            row.is_active = False
            row.resolved_on = now
            row.resolved_by = user_id
            self.db.add(
                WmExceptionHistory(
                    exception_instance_id=row.exception_instance_id,
                    old_is_active=True,
                    new_is_active=False,
                    old_severity=row.severity,
                    new_severity=row.severity,
                    action_code="RESOLVE",
                    action_note="Replaced by refresh",
                    acted_by=user_id,
                )
            )

        for item in items:
            inst = WmExceptionInstance(
                exception_type=item["exception_type"],
                severity=item["severity"],
                entity_type=item["entity_type"],
                entity_id=item["entity_id"],
                company_id=item.get("company_id"),
                branch_id=item.get("branch_id"),
                department_id=item.get("department_id"),
                customer_id=item.get("customer_id"),
                job_id=item.get("job_id"),
                task_id=item.get("task_id"),
                task_participant_id=item.get("task_participant_id"),
                emp_id=item.get("emp_id"),
                manager_id=item.get("manager_id"),
                planned_start=item.get("planned_start"),
                planned_due=item.get("planned_due"),
                actual_completion=item.get("actual_completion"),
                planned_hours=item.get("planned_hours"),
                actual_hours=item.get("actual_hours"),
                billed_amount=item.get("billed_amount"),
                total_cost=item.get("total_cost"),
                days_delayed=item.get("days_delayed"),
                exception_age_days=item.get("exception_age_days"),
                exception_message=item["exception_message"],
                recommended_action=item.get("recommended_action"),
                first_detected_on=now,
                last_evaluated_on=now,
                is_active=True,
            )
            self.db.add(inst)
            self.db.flush()
            self.db.add(
                WmExceptionHistory(
                    exception_instance_id=inst.exception_instance_id,
                    old_is_active=None,
                    new_is_active=True,
                    old_severity=None,
                    new_severity=inst.severity,
                    action_code="CREATE",
                    acted_by=user_id,
                )
            )

        self.db.commit()
        return {
            "status": "SUCCESS",
            "exceptions_generated": len(items),
            "message": "Exception analysis refreshed successfully",
        }

    def query_analytics(self, dimensions: list[str], metrics: list[str], filters: dict):
        rows = self.db.query(WmSalesHistory).all()
        facts = []
        for row in rows:
            facts.append(
                {
                    "user": None,
                    "product": int(row.product_id),
                    "branch": int(row.branch_id),
                    "customer": int(row.customer_id),
                    "time": row.sales_date.strftime("%Y-%m"),
                    "revenue": Decimal(str(row.revenue)),
                    "cost": Decimal(str(row.revenue)) * Decimal("0.7"),
                    "quantity": Decimal(str(row.quantity)),
                    "profit": Decimal(str(row.revenue)) * Decimal("0.3"),
                }
            )

        date_filter = filters.get("date")
        if date_filter == "last_30_days":
            cutoff = datetime.utcnow() - timedelta(days=30)
            facts = [x for x in facts if datetime.strptime(f"{x['time']}-01", "%Y-%m-%d") >= cutoff.replace(day=1)]

        grouped = defaultdict(lambda: defaultdict(lambda: Decimal("0")))
        for row in facts:
            key = tuple(row.get(d) for d in dimensions)
            for m in metrics:
                grouped[key][m] += Decimal(str(row.get(m, 0)))

        items = []
        for key, vals in grouped.items():
            item = {dimensions[idx]: key[idx] for idx in range(len(dimensions))}
            for m in metrics:
                item[m] = vals[m]
            items.append(item)
        return {"items": items, "count": len(items)}

    def generate_report(self, name: str, dimensions: list[str], metrics: list[str], filters: dict):
        out = self.query_analytics(dimensions, metrics, filters)
        return {"report_name": name, "generated_at": datetime.utcnow(), "rows": out["items"], "row_count": out["count"]}

    def get_dashboard_summary(self):
        sales = self.db.query(func.coalesce(func.sum(WmSalesHistory.revenue), 0)).scalar()
        deals = self.db.query(func.count(WmJob.job_id)).scalar()
        open_tasks = self.db.query(func.count(WmTask.task_id)).filter(WmTask.status_code.notin_(["Closed", "Done"])).scalar()
        return {
            "kpis": {
                "revenue": Decimal(str(sales or 0)),
                "jobs": int(deals or 0),
                "open_tasks": int(open_tasks or 0),
            }
        }

    def _detect_exceptions(self, company_id: int | None = None, entity_scope: str = "ALL"):
        today = date.today()
        exceptions = []

        tasks_query = self.db.query(WmTask).filter(WmTask.is_active.is_(True))
        if company_id is not None:
            tasks_query = tasks_query.filter(WmTask.company_id == company_id)
        tasks = tasks_query.all()

        participants_query = self.db.query(WmTaskParticipant).filter(WmTaskParticipant.is_active.is_(True))
        participants = participants_query.all()

        # task checks
        if entity_scope in {"ALL", "TASK"}:
            for task in tasks:
                if task.status_code in {"Cancelled", "Closed", "Archived"}:
                    continue

                if not task.primary_owner_emp_id or not task.manager_emp_id:
                    exceptions.append(
                        {
                            "exception_type": "UNMANAGED",
                            "severity": "HIGH" if not task.primary_owner_emp_id else "MEDIUM",
                            "entity_type": "TASK",
                            "entity_id": task.task_id,
                            "company_id": task.company_id,
                            "branch_id": task.branch_id,
                            "department_id": task.department_id,
                            "customer_id": task.customer_id,
                            "job_id": task.job_id,
                            "task_id": task.task_id,
                            "manager_id": task.manager_emp_id,
                            "planned_start": task.planned_start,
                            "planned_due": task.due_at,
                            "exception_message": "Task missing owner or manager mapping.",
                        }
                    )

                if task.due_at and task.status_code not in {"Done", "Closed", "Approved", "Accepted"}:
                    days_delayed = (today - task.due_at.date()).days
                    if days_delayed > 0:
                        exceptions.append(
                            {
                                "exception_type": "ROLLED_OVER",
                                "severity": "HIGH" if days_delayed > 3 else "MEDIUM",
                                "entity_type": "TASK",
                                "entity_id": task.task_id,
                                "company_id": task.company_id,
                                "branch_id": task.branch_id,
                                "department_id": task.department_id,
                                "customer_id": task.customer_id,
                                "job_id": task.job_id,
                                "task_id": task.task_id,
                                "planned_due": task.due_at,
                                "days_delayed": days_delayed,
                                "exception_message": "Task due date passed and work remains incomplete.",
                            }
                        )

                if task.completed_at and task.due_at and task.completed_at > task.due_at:
                    days_delayed = (task.completed_at.date() - task.due_at.date()).days
                    exceptions.append(
                        {
                            "exception_type": "LATE_COMPLETION",
                            "severity": "MEDIUM" if days_delayed <= 3 else "HIGH",
                            "entity_type": "TASK",
                            "entity_id": task.task_id,
                            "company_id": task.company_id,
                            "branch_id": task.branch_id,
                            "department_id": task.department_id,
                            "customer_id": task.customer_id,
                            "job_id": task.job_id,
                            "task_id": task.task_id,
                            "planned_due": task.due_at,
                            "actual_completion": task.completed_at,
                            "days_delayed": days_delayed,
                            "exception_message": "Task completed after due date.",
                        }
                    )

                actual_hours = self.db.query(func.coalesce(func.sum(WmTimesheet.hours), 0)).filter(
                    WmTimesheet.task_id == task.task_id,
                    WmTimesheet.approval_status == "Approved",
                    WmTimesheet.is_active.is_(True),
                ).scalar()
                planned_hours = Decimal(str(task.estimated_hours or 0))
                actual_hours_dec = Decimal(str(actual_hours or 0))
                if planned_hours > 0 and actual_hours_dec > planned_hours:
                    variance_pct = ((actual_hours_dec - planned_hours) / planned_hours) * Decimal("100")
                    severity = "CRITICAL" if variance_pct > 50 else "HIGH" if variance_pct > 25 else "MEDIUM"
                    exceptions.append(
                        {
                            "exception_type": "OVERRUN",
                            "severity": severity,
                            "entity_type": "TASK",
                            "entity_id": task.task_id,
                            "company_id": task.company_id,
                            "branch_id": task.branch_id,
                            "department_id": task.department_id,
                            "customer_id": task.customer_id,
                            "job_id": task.job_id,
                            "task_id": task.task_id,
                            "planned_hours": planned_hours,
                            "actual_hours": actual_hours_dec,
                            "exception_message": f"Task actual effort exceeded plan by {variance_pct:.2f}%.",
                        }
                    )

                if task.last_activity_at:
                    stale_days = (today - task.last_activity_at.date()).days
                    if stale_days >= 7:
                        exceptions.append(
                            {
                                "exception_type": "STALE_WORK" if stale_days < 14 else "LOST_WORK",
                                "severity": "MEDIUM" if stale_days < 10 else "HIGH",
                                "entity_type": "TASK",
                                "entity_id": task.task_id,
                                "company_id": task.company_id,
                                "branch_id": task.branch_id,
                                "department_id": task.department_id,
                                "customer_id": task.customer_id,
                                "job_id": task.job_id,
                                "task_id": task.task_id,
                                "exception_age_days": stale_days,
                                "exception_message": "Open task has no recent activity.",
                            }
                        )

        if entity_scope in {"ALL", "PARTICIPANT"}:
            for p in participants:
                if p.participant_status in {"Completed", "Accepted", "Cancelled"}:
                    continue
                task = next((t for t in tasks if t.task_id == p.task_id), None)
                if task and company_id is not None and task.company_id != company_id:
                    continue

                recent = self.db.query(WmTimesheet).filter(
                    WmTimesheet.task_participant_id == p.task_participant_id,
                    WmTimesheet.approval_status.in_(["Approved", "Submitted"]),
                    WmTimesheet.is_active.is_(True),
                    WmTimesheet.work_date >= (today - timedelta(days=7)),
                ).first()
                if not recent and p.emp_id:
                    exceptions.append(
                        {
                            "exception_type": "NO_TIMESHEET",
                            "severity": "HIGH",
                            "entity_type": "PARTICIPANT",
                            "entity_id": p.task_participant_id,
                            "company_id": task.company_id if task else None,
                            "branch_id": task.branch_id if task else None,
                            "department_id": task.department_id if task else None,
                            "customer_id": task.customer_id if task else None,
                            "job_id": task.job_id if task else None,
                            "task_id": p.task_id,
                            "task_participant_id": p.task_participant_id,
                            "emp_id": p.emp_id,
                            "manager_id": task.manager_emp_id if task else None,
                            "planned_due": p.planned_due,
                            "exception_message": "Assigned participant has no recent timesheet.",
                        }
                    )

                dep = self.db.query(WmTaskParticipantDependency).filter(
                    WmTaskParticipantDependency.successor_participant_id == p.task_participant_id
                ).first()
                if dep:
                    predecessor = self.db.query(WmTaskParticipant).filter(
                        WmTaskParticipant.task_participant_id == dep.predecessor_participant_id
                    ).first()
                    if predecessor and predecessor.participant_status not in {"Accepted", "Completed"}:
                        exceptions.append(
                            {
                                "exception_type": "BLOCKED_DEPENDENCY",
                                "severity": "MEDIUM",
                                "entity_type": "PARTICIPANT",
                                "entity_id": p.task_participant_id,
                                "company_id": task.company_id if task else None,
                                "branch_id": task.branch_id if task else None,
                                "department_id": task.department_id if task else None,
                                "customer_id": task.customer_id if task else None,
                                "job_id": task.job_id if task else None,
                                "task_id": p.task_id,
                                "task_participant_id": p.task_participant_id,
                                "exception_message": "Participant is blocked by unresolved dependency or acceptance.",
                            }
                        )

        if entity_scope in {"ALL", "BILLING"}:
            profit_rows = self.get_profitability(entity_type="TASK")["items"]
            cost_map = {r["entity_id"]: r for r in profit_rows}
            configs = self.db.query(WmBillingConfiguration).filter(WmBillingConfiguration.is_active.is_(True)).all()
            for c in configs:
                if company_id is not None:
                    task = self.db.query(WmTask).filter(WmTask.task_id == c.task_id).first() if c.task_id else None
                    if task and task.company_id != company_id:
                        continue
                readiness = self.db.query(WmBillingReadiness).filter(
                    WmBillingReadiness.entity_type == c.entity_type,
                    WmBillingReadiness.job_id == c.job_id,
                    WmBillingReadiness.task_id == c.task_id,
                    WmBillingReadiness.is_active.is_(True),
                ).first()
                billed = self.db.query(func.coalesce(func.sum(WmBillingDocumentLink.billed_amount), 0)).filter(
                    WmBillingDocumentLink.entity_type == c.entity_type,
                    WmBillingDocumentLink.job_id == c.job_id,
                    WmBillingDocumentLink.task_id == c.task_id,
                    WmBillingDocumentLink.billing_reference_type.like("%_INVOICE"),
                    WmBillingDocumentLink.is_active.is_(True),
                ).scalar()
                billed_dec = Decimal(str(billed or 0))

                if c.billable_flag and readiness and readiness.ready_for_billing_flag:
                    age_days = (today - (readiness.ready_for_billing_date.date() if readiness.ready_for_billing_date else today)).days
                    if billed_dec == 0 and age_days >= 3:
                        exceptions.append(
                            {
                                "exception_type": "UNBILLED_READY",
                                "severity": "HIGH",
                                "entity_type": c.entity_type,
                                "entity_id": c.task_id or c.job_id,
                                "job_id": c.job_id,
                                "task_id": c.task_id,
                                "customer_id": c.customer_id,
                                "billed_amount": billed_dec,
                                "total_cost": cost_map.get(c.task_id, {}).get("total_cost", Decimal("0")),
                                "exception_message": "Billable work is ready for billing but not invoiced.",
                            }
                        )

                total_cost = Decimal(str(cost_map.get(c.task_id, {}).get("total_cost", 0)))
                if billed_dec > 0 and billed_dec < total_cost:
                    exceptions.append(
                        {
                            "exception_type": "BILLED_BELOW_COST",
                            "severity": "CRITICAL",
                            "entity_type": c.entity_type,
                            "entity_id": c.task_id or c.job_id,
                            "job_id": c.job_id,
                            "task_id": c.task_id,
                            "customer_id": c.customer_id,
                            "billed_amount": billed_dec,
                            "total_cost": total_cost,
                            "exception_message": "Billed value is lower than total cost.",
                        }
                    )
                elif billed_dec > 0 and billed_dec < (total_cost * Decimal("1.1")):
                    exceptions.append(
                        {
                            "exception_type": "UNDERBILLED",
                            "severity": "MEDIUM",
                            "entity_type": c.entity_type,
                            "entity_id": c.task_id or c.job_id,
                            "job_id": c.job_id,
                            "task_id": c.task_id,
                            "customer_id": c.customer_id,
                            "billed_amount": billed_dec,
                            "total_cost": total_cost,
                            "exception_message": "Billed value is below expected recovery threshold.",
                        }
                    )

        if entity_scope in {"ALL", "APPROVAL"}:
            ts_pending = self.db.query(WmTimesheet).filter(
                WmTimesheet.approval_status == "Submitted",
                WmTimesheet.is_active.is_(True),
            ).all()
            for t in ts_pending:
                if not t.submitted_on:
                    continue
                age_days = (today - t.submitted_on.date()).days
                if age_days >= 3:
                    exceptions.append(
                        {
                            "exception_type": "APPROVAL_DELAY",
                            "severity": "HIGH" if age_days > 3 else "MEDIUM",
                            "entity_type": "TIMESHEET",
                            "entity_id": t.timesheet_id,
                            "company_id": t.company_id,
                            "branch_id": t.branch_id,
                            "department_id": t.department_id,
                            "customer_id": t.customer_id,
                            "job_id": t.job_id,
                            "task_id": t.task_id,
                            "emp_id": t.emp_id,
                            "exception_age_days": age_days,
                            "exception_message": "Submitted timesheet is pending approval beyond threshold.",
                        }
                    )

            exp_pending = self.db.query(WmExpenseClaim).filter(
                WmExpenseClaim.approval_status == "Submitted",
                WmExpenseClaim.is_active.is_(True),
            ).all()
            for e in exp_pending:
                if not e.submitted_on:
                    continue
                age_days = (today - e.submitted_on.date()).days
                if age_days >= 3:
                    exceptions.append(
                        {
                            "exception_type": "APPROVAL_DELAY",
                            "severity": "HIGH" if age_days > 3 else "MEDIUM",
                            "entity_type": "EXPENSE_CLAIM",
                            "entity_id": e.claim_id,
                            "company_id": e.company_id,
                            "branch_id": e.branch_id,
                            "department_id": e.department_id,
                            "customer_id": e.customer_id,
                            "job_id": e.job_id,
                            "task_id": e.task_id,
                            "emp_id": e.emp_id,
                            "exception_age_days": age_days,
                            "exception_message": "Submitted expense claim is pending approval beyond threshold.",
                        }
                    )

        return exceptions

    # ---- Existing profitability helpers ----
    def _build_rows(self, entity_type: str, **filters) -> dict[int, dict]:
        pairs, base, missing_cost_by_pair = self._load_cost_base(**filters)
        billed_by_pair = self._load_billing_by_pair(**filters)
        pair_flags = self._load_pair_flags()

        by_entity = defaultdict(lambda: self._empty_bucket(entity_type))
        pair_to_entity_rows = defaultdict(list)
        for row in base:
            pair = (row["job_id"], row["task_id"])
            pair_to_entity_rows[pair].append(row)

        for pair, rows in pair_to_entity_rows.items():
            pair_cost = sum((x["total_cost"] for x in rows), Decimal("0"))
            pair_billed = billed_by_pair.get(pair, Decimal("0"))
            for row in rows:
                key, name = self._entity_key_name(entity_type, row)
                if key is None:
                    continue
                share = Decimal("0")
                if pair_cost > 0 and pair_billed > 0:
                    share = (row["total_cost"] / pair_cost) * pair_billed
                bucket = by_entity[key]
                bucket["entity_id"] = key
                bucket["entity_name"] = name
                bucket["approved_labor_hours"] += row["approved_hours"]
                bucket["approved_billable_hours"] += row["approved_billable_hours"]
                bucket["labor_cost"] += row["labor_cost"]
                bucket["non_labor_cost"] += row["non_labor_cost"]
                bucket["total_cost"] += row["total_cost"]
                bucket["billed_amount"] += share
                flags = pair_flags.get(pair, {"billable": False, "ready": False})
                bucket["billable_ready"] = bucket["billable_ready"] or (flags["billable"] and flags["ready"])
                bucket["missing_cost_rate"] = bucket["missing_cost_rate"] or (row["emp_id"] in missing_cost_by_pair.get(pair, set()))

        if entity_type in {"JOB", "TASK", "CUSTOMER", "COMPANY", "BRANCH", "DEPARTMENT"}:
            for pair, billed in billed_by_pair.items():
                if pair not in pairs:
                    continue
                sample = pairs[pair]
                key, name = self._entity_key_name(entity_type, sample)
                if key is None:
                    continue
                if by_entity[key]["billed_amount"] == 0:
                    by_entity[key]["entity_id"] = key
                    by_entity[key]["entity_name"] = name
                    by_entity[key]["billed_amount"] = billed

        return by_entity

    def _load_cost_base(self, **filters):
        date_from = self._parse_date(filters.get("date_from"))
        date_to = self._parse_date(filters.get("date_to"))
        employees = {e.emp_id: e for e in self.db.query(RefEmployee).all()}
        jobs = {j.job_id: j for j in self.db.query(WmJob).filter(WmJob.is_active.is_(True)).all()}
        tasks = {t.task_id: t for t in self.db.query(WmTask).filter(WmTask.is_active.is_(True)).all()}

        base_map = {}
        missing_cost_by_pair = defaultdict(set)

        ts_query = self.db.query(WmTimesheet).filter(WmTimesheet.approval_status == "Approved", WmTimesheet.is_active.is_(True))
        if date_from:
            ts_query = ts_query.filter(WmTimesheet.work_date >= date_from)
        if date_to:
            ts_query = ts_query.filter(WmTimesheet.work_date <= date_to)

        for ts in ts_query.all():
            row = self._to_scope_row(ts.company_id, ts.branch_id, ts.department_id, ts.customer_id, ts.job_id, ts.task_id, ts.emp_id, ts.task_participant_id, jobs, tasks)
            if not self._match_scope(row, filters):
                continue
            key = (row["job_id"], row["task_id"], row["emp_id"], row["task_participant_id"])
            bucket = base_map.setdefault(key, self._empty_base(row))
            bucket["approved_hours"] += Decimal(str(ts.hours or 0))
            bucket["approved_billable_hours"] += Decimal(str(ts.billable_hours or 0))
            hourly_cost = Decimal(str((employees.get(ts.emp_id).hourly_cost if employees.get(ts.emp_id) else 0) or 0))
            if hourly_cost == 0:
                missing_cost_by_pair[(row["job_id"], row["task_id"])].add(ts.emp_id)
            regular_cost = Decimal(str(ts.hours or 0)) * hourly_cost
            overtime_cost = Decimal(str(ts.overtime_hours or 0)) * hourly_cost
            bucket["labor_cost"] += regular_cost + overtime_cost
            bucket["total_cost"] += regular_cost + overtime_cost

        ex_query = self.db.query(WmExpenseClaim).filter(WmExpenseClaim.approval_status.in_(["Approved", "Converted"]), WmExpenseClaim.is_active.is_(True))
        if date_from:
            ex_query = ex_query.filter(WmExpenseClaim.expense_date >= date_from)
        if date_to:
            ex_query = ex_query.filter(WmExpenseClaim.expense_date <= date_to)

        for ex in ex_query.all():
            row = self._to_scope_row(ex.company_id, ex.branch_id, ex.department_id, ex.customer_id, ex.job_id, ex.task_id, ex.emp_id, ex.task_participant_id, jobs, tasks)
            if not self._match_scope(row, filters):
                continue
            key = (row["job_id"], row["task_id"], row["emp_id"], row["task_participant_id"])
            bucket = base_map.setdefault(key, self._empty_base(row))
            amount = Decimal(str(ex.total_amount or 0))
            bucket["non_labor_cost"] += amount
            bucket["total_cost"] += amount

        pairs = {}
        for row in base_map.values():
            pair = (row["job_id"], row["task_id"])
            if pair not in pairs:
                pairs[pair] = row
        return pairs, list(base_map.values()), missing_cost_by_pair

    def _load_billing_by_pair(self, **filters):
        date_from = self._parse_date(filters.get("date_from"))
        date_to = self._parse_date(filters.get("date_to"))
        billed = defaultdict(lambda: Decimal("0"))
        q = self.db.query(WmBillingDocumentLink).filter(
            WmBillingDocumentLink.is_active.is_(True),
            WmBillingDocumentLink.billing_reference_type.like("%_INVOICE"),
        )
        if date_from:
            q = q.filter(WmBillingDocumentLink.billed_date >= date_from)
        if date_to:
            q = q.filter(WmBillingDocumentLink.billed_date <= date_to)

        for doc in q.all():
            pair = (doc.job_id, doc.task_id)
            billed[pair] += Decimal(str(doc.billed_amount or 0))
        return billed

    def _load_pair_flags(self):
        config = {(c.job_id, c.task_id): bool(c.billable_flag) for c in self.db.query(WmBillingConfiguration).filter(WmBillingConfiguration.is_active.is_(True)).all()}
        ready = {(r.job_id, r.task_id): bool(r.ready_for_billing_flag) for r in self.db.query(WmBillingReadiness).filter(WmBillingReadiness.is_active.is_(True)).all()}
        pairs = set(config.keys()) | set(ready.keys())
        return {p: {"billable": config.get(p, False), "ready": ready.get(p, False)} for p in pairs}

    def _finalize_row(self, entity_type: str, row: dict):
        billed = row["billed_amount"]
        total_cost = row["total_cost"]
        unbilled = total_cost if row["billable_ready"] and billed == 0 else Decimal("0")
        underbilling = (total_cost - billed) if billed < total_cost else Decimal("0")
        profit = billed - total_cost
        margin = (profit / billed * Decimal("100")) if billed > 0 else None

        exception_type = ""
        if row["missing_cost_rate"]:
            exception_type = "MISSING_COST_RATE"
        elif row["billable_ready"] and billed == 0:
            exception_type = "UNBILLED"
        elif billed < total_cost and billed > 0:
            exception_type = "UNDERBILLED"
        elif profit < 0:
            exception_type = "NEGATIVE_MARGIN"

        return {
            "entity_type": entity_type,
            "entity_id": row["entity_id"],
            "entity_name": row["entity_name"],
            "approved_labor_hours": row["approved_labor_hours"],
            "approved_billable_hours": row["approved_billable_hours"],
            "labor_cost": row["labor_cost"],
            "non_labor_cost": row["non_labor_cost"],
            "total_cost": total_cost,
            "billed_amount": billed,
            "unbilled_amount": unbilled,
            "underbilling_amount": underbilling,
            "profit_amount": profit,
            "margin_percent": margin,
            "exception_type": exception_type,
        }

    def _entity_key_name(self, entity_type: str, row: dict):
        key_map = {
            "JOB": (row["job_id"], row.get("job_name") or f"Job {row['job_id']}"),
            "TASK": (row["task_id"], row.get("task_name") or f"Task {row['task_id']}"),
            "CUSTOMER": (row["customer_id"], f"Customer {row['customer_id']}"),
            "EMPLOYEE": (row["emp_id"], row.get("employee_name") or f"Employee {row['emp_id']}"),
            "PARTICIPANT": (row["task_participant_id"], f"Participant {row['task_participant_id']}"),
            "BRANCH": (row["branch_id"], f"Branch {row['branch_id']}"),
            "DEPARTMENT": (row["department_id"], f"Department {row['department_id']}"),
            "COMPANY": (row["company_id"], f"Company {row['company_id']}"),
        }
        key, name = key_map[entity_type]
        if key is None:
            return None, ""
        return key, name

    def _match_scope(self, row: dict, filters: dict) -> bool:
        for field in ["company_id", "branch_id", "department_id", "customer_id", "job_id", "task_id", "emp_id"]:
            val = filters.get(field)
            if val is not None and row.get(field) != val:
                return False
        return True

    def _to_scope_row(self, company_id, branch_id, department_id, customer_id, job_id, task_id, emp_id, participant_id, jobs, tasks):
        job = jobs.get(job_id) if job_id else None
        task = tasks.get(task_id) if task_id else None
        return {
            "company_id": company_id or (job.company_id if job else None) or (task.company_id if task else None),
            "branch_id": branch_id or (job.branch_id if job else None) or (task.branch_id if task else None),
            "department_id": department_id or (job.department_id if job else None) or (task.department_id if task else None),
            "customer_id": customer_id or (task.customer_id if task else None) or (job.customer_id if job else None),
            "job_id": job_id,
            "task_id": task_id,
            "emp_id": emp_id,
            "task_participant_id": participant_id,
            "job_name": job.job_name if job else None,
            "task_name": task.title if task else None,
            "employee_name": None,
        }

    def _empty_base(self, row: dict):
        return {
            **row,
            "approved_hours": Decimal("0"),
            "approved_billable_hours": Decimal("0"),
            "labor_cost": Decimal("0"),
            "non_labor_cost": Decimal("0"),
            "total_cost": Decimal("0"),
        }

    def _empty_bucket(self, entity_type: str):
        return {
            "entity_id": 0,
            "entity_name": "",
            "approved_labor_hours": Decimal("0"),
            "approved_billable_hours": Decimal("0"),
            "labor_cost": Decimal("0"),
            "non_labor_cost": Decimal("0"),
            "total_cost": Decimal("0"),
            "billed_amount": Decimal("0"),
            "billable_ready": False,
            "missing_cost_rate": False,
        }

    def _parse_date(self, value):
        if not value:
            return None
        if isinstance(value, date):
            return value
        return date.fromisoformat(value)
