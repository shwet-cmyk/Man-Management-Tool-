from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.timesheets.schemas import (
    TimesheetCreateRequest,
    TimesheetCreateResponse,
    TimesheetDecisionRequest,
    TimesheetDecisionResponse,
    TimesheetSubmitRequest,
    TimesheetSubmitResponse,
)
from app.modules.timesheets.service import TimesheetService

router = APIRouter(prefix="/wm/timesheets", tags=["Work Management - Timesheets"])


@router.post("", response_model=TimesheetCreateResponse)
def create_timesheet(payload: TimesheetCreateRequest, db: Session = Depends(get_db)):
    return TimesheetService(db).create_timesheet(payload)


@router.post("/{timesheet_id}/submit", response_model=TimesheetSubmitResponse)
def submit_timesheet(timesheet_id: int, payload: TimesheetSubmitRequest, db: Session = Depends(get_db)):
    return TimesheetService(db).submit_timesheet(timesheet_id=timesheet_id, remarks=payload.remarks)


@router.post("/{timesheet_id}/decision", response_model=TimesheetDecisionResponse)
def decide_timesheet(timesheet_id: int, payload: TimesheetDecisionRequest, db: Session = Depends(get_db)):
    return TimesheetService(db).decide_timesheet(timesheet_id=timesheet_id, payload=payload)
