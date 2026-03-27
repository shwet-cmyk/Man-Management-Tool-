from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.integrations.tez_erp_client import TezERPClient
from app.modules.master_sync.schemas import (
    EmployeeSyncRequest,
    EmployeeSyncResult,
    EmployeeSyncSummary,
    RefEmployeeRead,
    SyncLogRead,
)
from app.modules.master_sync.service import (
    EmployeeSyncService,
    get_employee_summary,
    list_ref_employees,
    list_sync_logs,
)

router = APIRouter(prefix="/sync/employees", tags=["Master Sync - Employees"])


@router.post("", response_model=EmployeeSyncResult)
def sync_employees(payload: EmployeeSyncRequest, db: Session = Depends(get_db)):
    service = EmployeeSyncService(db=db, erp_client=TezERPClient())
    return service.sync_employees(sync_mode=payload.sync_mode)


@router.get("/summary", response_model=EmployeeSyncSummary)
def employee_sync_summary(db: Session = Depends(get_db)):
    return get_employee_summary(db)


@router.get("/logs", response_model=list[SyncLogRead])
def employee_sync_logs(limit: int = Query(default=20, ge=1, le=200), db: Session = Depends(get_db)):
    return list_sync_logs(db, limit=limit)


@router.get("/cache", response_model=list[RefEmployeeRead])
def employee_cache(db: Session = Depends(get_db)):
    return list_ref_employees(db)
