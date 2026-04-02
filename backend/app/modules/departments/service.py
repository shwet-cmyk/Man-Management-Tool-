from sqlalchemy.orm import Session

from app.models.department import Department
from app.schemas.department import DepartmentCreate


def list_departments(db: Session) -> list[Department]:
    return db.query(Department).order_by(Department.name.asc()).all()


def create_department(db: Session, payload: DepartmentCreate) -> Department:
    department = Department(**payload.model_dump())
    db.add(department)
    db.commit()
    db.refresh(department)
    return department
