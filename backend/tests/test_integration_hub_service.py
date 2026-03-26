from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.models.wm_api_log import WmApiLog
from app.models.wm_job import WmJob
from app.models.wm_webhook_log import WmWebhookLog
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


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_integration_hub_auth_and_endpoints():
    db = setup_db()
    svc = IntegrationHubService(db)
    key = svc.create_api_key(ApiKeyCreateRequest(client_name="CRM", api_key="k1", rate_limit_per_minute=1000))
    api_key = svc.validate_key("k1")
    assert key["client_name"] == "CRM"

    db.add(WmJob(job_id=5001, job_no="JOB-1", company_id=1, customer_id=11, job_name="Integration Job", is_billable=True, created_by=1, execution_status="Open", billing_status="Not Billed"))
    db.commit()

    svc.register_webhook(WebhookCreateRequest(event_name="TASK_CREATED", url="https://example.com/hook"))
    task = svc.create_task(
        IntegrationTaskCreateRequest(company_id=1, job_id=5001, title="External Task", assigned_users=[101], deadline=datetime.utcnow() + timedelta(days=2), created_by=1),
        api_key.api_key_id,
    )
    svc.update_task(task["task_id"], IntegrationTaskUpdateRequest(status_code="In Progress"), api_key.api_key_id)
    job = svc.fetch_job(5001, api_key.api_key_id)
    assert job["task_count"] == 1

    timesheet = svc.push_timesheet(
        IntegrationTimesheetPushRequest(company_id=1, job_id=5001, task_id=task["task_id"], emp_id=101, work_date=date.today(), hours=Decimal("2"), billable_hours=Decimal("2"), created_by=1),
        api_key.api_key_id,
    )
    assert timesheet["timesheet_id"] > 0

    expense = svc.push_expense(
        IntegrationExpensePushRequest(company_id=1, emp_id=101, expense_date=date.today(), amount=Decimal("100"), tax_amount=Decimal("18"), expense_type="Travel", created_by=1, job_id=5001, task_id=task["task_id"]),
        api_key.api_key_id,
    )
    assert expense["claim_id"] > 0

    trx = svc.push_transaction(TransactionPushRequest(source="INVOICE", reference_no="INV-1", payload={"amount": 1000}), api_key.api_key_id)
    assert trx["status"] == "RECEIVED"

    assert db.query(WmApiLog).count() >= 6
    assert db.query(WmWebhookLog).count() >= 1
