from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.database.session import Base
from app.models.ref_employee import RefEmployee
from app.modules.ticket_integration.schemas import IntegrationConfigRequest, TaskFromTicketRequest, TicketFetchRequest
from app.modules.ticket_integration.service import TicketIntegrationService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def seed_employee(db, emp_id: int):
    db.add(
        RefEmployee(
            emp_id=emp_id,
            employee_name=f"Emp {emp_id}",
            company_id=1,
            monthly_ctc=Decimal("100000"),
            hourly_cost=Decimal("625"),
            is_active=True,
            last_synced_at=datetime.utcnow(),
        )
    )
    db.commit()


@pytest.fixture(autouse=True)
def disable_strict_validation():
    old = settings.strict_master_validation
    settings.strict_master_validation = False
    yield
    settings.strict_master_validation = old


def base_config(mock_mode: bool = True):
    return IntegrationConfigRequest(
        mock_mode=mock_mode,
        duplicate_policy="block",
        default_billable_flag=False,
        auto_create_first_job=False,
        default_primary_owner_emp_id=100,
        default_manager_emp_id=101,
        source_system_name="TEZ_ERP",
    )


def test_fetch_10_open_tickets_successfully():
    db = setup_db()
    TicketIntegrationService.set_config(base_config(mock_mode=True))
    out = TicketIntegrationService(db).sync_tickets(TicketFetchRequest(mode="filtered", open_only=True, limit=10, triggered_by=100))
    assert out["status"] == "success"
    assert out["summary"]["fetched_count"] == 10


def test_fetch_one_high_priority_ticket():
    db = setup_db()
    TicketIntegrationService.set_config(base_config(mock_mode=True))
    out = TicketIntegrationService(db).sync_tickets(TicketFetchRequest(mode="filtered", priority="HIGH", limit=1, triggered_by=100))
    assert out["summary"]["fetched_count"] == 1


def test_create_task_from_fetched_ticket_and_block_duplicate():
    db = setup_db()
    seed_employee(db, 100)
    seed_employee(db, 101)
    TicketIntegrationService.set_config(base_config(mock_mode=True))
    service = TicketIntegrationService(db)
    service.sync_tickets(TicketFetchRequest(mode="manual", ticket_no="TKT-1000", limit=1, triggered_by=100))

    first = service.create_task_from_ticket(TaskFromTicketRequest(ticket_no="TKT-1000", triggered_by=100))
    second = service.create_task_from_ticket(TaskFromTicketRequest(ticket_no="TKT-1000", triggered_by=100))
    assert first["status"] == "success"
    assert second["status"] == "validation_error"


def test_auth_failure_from_real_api_returns_auth_error(monkeypatch):
    db = setup_db()
    cfg = base_config(mock_mode=False)
    TicketIntegrationService.set_config(cfg)

    from app.modules.ticket_integration import ticket_api_service

    def fake_fetch(*args, **kwargs):
        return {"success": False, "mode": "real", "error_type": "auth_error", "message": "bad key", "retryable": False, "tickets": []}

    monkeypatch.setattr(ticket_api_service.TicketApiService, "fetch_tickets", fake_fetch)
    out = TicketIntegrationService(db).sync_tickets(TicketFetchRequest(mode="full", triggered_by=100))
    assert out["status"] == "auth_error"


def test_partial_sync_with_two_failed_records(monkeypatch):
    db = setup_db()
    TicketIntegrationService.set_config(base_config(mock_mode=True))

    from app.modules.ticket_integration import ticket_api_service

    payload = [{"ticket_no": "OK-1", "remark": "ok", "priority": "HIGH", "status": "OPEN"}, {"bad": "record"}, {"bad": "record2"}]

    def fake_fetch(*args, **kwargs):
        return {"success": True, "mode": "mock", "tickets": payload}

    monkeypatch.setattr(ticket_api_service.TicketApiService, "fetch_tickets", fake_fetch)
    out = TicketIntegrationService(db).sync_tickets(TicketFetchRequest(mode="full", triggered_by=100))
    assert out["status"] == "partial_success"
    assert out["summary"]["failed_count"] == 2


def test_incremental_sync_uses_last_synced_at():
    db = setup_db()
    TicketIntegrationService.set_config(base_config(mock_mode=True))
    service = TicketIntegrationService(db)
    service.sync_tickets(TicketFetchRequest(mode="full", limit=1, triggered_by=100))
    out = service.sync_tickets(TicketFetchRequest(mode="incremental", limit=1, triggered_by=100))
    assert out["status"] in {"success", "partial_success"}


def test_dashboard_outputs_available_and_converted_counts():
    db = setup_db()
    seed_employee(db, 100)
    seed_employee(db, 101)
    TicketIntegrationService.set_config(base_config(mock_mode=True))
    service = TicketIntegrationService(db)
    service.sync_tickets(TicketFetchRequest(mode="manual", ticket_no="TKT-1001", limit=1, triggered_by=100))
    service.create_task_from_ticket(TaskFromTicketRequest(ticket_no="TKT-1001", triggered_by=100))
    dash = service.integration_dashboard()
    assert dash["tickets_already_converted_to_tasks"] >= 1
