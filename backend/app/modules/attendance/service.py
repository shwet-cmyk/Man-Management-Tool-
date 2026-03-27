from datetime import date

from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.schemas.attendance import AttendanceCreate


def list_attendance(db: Session, work_date: date | None = None) -> list[Attendance]:
    query = db.query(Attendance).order_by(Attendance.work_date.desc())
    if work_date:
        query = query.filter(Attendance.work_date == work_date)
    return query.all()


def create_attendance(db: Session, payload: AttendanceCreate) -> Attendance:
    attendance = Attendance(**payload.model_dump())
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance
