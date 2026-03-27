from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.reports.schemas import (
    CreateReportRequest,
    CreateScheduleRequest,
    ExportReportRequest,
    RunReportRequest,
    SaveReportConfigRequest,
)
from app.modules.reports.service import ReportsService

router = APIRouter(prefix="/wm/reports", tags=["Work Management - Reports"])


@router.post("")
def create_report(payload: CreateReportRequest, db: Session = Depends(get_db)):
    return ReportsService(db).create_report(payload)


@router.post("/config")
def save_report_config(payload: SaveReportConfigRequest, db: Session = Depends(get_db)):
    return ReportsService(db).save_config(payload)


@router.post("/run")
def run_report(payload: RunReportRequest, db: Session = Depends(get_db)):
    return ReportsService(db).run_report(payload)


@router.post("/export")
def export_report(payload: ExportReportRequest, db: Session = Depends(get_db)):
    return ReportsService(db).export_report(payload)


@router.post("/schedule")
def create_schedule(payload: CreateScheduleRequest, db: Session = Depends(get_db)):
    return ReportsService(db).create_schedule(payload)


@router.post("/schedule/run-due")
def run_due_schedules(db: Session = Depends(get_db)):
    return ReportsService(db).run_due_schedules()


@router.get("/standard/job-profitability")
def job_profitability(company_id: int | None = None, db: Session = Depends(get_db)):
    return ReportsService(db).standard_job_profitability(company_id=company_id)


@router.get("/standard/client-profitability")
def client_profitability(company_id: int | None = None, db: Session = Depends(get_db)):
    return ReportsService(db).standard_client_profitability(company_id=company_id)


@router.get("/standard/employee-productivity")
def employee_productivity(company_id: int | None = None, db: Session = Depends(get_db)):
    return ReportsService(db).standard_employee_productivity(company_id=company_id)


@router.get("/standard/unbilled-work")
def unbilled_work(company_id: int | None = None, db: Session = Depends(get_db)):
    return ReportsService(db).standard_unbilled_work(company_id=company_id)


@router.get("/standard/overrun-analysis")
def overrun_analysis(company_id: int | None = None, db: Session = Depends(get_db)):
    return ReportsService(db).standard_overrun_analysis(company_id=company_id)


@router.get("/standard/exceptions")
def exception_report(company_id: int | None = None, db: Session = Depends(get_db)):
    return ReportsService(db).standard_exception_report(company_id=company_id)
