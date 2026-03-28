from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.attendance.service import create_attendance, list_attendance
from app.schemas.attendance import AttendanceCreate, AttendanceRead

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.get("", response_model=list[AttendanceRead])
def get_attendance(
    work_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return list_attendance(db, work_date)


@router.post("", response_model=AttendanceRead, status_code=status.HTTP_201_CREATED)
def add_attendance(payload: AttendanceCreate, db: Session = Depends(get_db)):
    return create_attendance(db, payload)
