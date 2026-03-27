from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.departments.service import create_department, list_departments
from app.schemas.department import DepartmentCreate, DepartmentRead

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("", response_model=list[DepartmentRead])
def get_departments(db: Session = Depends(get_db)):
    return list_departments(db)


@router.post("", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
def add_department(payload: DepartmentCreate, db: Session = Depends(get_db)):
    return create_department(db, payload)
