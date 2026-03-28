from __future__ import annotations

import json
from calendar import monthrange
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.wm_increment_config import WmIncrementConfig
from app.models.wm_holiday_calendar import WmHolidayCalendar
from app.models.wm_job import WmJob
from app.models.wm_points_event import WmPointsEvent
from app.models.wm_shift_master import WmShiftMaster
from app.models.wm_timesheet import WmTimesheet


@dataclass
class CapacityThresholds:
    under: float = 60
    optimal: float = 85
    full: float = 100
    over: float = 120


class PointsLedgerService:
    def __init__(self, db: Session):
        self.db = db

    def add_event(self, **kwargs) -> WmPointsEvent:
        event_id = int((self.db.query(func.max(WmPointsEvent.points_event_id)).scalar() or 0) + 1)
        row = WmPointsEvent(points_event_id=event_id, **kwargs)
        self.db.add(row)
        return row

    def employee_points_summary(self, employee_id: int, start_date: date | None = None, end_date: date | None = None) -> dict:
        q = self.db.query(WmPointsEvent).filter(WmPointsEvent.employee_id == employee_id)
        if start_date:
            q = q.filter(WmPointsEvent.event_date >= start_date)
        if end_date:
            q = q.filter(WmPointsEvent.event_date <= end_date)
        rows = q.all()
        today = datetime.utcnow().date()
        month_start = today.replace(day=1)
        quarter_start = date(today.year, ((today.month - 1) // 3) * 3 + 1, 1)
        year_start = date(today.year, 1, 1)
        return {
            "employee_id": employee_id,
            "total_points_lifetime": sum(r.points_awarded for r in self.db.query(WmPointsEvent).filter(WmPointsEvent.employee_id == employee_id).all()),
            "total_points_current_month": sum(r.points_awarded for r in rows if r.event_date >= month_start),
            "total_points_current_quarter": sum(r.points_awarded for r in rows if r.event_date >= quarter_start),
            "total_points_current_year": sum(r.points_awarded for r in rows if r.event_date >= year_start),
            "positive_points_count": sum(1 for r in rows if r.points_awarded > 0),
            "negative_points_count": sum(1 for r in rows if r.points_awarded < 0),
            "on_time_completion_count": sum(1 for r in rows if r.event_type == "ON_TIME_COMPLETION_REWARD"),
            "late_completion_count": sum(1 for r in rows if r.event_type in {"LATE_COMPLETION_PENALTY", "TEAM_FAILURE_PENALTY"}),
            "partial_team_penalty_count": sum(1 for r in rows if r.event_type == "PARTIAL_TEAM_COMPLETION_PENALTY"),
        }


class TeamCompletionEvaluationService:
    def evaluate(self, job_rows: list[WmJob]) -> dict:
        active = [j for j in job_rows if (j.assigned_employee_id and j.execution_status != "Cancelled")]
        employees = sorted(set(j.assigned_employee_id for j in active))
        employee_status: dict[int, bool] = {}
        for emp in employees:
            emp_jobs = [j for j in active if j.assigned_employee_id == emp]
            employee_status[emp] = all(self._is_on_time(j) for j in emp_jobs)

        on_time_count = sum(1 for ok in employee_status.values() if ok)
        late_count = sum(1 for ok in employee_status.values() if not ok)
        multi = len(employee_status) > 1
        return {
            "is_multi_employee_task": multi,
            "total_assigned_employees": len(employee_status),
            "on_time_employee_count": on_time_count,
            "late_employee_count": late_count,
            "all_completed_on_time_flag": on_time_count > 0 and late_count == 0,
            "partial_team_failure_flag": on_time_count > 0 and late_count > 0,
            "all_failed_flag": on_time_count == 0 and late_count > 0,
            "employee_on_time_map": employee_status,
        }

    def _is_on_time(self, job: WmJob) -> bool:
        due_ref = getattr(job, "original_due_date", None) or job.due_date
        if not due_ref:
            return False
        if job.execution_status not in {"Completed", "Billed", "Closed"}:
            return False
        if not job.completed_at:
            return False
        return job.completed_at.date() <= due_ref


class IncrementConfigService:
    DEFAULT_BANDS = [
        {"min": -99999, "max": 0, "increment": 0},
        {"min": 1, "max": 50, "increment": 2},
        {"min": 51, "max": 120, "increment": 4},
        {"min": 121, "max": 220, "increment": 6},
        {"min": 221, "max": 320, "increment": 8},
        {"min": 321, "max": 420, "increment": 10},
        {"min": 421, "max": 99999, "increment": 12},
    ]

    def __init__(self, db: Session):
        self.db = db

    def get_active(self) -> WmIncrementConfig:
        row = self.db.query(WmIncrementConfig).filter(WmIncrementConfig.active_flag.is_(True)).order_by(WmIncrementConfig.config_id.desc()).first()
        if row:
            return row
        config_id = int((self.db.query(func.max(WmIncrementConfig.config_id)).scalar() or 0) + 1)
        row = WmIncrementConfig(config_id=config_id, max_increment_percent=12, point_to_increment_mode="BAND", divisor_value=100, score_bands_json=json.dumps(self.DEFAULT_BANDS), minimum_score_floor=0, penalty_carry_forward_flag=True, manual_override_allowed_flag=False, manager_review_required_flag=True, active_flag=True)
        self.db.add(row)
        self.db.commit()
        return row


class IncrementEngineService:
    def __init__(self, db: Session):
        self.db = db
        self.config = IncrementConfigService(db)

    def calculate_increment_percent(self, points: int) -> float:
        cfg = self.config.get_active()
        max_increment = float(cfg.max_increment_percent)
        mode = (cfg.point_to_increment_mode or "BAND").upper()
        if mode == "PROPORTIONAL":
            divisor = float(cfg.divisor_value or 100)
            return round(max(0.0, min(max_increment, points / divisor)), 2)

        bands = json.loads(cfg.score_bands_json) if cfg.score_bands_json else IncrementConfigService.DEFAULT_BANDS
        for band in bands:
            if band["min"] <= points <= band["max"]:
                return round(min(max_increment, float(band["increment"])), 2)
        return 0.0


class CapacityPlanningService:
    def __init__(self, db: Session):
        self.db = db
        self.thresholds = CapacityThresholds()

    def employee_capacity(self, employee_id: int, start_date: date, end_date: date) -> dict:
        available_hours = self._available_hours(start_date, end_date)
        planned_jobs = self.db.query(WmJob).filter(
            WmJob.assigned_employee_id == employee_id,
            WmJob.is_active.is_(True),
            WmJob.execution_status != "Cancelled",
            WmJob.start_date <= end_date,
            WmJob.due_date >= start_date,
        ).all()
        planned_hours = sum(float(j.planned_hours or 0) for j in planned_jobs)

        actual_rows = self.db.query(WmTimesheet).filter(
            WmTimesheet.emp_id == employee_id,
            WmTimesheet.work_date >= start_date,
            WmTimesheet.work_date <= end_date,
        ).all()
        actual_hours = sum(float(r.total_hours or 0) for r in actual_rows)

        planned_util = (planned_hours / available_hours * 100) if available_hours else 0
        actual_util = (actual_hours / available_hours * 100) if available_hours else 0

        return {
            "employee_id": employee_id,
            "available_working_hours": round(available_hours, 2),
            "planned_hours": round(planned_hours, 2),
            "actual_logged_hours": round(actual_hours, 2),
            "variance_hours": round(actual_hours - planned_hours, 2),
            "variance_percent": round(actual_util - planned_util, 2),
            "planned_utilization_percent": round(planned_util, 2),
            "actual_utilization_percent": round(actual_util, 2),
            "planned_capacity_status": self._status(planned_util),
            "actual_capacity_status": self._status(actual_util),
            "underutilization_gap": round(max(0, available_hours - planned_hours), 2),
            "overload_gap": round(max(0, planned_hours - available_hours), 2),
        }

    def _available_hours(self, start_date: date, end_date: date) -> float:
        d = start_date
        days = 0
        while d <= end_date:
            if d.weekday() != 6:  # sunday off
                days += 1
            d += timedelta(days=1)
        return days * 9.0

    def _status(self, utilization: float) -> str:
        if utilization < self.thresholds.under:
            return "Under Occupied"
        if utilization <= self.thresholds.optimal:
            return "Optimally Occupied"
        if utilization <= self.thresholds.full:
            return "Fully Occupied"
        if utilization <= self.thresholds.over:
            return "Over Occupied"
        return "Critically Overloaded"


class EmployeeScheduleService:
    def __init__(self, db: Session):
        self.db = db

    def daily_capacity(self, employee_id: int, day: date) -> dict:
        shift = self._employee_shift(employee_id)
        default_hours = float(getattr(shift, "total_working_hours", 9.0) or 9.0)
        weekly_off_days = self._weekly_off_days(shift)
        holiday_row = self.db.query(WmHolidayCalendar).filter(WmHolidayCalendar.holiday_date == day).first()
        is_weekly_off = day.weekday() in weekly_off_days
        is_holiday = bool(holiday_row and not holiday_row.weekly_off)
        available = 0.0 if (is_weekly_off or is_holiday) else default_hours
        return {
            "date": day,
            "available_hours": round(available, 2),
            "is_holiday": is_holiday,
            "is_weekly_off": is_weekly_off,
            "holiday_name": getattr(holiday_row, "description", None) if is_holiday else None,
        }

    def date_span_capacity(self, employee_id: int, start_date: date, end_date: date) -> list[dict]:
        rows = []
        cursor = start_date
        while cursor <= end_date:
            rows.append(self.daily_capacity(employee_id, cursor))
            cursor += timedelta(days=1)
        return rows

    def _employee_shift(self, employee_id: int) -> WmShiftMaster | None:
        # Current schema does not map employee->shift. Pick default shift when available.
        return self.db.query(WmShiftMaster).order_by(WmShiftMaster.shift_id.asc()).first()

    def _weekly_off_days(self, shift: WmShiftMaster | None) -> set[int]:
        pattern = ((shift.weekly_off_pattern if shift else None) or "Sunday").lower()
        map_day = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6,
        }
        matches = {idx for name, idx in map_day.items() if name in pattern}
        return matches or {6}


class PlannedAllocationService:
    def __init__(self, db: Session):
        self.db = db

    def daily_planned_hours(self, employee_id: int, start_date: date, end_date: date) -> dict[date, float]:
        rows = defaultdict(float)
        jobs = self.db.query(WmJob).filter(
            WmJob.assigned_employee_id == employee_id,
            WmJob.is_active.is_(True),
            WmJob.execution_status != "Cancelled",
            WmJob.start_date <= end_date,
            WmJob.due_date >= start_date,
        ).all()
        for job in jobs:
            if not job.start_date or not job.due_date:
                continue
            overlap_start = max(start_date, job.start_date)
            overlap_end = min(end_date, job.due_date)
            if overlap_start > overlap_end:
                continue
            total_days = (job.due_date - job.start_date).days + 1
            if total_days <= 0:
                total_days = 1
            per_day = float(job.planned_hours or 0) / total_days
            cursor = overlap_start
            while cursor <= overlap_end:
                rows[cursor] += per_day
                cursor += timedelta(days=1)
        return {k: round(v, 2) for k, v in rows.items()}


class ProductiveTimeService:
    def __init__(self, db: Session):
        self.db = db

    def daily_actual_hours(self, employee_id: int, start_date: date, end_date: date) -> dict[date, float]:
        rows = defaultdict(float)
        entries = self.db.query(WmTimesheet).filter(
            WmTimesheet.emp_id == employee_id,
            WmTimesheet.work_date >= start_date,
            WmTimesheet.work_date <= end_date,
            WmTimesheet.is_active.is_(True),
        ).all()
        for entry in entries:
            rows[entry.work_date] += float(entry.hours or 0)
        return {k: round(v, 2) for k, v in rows.items()}


class CapacityCalendarService:
    def __init__(self, db: Session):
        self.db = db
        self.schedule = EmployeeScheduleService(db)
        self.planned = PlannedAllocationService(db)
        self.actual = ProductiveTimeService(db)

    def month_view(self, employee_id: int, reference_date: date) -> dict:
        start_date = reference_date.replace(day=1)
        end_date = reference_date.replace(day=monthrange(reference_date.year, reference_date.month)[1])
        return self._build_view(employee_id, start_date, end_date, "month")

    def week_view(self, employee_id: int, reference_date: date) -> dict:
        start_date = reference_date - timedelta(days=reference_date.weekday())
        end_date = start_date + timedelta(days=6)
        return self._build_view(employee_id, start_date, end_date, "week")

    def day_view(self, employee_id: int, reference_date: date) -> dict:
        return self._build_view(employee_id, reference_date, reference_date, "day")

    def _build_view(self, employee_id: int, start_date: date, end_date: date, mode: str) -> dict:
        capacity = self.schedule.date_span_capacity(employee_id, start_date, end_date)
        planned_map = self.planned.daily_planned_hours(employee_id, start_date, end_date)
        actual_map = self.actual.daily_actual_hours(employee_id, start_date, end_date)
        days = []
        for day_info in capacity:
            day = day_info["date"]
            available = day_info["available_hours"]
            planned = planned_map.get(day, 0.0)
            actual = actual_map.get(day, 0.0)
            free_hours = max(0.0, available - planned)
            overload_hours = max(0.0, planned - available)
            days.append({
                **day_info,
                "planned_hours": round(planned, 2),
                "actual_hours": round(actual, 2),
                "free_hours": round(free_hours, 2),
                "overload_hours": round(overload_hours, 2),
            })
        return {
            "employee_id": employee_id,
            "mode": mode,
            "start_date": start_date,
            "end_date": end_date,
            "days": days,
            "totals": {
                "available_hours": round(sum(d["available_hours"] for d in days), 2),
                "planned_hours": round(sum(d["planned_hours"] for d in days), 2),
                "actual_hours": round(sum(d["actual_hours"] for d in days), 2),
                "free_hours": round(sum(d["free_hours"] for d in days), 2),
                "overload_hours": round(sum(d["overload_hours"] for d in days), 2),
            },
        }


class CalendarDrilldownService:
    def __init__(self, db: Session):
        self.calendar = CapacityCalendarService(db)

    def run(self, employee_id: int, reference_date: date, mode: str = "month") -> dict:
        normalized = mode.lower()
        if normalized == "day":
            return self.calendar.day_view(employee_id, reference_date)
        if normalized == "week":
            return self.calendar.week_view(employee_id, reference_date)
        return self.calendar.month_view(employee_id, reference_date)


class TeamCapacityService:
    def __init__(self, db: Session):
        self.db = db
        self.calendar = CapacityCalendarService(db)

    def manager_summary(self, manager_id: int, start_date: date, end_date: date) -> dict:
        employee_ids = [emp_id for (emp_id,) in self.db.query(WmJob.assigned_employee_id).filter(
            WmJob.manager_id == manager_id,
            WmJob.assigned_employee_id.isnot(None),
            WmJob.is_active.is_(True),
        ).distinct().all() if emp_id]
        employee_rows = [self.calendar._build_view(emp_id, start_date, end_date, "team_span") for emp_id in employee_ids]
        return {
            "manager_id": manager_id,
            "employee_count": len(employee_rows),
            "employees": [{
                "employee_id": row["employee_id"],
                **row["totals"],
            } for row in employee_rows],
            "team_totals": {
                "available_hours": round(sum(row["totals"]["available_hours"] for row in employee_rows), 2),
                "planned_hours": round(sum(row["totals"]["planned_hours"] for row in employee_rows), 2),
                "actual_hours": round(sum(row["totals"]["actual_hours"] for row in employee_rows), 2),
                "free_hours": round(sum(row["totals"]["free_hours"] for row in employee_rows), 2),
                "overload_hours": round(sum(row["totals"]["overload_hours"] for row in employee_rows), 2),
            },
        }


class GamificationService:
    def __init__(self, db: Session):
        self.db = db
        self.ledger = PointsLedgerService(db)
        self.team_eval = TeamCompletionEvaluationService()

    def evaluate_task_and_award(self, parent_task_id: int, created_by: int = 1) -> dict:
        jobs = self.db.query(WmJob).filter(WmJob.parent_task_id == parent_task_id, WmJob.is_active.is_(True)).all()
        if not jobs:
            return {"status": "success", "created_events": 0, "details": []}

        eval_out = self.team_eval.evaluate(jobs)
        created = []
        for emp_id, is_on_time in eval_out["employee_on_time_map"].items():
            points, event_type, mode, reason = self._points_rule(eval_out, is_on_time)
            emp_jobs = [j for j in jobs if j.assigned_employee_id == emp_id]
            due_ref = min((getattr(j, "original_due_date", None) or j.due_date) for j in emp_jobs if (getattr(j, "original_due_date", None) or j.due_date))
            completion = max((j.completed_at.date() for j in emp_jobs if j.completed_at), default=None)
            self.ledger.add_event(
                employee_id=emp_id,
                source_entity_type="TASK",
                source_entity_id=parent_task_id,
                parent_task_id=parent_task_id,
                job_id=None,
                event_type=event_type,
                event_reason=reason,
                event_date=datetime.utcnow().date(),
                due_date_reference=due_ref,
                completion_date=completion,
                points_awarded=points,
                positive_or_negative_flag="POSITIVE" if points > 0 else "NEGATIVE",
                evaluation_mode=mode,
                created_by=created_by,
                remarks=f"Employees on-time={eval_out['on_time_employee_count']}, late={eval_out['late_employee_count']}",
            )
            created.append({"employee_id": emp_id, "points": points, "event_type": event_type})

        self.db.commit()
        return {"status": "success", "created_events": len(created), "evaluation": eval_out, "details": created}

    def _points_rule(self, eval_out: dict, is_on_time: bool) -> tuple[int, str, str, str]:
        if not eval_out["is_multi_employee_task"]:
            if is_on_time:
                return 10, "ON_TIME_COMPLETION_REWARD", "single", "Single-owner on-time completion against committed due date"
            return -20, "LATE_COMPLETION_PENALTY", "single", "Single-owner late/missed completion against committed due date"

        if eval_out["all_completed_on_time_flag"]:
            return 10, "ON_TIME_COMPLETION_REWARD", "multi-employee", "All team contributors completed on time"
        if eval_out["partial_team_failure_flag"]:
            if is_on_time:
                return -5, "PARTIAL_TEAM_COMPLETION_PENALTY", "team partial failure", "Partial team failure penalty despite individual on-time completion"
            return -20, "LATE_COMPLETION_PENALTY", "team partial failure", "Late contributor during partial team failure"
        return -20, "TEAM_FAILURE_PENALTY", "multi-employee", "All contributors missed committed completion"


class DashboardAggregationService:
    def __init__(self, db: Session):
        self.db = db
        self.ledger = PointsLedgerService(db)
        self.capacity = CapacityPlanningService(db)
        self.increment = IncrementEngineService(db)

    def employee_scorecard(self, employee_id: int, start_date: date, end_date: date) -> dict:
        points = self.ledger.employee_points_summary(employee_id, start_date, end_date)
        cap = self.capacity.employee_capacity(employee_id, start_date, end_date)
        inc = self.increment.calculate_increment_percent(points["total_points_current_year"])
        return {
            **points,
            **cap,
            "increment_eligibility_percent": inc,
            "max_possible_increment_percent": 12,
        }

    def leadership_widgets(self, start_date: date, end_date: date) -> dict:
        rows = self.db.query(WmPointsEvent).filter(WmPointsEvent.event_date >= start_date, WmPointsEvent.event_date <= end_date).all()
        by_emp = defaultdict(int)
        for r in rows:
            by_emp[r.employee_id] += r.points_awarded
        ranked = sorted(by_emp.items(), key=lambda x: x[1], reverse=True)
        return {
            "total_positive_points": sum(r.points_awarded for r in rows if r.points_awarded > 0),
            "total_negative_points": sum(r.points_awarded for r in rows if r.points_awarded < 0),
            "average_increment_eligibility_percent": round(sum(self.increment.calculate_increment_percent(v) for v in by_emp.values()) / (len(by_emp) or 1), 2),
            "top_10_employees_by_points": ranked[:10],
            "bottom_10_employees_by_points": list(reversed(ranked[-10:])),
            "team_coordination_penalty_trend": sum(1 for r in rows if r.event_type == "PARTIAL_TEAM_COMPLETION_PENALTY"),
        }

    def calendar_capacity_widgets(self, employee_id: int, reference_date: date) -> dict:
        calendar = CapacityCalendarService(self.db).month_view(employee_id, reference_date)
        return {
            "employee_id": employee_id,
            "reference_date": reference_date,
            "planned_vs_actual_hours": {
                "planned": calendar["totals"]["planned_hours"],
                "actual": calendar["totals"]["actual_hours"],
            },
            "free_hours": calendar["totals"]["free_hours"],
            "overload_hours": calendar["totals"]["overload_hours"],
            "holidays_count": sum(1 for d in calendar["days"] if d["is_holiday"]),
            "weekly_off_count": sum(1 for d in calendar["days"] if d["is_weekly_off"]),
        }


class UtilizationAnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.capacity = CapacityPlanningService(db)

    def manager_team_capacity(self, manager_id: int, start_date: date, end_date: date) -> dict:
        employees = self.db.query(WmJob.assigned_employee_id).filter(WmJob.manager_id == manager_id, WmJob.assigned_employee_id.isnot(None)).distinct().all()
        stats = [self.capacity.employee_capacity(emp_id, start_date, end_date) for (emp_id,) in employees if emp_id]
        return {
            "manager_id": manager_id,
            "team_under_occupied_count": sum(1 for s in stats if s["planned_capacity_status"] == "Under Occupied"),
            "team_overloaded_count": sum(1 for s in stats if s["planned_capacity_status"] in {"Over Occupied", "Critically Overloaded"}),
            "employees_needing_reallocation": [s["employee_id"] for s in stats if s["planned_capacity_status"] in {"Under Occupied", "Critically Overloaded"}],
            "team_planned_vs_actual": stats,
        }


class ScoreAuditService:
    def __init__(self, db: Session):
        self.db = db

    def ledger_report(self, start_date: date | None = None, end_date: date | None = None, employee_id: int | None = None) -> list[dict]:
        q = self.db.query(WmPointsEvent)
        if start_date:
            q = q.filter(WmPointsEvent.event_date >= start_date)
        if end_date:
            q = q.filter(WmPointsEvent.event_date <= end_date)
        if employee_id:
            q = q.filter(WmPointsEvent.employee_id == employee_id)
        return [{
            "points_event_id": r.points_event_id,
            "employee_id": r.employee_id,
            "event_type": r.event_type,
            "points_awarded": r.points_awarded,
            "evaluation_mode": r.evaluation_mode,
            "due_date_reference": r.due_date_reference,
            "completion_date": r.completion_date,
            "event_reason": r.event_reason,
        } for r in q.order_by(WmPointsEvent.points_event_id.desc()).all()]

    def capacity_report(self, employee_id: int, start_date: date, end_date: date) -> dict:
        return CapacityCalendarService(self.db)._build_view(employee_id, start_date, end_date, "report")
