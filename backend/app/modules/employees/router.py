from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.employees.service import create_employee, list_employees
from app.schemas.employee import EmployeeCreate, EmployeeRead

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("", response_model=list[EmployeeRead])
def get_employees(db: Session = Depends(get_db)):
    return list_employees(db)


@router.post("", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def add_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    return create_employee(db, payload)
