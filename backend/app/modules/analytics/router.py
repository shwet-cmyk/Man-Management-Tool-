from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.analytics.schemas import AnalyticsEntityType, AnalyticsQueryRequest, AnalyticsReportRequest, ExceptionType, RefreshExceptionsRequest
from app.modules.analytics.service import AnalyticsService

router = APIRouter(prefix="/wm/analytics", tags=["Work Management - Analytics"])


@router.get("/profitability")
def get_profitability(
    entity_type: AnalyticsEntityType = Query(...),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    company_id: int | None = Query(None),
    branch_id: int | None = Query(None),
    department_id: int | None = Query(None),
    customer_id: int | None = Query(None),
    job_id: int | None = Query(None),
    task_id: int | None = Query(None),
    emp_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    return AnalyticsService(db).get_profitability(
        entity_type=entity_type,
        date_from=date_from,
        date_to=date_to,
        company_id=company_id,
        branch_id=branch_id,
        department_id=department_id,
        customer_id=customer_id,
        job_id=job_id,
        task_id=task_id,
        emp_id=emp_id,
    )


@router.get("/exceptions")
def get_exceptions(
    exception_type: ExceptionType | None = Query(None),
    entity_type: str | None = Query(None),
    company_id: int | None = Query(None),
    manager_id: int | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return AnalyticsService(db).get_exception_queue(
        exception_type=exception_type,
        entity_type=entity_type,
        company_id=company_id,
        manager_id=manager_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.post("/exceptions/refresh")
def refresh_exceptions(payload: RefreshExceptionsRequest, db: Session = Depends(get_db)):
    return AnalyticsService(db).refresh_exceptions(company_id=payload.company_id, entity_scope=payload.entity_scope)


@router.post("/query")
def query_analytics(payload: AnalyticsQueryRequest, db: Session = Depends(get_db)):
    return AnalyticsService(db).query_analytics(payload.dimensions, payload.metrics, payload.filters)


@router.post("/report")
def generate_report(payload: AnalyticsReportRequest, db: Session = Depends(get_db)):
    return AnalyticsService(db).generate_report(payload.name, payload.query.dimensions, payload.query.metrics, payload.query.filters)


@router.get("/dashboard")
def analytics_dashboard(db: Session = Depends(get_db)):
    return AnalyticsService(db).get_dashboard_summary()
