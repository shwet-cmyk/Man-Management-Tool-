from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.integration_hub.schemas import (
    ApiKeyCreateRequest,
    IntegrationExpensePushRequest,
    IntegrationTaskCreateRequest,
    IntegrationTaskUpdateRequest,
    IntegrationTimesheetPushRequest,
    TransactionPushRequest,
    WebhookCreateRequest,
)
from app.modules.integration_hub.service import IntegrationHubService

router = APIRouter(prefix="/wm/integrations", tags=["Work Management - Integration Hub"])


@router.post("/api-keys")
def create_api_key(payload: ApiKeyCreateRequest, db: Session = Depends(get_db)):
    return IntegrationHubService(db).create_api_key(payload)


def _auth(db: Session, x_api_key: str | None):
    if not x_api_key:
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="Missing x-api-key header")
    return IntegrationHubService(db).validate_key(x_api_key)


@router.post("/webhooks")
def register_webhook(payload: WebhookCreateRequest, db: Session = Depends(get_db), x_api_key: str | None = Header(default=None)):
    _auth(db, x_api_key)
    return IntegrationHubService(db).register_webhook(payload)


@router.post("/task")
def create_task(payload: IntegrationTaskCreateRequest, db: Session = Depends(get_db), x_api_key: str | None = Header(default=None)):
    key = _auth(db, x_api_key)
    return IntegrationHubService(db).create_task(payload, key.api_key_id)


@router.put("/task/{task_id}")
def update_task(task_id: int, payload: IntegrationTaskUpdateRequest, db: Session = Depends(get_db), x_api_key: str | None = Header(default=None)):
    key = _auth(db, x_api_key)
    return IntegrationHubService(db).update_task(task_id, payload, key.api_key_id)


@router.get("/jobs/{job_id}")
def fetch_job(job_id: int, db: Session = Depends(get_db), x_api_key: str | None = Header(default=None)):
    key = _auth(db, x_api_key)
    return IntegrationHubService(db).fetch_job(job_id, key.api_key_id)


@router.post("/timesheets")
def push_timesheet(payload: IntegrationTimesheetPushRequest, db: Session = Depends(get_db), x_api_key: str | None = Header(default=None)):
    key = _auth(db, x_api_key)
    return IntegrationHubService(db).push_timesheet(payload, key.api_key_id)


@router.post("/expenses")
def push_expense(payload: IntegrationExpensePushRequest, db: Session = Depends(get_db), x_api_key: str | None = Header(default=None)):
    key = _auth(db, x_api_key)
    return IntegrationHubService(db).push_expense(payload, key.api_key_id)


@router.post("/finance/transactions")
def push_transaction(payload: TransactionPushRequest, db: Session = Depends(get_db), x_api_key: str | None = Header(default=None)):
    key = _auth(db, x_api_key)
    return IntegrationHubService(db).push_transaction(payload, key.api_key_id)
