from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.man_management.schemas import ApprovalActionRequest, BillingActionRequest, EmployeeGroupCreateRequest, HolidayCreateRequest, JobTaskLineRequest, JobTaskStatusRequest, JobUpsertRequest, SettingsUpsertRequest, TimesheetEntryRequest
from app.modules.man_management.service import ManManagementService

router = APIRouter(prefix="/wm/man-management", tags=["Man Management"])


@router.post("/employee-groups")
def create_employee_group(payload: EmployeeGroupCreateRequest, db: Session = Depends(get_db)):
    return ManManagementService(db).create_employee_group(payload)


@router.get("/employee-groups")
def list_employee_groups(active_flag: bool | None = None, search: str | None = None, db: Session = Depends(get_db)):
    return ManManagementService(db).list_employee_groups(active_flag=active_flag, search=search)


@router.post("/holidays")
def create_holiday(payload: HolidayCreateRequest, db: Session = Depends(get_db)):
    return ManManagementService(db).create_holiday(payload)


@router.get("/holidays")
def list_holidays(company_id: int | None = None, branch_id: int | None = None, db: Session = Depends(get_db)):
    return ManManagementService(db).list_holidays(company_id=company_id, branch_id=branch_id)


@router.post("/settings")
def upsert_settings(payload: SettingsUpsertRequest, db: Session = Depends(get_db)):
    return ManManagementService(db).upsert_settings(payload)


@router.post("/jobs")
def create_job(payload: JobUpsertRequest, db: Session = Depends(get_db)):
    return ManManagementService(db).create_job(payload)


@router.put("/jobs/{job_id}")
def edit_job(job_id: int, payload: JobUpsertRequest, db: Session = Depends(get_db)):
    return ManManagementService(db).edit_job(job_id, payload)


@router.post("/jobs/{job_id}/copy")
def copy_job(job_id: int, include_task_lines: bool = True, created_by: int = 1, db: Session = Depends(get_db)):
    return ManManagementService(db).copy_job(job_id, created_by=created_by, include_task_lines=include_task_lines)


@router.delete("/jobs/{job_id}")
def delete_job(job_id: int, deleted_by: int = 1, db: Session = Depends(get_db)):
    return ManManagementService(db).delete_job(job_id, deleted_by=deleted_by)


@router.get("/jobs/{job_id}")
def view_job(job_id: int, db: Session = Depends(get_db)):
    return ManManagementService(db).view_job(job_id)


@router.get("/jobs")
def job_register(db: Session = Depends(get_db)):
    return ManManagementService(db).job_register()


@router.post("/job-task-lines")
def add_job_task_line(payload: JobTaskLineRequest, db: Session = Depends(get_db)):
    return ManManagementService(db).add_job_task_line(payload)


@router.post("/job-task-lines/{job_task_id}/status")
def update_job_task_status(job_task_id: int, payload: JobTaskStatusRequest, db: Session = Depends(get_db)):
    return ManManagementService(db).update_job_task_status(job_task_id, payload)


@router.post("/timesheets")
def add_timesheet(payload: TimesheetEntryRequest, db: Session = Depends(get_db)):
    return ManManagementService(db).add_timesheet(payload)


@router.get("/timesheets")
def timesheet_register(db: Session = Depends(get_db)):
    return ManManagementService(db).timesheet_register()


@router.post("/approvals/action")
def approval_action(payload: ApprovalActionRequest, db: Session = Depends(get_db)):
    return ManManagementService(db).approval_action(payload)


@router.get("/jobs/{job_id}/billing-readiness")
def billing_readiness(job_id: int, db: Session = Depends(get_db)):
    return ManManagementService(db).billing_readiness(job_id)


@router.post("/jobs/billing")
def mark_billed(payload: BillingActionRequest, db: Session = Depends(get_db)):
    return ManManagementService(db).mark_billed(payload)


@router.get("/dashboard")
def dashboard(manager_id: int | None = None, employee_id: int | None = None, db: Session = Depends(get_db)):
    return ManManagementService(db).dashboard(manager_id=manager_id, employee_id=employee_id)
