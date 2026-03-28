from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.performance_engine.schemas import (
    CalendarDrilldownRequest,
    CalendarFilterRequest,
    CapacityRequest,
    EmployeeCalendarRequest,
    EmployeeSummaryRequest,
    ScoreTaskRequest,
    TeamCalendarRequest,
)
from app.modules.performance_engine.service import (
    CalendarDrilldownService,
    CapacityCalendarService,
    DashboardAggregationService,
    GamificationService,
    ScoreAuditService,
    TeamCapacityService,
    UtilizationAnalyticsService,
)

router = APIRouter(prefix="/performance-engine", tags=["Performance Engine"])


@router.post("/score-task")
def score_task(payload: ScoreTaskRequest, db: Session = Depends(get_db)):
    return GamificationService(db).evaluate_task_and_award(payload.parent_task_id, payload.created_by)


@router.post("/employee-scorecard")
def employee_scorecard(payload: EmployeeSummaryRequest, db: Session = Depends(get_db)):
    start = payload.start_date or date(date.today().year, 1, 1)
    end = payload.end_date or date.today()
    return DashboardAggregationService(db).employee_scorecard(payload.employee_id, start, end)


@router.post("/capacity")
def employee_capacity(payload: CapacityRequest, db: Session = Depends(get_db)):
    return UtilizationAnalyticsService(db).capacity.employee_capacity(payload.employee_id, payload.start_date, payload.end_date)


@router.get("/reports/points-ledger")
def points_ledger(employee_id: int | None = None, db: Session = Depends(get_db)):
    return {"status": "success", "rows": ScoreAuditService(db).ledger_report(employee_id=employee_id)}


@router.post("/calendar/employee/month")
def employee_calendar_month(payload: EmployeeCalendarRequest, db: Session = Depends(get_db)):
    return CapacityCalendarService(db).month_view(payload.employee_id, payload.reference_date)


@router.post("/calendar/employee/week")
def employee_calendar_week(payload: EmployeeCalendarRequest, db: Session = Depends(get_db)):
    return CapacityCalendarService(db).week_view(payload.employee_id, payload.reference_date)


@router.post("/calendar/employee/day")
def employee_calendar_day(payload: EmployeeCalendarRequest, db: Session = Depends(get_db)):
    return CapacityCalendarService(db).day_view(payload.employee_id, payload.reference_date)


@router.post("/calendar/drilldown")
def calendar_drilldown(payload: CalendarDrilldownRequest, db: Session = Depends(get_db)):
    return CalendarDrilldownService(db).run(payload.employee_id, payload.reference_date, payload.mode)


@router.post("/calendar/team-summary")
def team_calendar_summary(payload: TeamCalendarRequest, db: Session = Depends(get_db)):
    return TeamCapacityService(db).manager_summary(payload.manager_id, payload.start_date, payload.end_date)


@router.post("/widgets/calendar-capacity")
def calendar_capacity_widget(payload: EmployeeCalendarRequest, db: Session = Depends(get_db)):
    return DashboardAggregationService(db).calendar_capacity_widgets(payload.employee_id, payload.reference_date)


@router.post("/reports/capacity")
def capacity_report(payload: CalendarFilterRequest, db: Session = Depends(get_db)):
    if payload.employee_id:
        return ScoreAuditService(db).capacity_report(payload.employee_id, payload.start_date, payload.end_date)
    if payload.manager_id:
        return TeamCapacityService(db).manager_summary(payload.manager_id, payload.start_date, payload.end_date)
    return {"status": "error", "message": "Either employee_id or manager_id is required."}
