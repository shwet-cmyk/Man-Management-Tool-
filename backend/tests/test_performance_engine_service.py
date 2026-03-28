from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.modules.performance_engine.service import (
    CalendarDrilldownService,
    CapacityCalendarService,
    CapacityPlanningService,
    TeamCapacityService,
    TeamCompletionEvaluationService,
)


class FakeQuery:
    def __init__(self, rows, skip_filter: bool = False):
        self._rows = rows
        self._skip_filter = skip_filter

    def filter(self, *args, **kwargs):
        if self._skip_filter:
            return self
        def _value(side):
            return getattr(side, "value", side)

        for cond in args:
            left = getattr(cond, "left", None)
            right = getattr(cond, "right", None)
            key = getattr(left, "key", None)
            op_name = getattr(getattr(cond, "operator", None), "__name__", "")
            if not key:
                continue
            value = _value(right)
            if op_name in {"eq", "is_"}:
                self._rows = [r for r in self._rows if getattr(r, key, None) == value]
            elif op_name in {"ne", "is_not"}:
                self._rows = [r for r in self._rows if getattr(r, key, None) != value]
            elif op_name == "ge":
                self._rows = [r for r in self._rows if getattr(r, key, None) >= value]
            elif op_name == "le":
                self._rows = [r for r in self._rows if getattr(r, key, None) <= value]
            elif op_name == "gt":
                self._rows = [r for r in self._rows if getattr(r, key, None) > value]
            elif op_name == "lt":
                self._rows = [r for r in self._rows if getattr(r, key, None) < value]
            elif op_name == "is_not":
                self._rows = [r for r in self._rows if getattr(r, key, None) is not None]
        return self

    def order_by(self, *args, **kwargs):
        return self

    def distinct(self):
        return self

    def first(self):
        return self._rows[0] if self._rows else None

    def all(self):
        return self._rows


class FakeDB:
    def __init__(self, jobs=None, timesheets=None, shifts=None, holidays=None, manager_employee_ids=None):
        self.jobs = jobs or []
        self.timesheets = timesheets or []
        self.shifts = shifts or []
        self.holidays = holidays or []
        self.manager_employee_ids = manager_employee_ids or []

    def query(self, model):
        model_name = getattr(model, "__name__", str(model))
        if model_name == "WmJob":
            return FakeQuery(self.jobs)
        if model_name == "WmTimesheet":
            return FakeQuery(self.timesheets)
        if model_name == "WmShiftMaster":
            return FakeQuery(self.shifts)
        if model_name == "WmHolidayCalendar":
            return FakeQuery(self.holidays)
        if "assigned_employee_id" in model_name:
            return FakeQuery([(emp_id,) for emp_id in self.manager_employee_ids], skip_filter=True)
        return FakeQuery([])


def _job(emp_id, due, completed, status="Completed"):
    return SimpleNamespace(
        assigned_employee_id=emp_id,
        due_date=due,
        completed_at=completed,
        execution_status=status,
        is_active=True,
    )


def test_multi_employee_partial_failure_rules():
    evaluator = TeamCompletionEvaluationService()
    jobs = [
        _job(1, date(2026, 3, 1), completed=date(2026, 3, 1)),
        _job(2, date(2026, 3, 1), completed=date(2026, 3, 2)),
    ]
    jobs[0].completed_at = SimpleNamespace(date=lambda: date(2026, 3, 1))
    jobs[1].completed_at = SimpleNamespace(date=lambda: date(2026, 3, 2))
    out = evaluator.evaluate(jobs)
    assert out["is_multi_employee_task"] is True
    assert out["partial_team_failure_flag"] is True
    assert out["on_time_employee_count"] == 1
    assert out["late_employee_count"] == 1


def test_capacity_status_thresholds():
    service = CapacityPlanningService(db=None)
    assert service._status(50) == "Under Occupied"
    assert service._status(70) == "Optimally Occupied"
    assert service._status(90) == "Fully Occupied"
    assert service._status(110) == "Over Occupied"
    assert service._status(130) == "Critically Overloaded"


def test_capacity_calendar_month_week_day_and_math():
    jobs = [
        SimpleNamespace(
            assigned_employee_id=1,
            is_active=True,
            execution_status="Open",
            start_date=date(2026, 3, 3),
            due_date=date(2026, 3, 5),
            planned_hours=Decimal("18.0"),
            manager_id=7,
        )
    ]
    timesheets = [
        SimpleNamespace(emp_id=1, work_date=date(2026, 3, 3), hours=Decimal("5.0"), is_active=True),
        SimpleNamespace(emp_id=1, work_date=date(2026, 3, 4), hours=Decimal("7.0"), is_active=True),
    ]
    shift = SimpleNamespace(shift_id=1, total_working_hours=Decimal("9.0"), weekly_off_pattern="Sunday")
    holidays = [SimpleNamespace(holiday_date=date(2026, 3, 6), weekly_off=False, description="Festival")]
    service = CapacityCalendarService(FakeDB(jobs=jobs, timesheets=timesheets, shifts=[shift], holidays=holidays))

    month = service.month_view(1, date(2026, 3, 15))
    week = service.week_view(1, date(2026, 3, 4))
    day = service.day_view(1, date(2026, 3, 4))

    assert month["mode"] == "month"
    assert week["mode"] == "week"
    assert day["mode"] == "day"
    assert day["days"][0]["planned_hours"] == 6.0
    assert day["days"][0]["actual_hours"] == 7.0
    assert day["days"][0]["free_hours"] == 3.0
    holiday_row = [d for d in month["days"] if d["date"] == date(2026, 3, 6)][0]
    assert holiday_row["is_holiday"] is True
    assert holiday_row["available_hours"] == 0.0


def test_calendar_drilldown_and_team_summary():
    jobs = [
        SimpleNamespace(
            assigned_employee_id=1,
            is_active=True,
            execution_status="Open",
            start_date=date(2026, 3, 10),
            due_date=date(2026, 3, 10),
            planned_hours=Decimal("12"),
            manager_id=11,
        ),
        SimpleNamespace(
            assigned_employee_id=2,
            is_active=True,
            execution_status="Open",
            start_date=date(2026, 3, 10),
            due_date=date(2026, 3, 10),
            planned_hours=Decimal("8"),
            manager_id=11,
        ),
    ]
    shift = SimpleNamespace(shift_id=1, total_working_hours=Decimal("9.0"), weekly_off_pattern="Sunday")
    db = FakeDB(jobs=jobs, shifts=[shift], manager_employee_ids=[1, 2])

    drill = CalendarDrilldownService(db).run(1, date(2026, 3, 10), mode="day")
    assert drill["mode"] == "day"
    assert drill["totals"]["overload_hours"] == 3.0

    summary = TeamCapacityService(db).manager_summary(11, date(2026, 3, 10), date(2026, 3, 10))
    assert summary["employee_count"] == 2
    assert summary["team_totals"]["planned_hours"] == 20.0
