from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.models.ref_employee import RefEmployee
from app.models.wm_billing_configuration import WmBillingConfiguration
from app.models.wm_billing_document_link import WmBillingDocumentLink
from app.models.wm_billing_readiness import WmBillingReadiness
from app.models.wm_expense_claim import WmExpenseClaim
from app.models.wm_job import WmJob
from app.models.wm_task import WmTask
from app.models.wm_timesheet import WmTimesheet
from app.modules.billing.schemas import (
    BillingConfigureRequest,
    InvoiceRequest,
    MarkReadyForBillingRequest,
    ProformaRequest,
    RemoveReadinessRequest,
)
from app.modules.billing.service import BillingService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def seed_base(db):
    now = datetime.utcnow()
    db.add(
        RefEmployee(
            emp_id=210,
            employee_name="Emp 210",
            company_id=1,
            branch_id=10,
            department_id=20,
            monthly_ctc=Decimal("100000"),
            hourly_cost=Decimal("625"),
            is_active=True,
            last_synced_at=now,
        )
    )
    db.add(
        WmJob(
            job_id=50021,
            job_no="JOB-2026-001",
            company_id=1,
            branch_id=10,
            department_id=20,
            customer_id=30,
            job_name="Compliance",
            is_billable=True,
            created_by=1,
            execution_status="Open",
            billing_status="Not Billed",
        )
    )
    db.add(
        WmTask(
            task_id=60015,
            task_no="TSK-2026-1",
            company_id=1,
            customer_id=30,
            job_id=50021,
            title="Task",
            task_type="Task",
            priority_code="Medium",
            status_code="Done",
            primary_owner_emp_id=210,
            billable_flag=True,
            billed_amount=Decimal("0"),
            estimated_hours=Decimal("5"),
            planned_start=now,
            due_at=now + timedelta(days=1),
            created_by=210,
            source_type="MANUAL",
        )
    )
    db.add(
        WmTimesheet(
            timesheet_id=90051,
            company_id=1,
            branch_id=10,
            department_id=20,
            customer_id=30,
            job_id=50021,
            task_id=60015,
            emp_id=210,
            work_date=date(2026, 4, 2),
            hours=Decimal("2"),
            billable_hours=Decimal("1.5"),
            overtime_hours=Decimal("0"),
            approval_status="Approved",
            created_by=210,
        )
    )
    db.add(
        WmExpenseClaim(
            claim_id=80011,
            claim_no="EXP-2026-00001",
            claim_type="REIMBURSEMENT",
            expense_type="Travel",
            company_id=1,
            branch_id=10,
            department_id=20,
            emp_id=210,
            job_id=50021,
            task_id=60015,
            customer_id=30,
            expense_date=date(2026, 4, 2),
            amount=Decimal("100"),
            tax_amount=Decimal("0"),
            total_amount=Decimal("100"),
            recoverable_flag=True,
            approval_status="Approved",
            created_by=210,
        )
    )
    db.commit()


def _configure_ready(service, monkeypatch):
    monkeypatch.setattr(service.tez_client, "master_exists", lambda *args, **kwargs: True)
    service.configure_billing(
        BillingConfigureRequest(
            entity_type="TASK",
            job_id=50021,
            task_id=60015,
            customer_id=30,
            billable_flag=True,
            billing_model="TIME_MATERIAL",
        )
    )
    service.mark_ready_for_billing(MarkReadyForBillingRequest(entity_type="TASK", job_id=50021, task_id=60015))


def test_configure_billing_task_success(monkeypatch):
    db = setup_db()
    seed_base(db)
    service = BillingService(db)
    monkeypatch.setattr(service.tez_client, "master_exists", lambda *args, **kwargs: True)

    result = service.configure_billing(
        BillingConfigureRequest(
            entity_type="TASK",
            job_id=50021,
            task_id=60015,
            customer_id=30,
            billable_flag=True,
            billing_model="TIME_MATERIAL",
            billing_remarks="Client approved",
        )
    )

    assert result["billing_status"] == "Billable"
    config = db.query(WmBillingConfiguration).first()
    assert config.task_id == 60015


def test_mark_ready_task_success(monkeypatch):
    db = setup_db()
    seed_base(db)
    service = BillingService(db)
    _configure_ready(service, monkeypatch)

    ready = db.query(WmBillingReadiness).first()
    assert ready.billing_status == "Ready for Billing"
    assert Decimal(str(ready.included_billable_hours)) == Decimal("1.5")
    assert Decimal(str(ready.included_recoverable_expense)) == Decimal("100")


def test_remove_readiness_success(monkeypatch):
    db = setup_db()
    seed_base(db)
    service = BillingService(db)
    _configure_ready(service, monkeypatch)

    result = service.remove_readiness(RemoveReadinessRequest(entity_type="TASK", task_id=60015))

    assert result["billing_status"] == "Billable"
    readiness = db.query(WmBillingReadiness).first()
    assert readiness.ready_for_billing_flag is False


def test_create_proforma_success(monkeypatch):
    db = setup_db()
    seed_base(db)
    service = BillingService(db)
    _configure_ready(service, monkeypatch)

    result = service.process_proforma(ProformaRequest(entity_type="TASK", job_id=50021, task_id=60015, action_type="CREATE"))

    assert result["billing_status"] == "Proforma Created"
    assert result["proforma_no"].startswith("PRO-")


def test_link_existing_proforma_success(monkeypatch):
    db = setup_db()
    seed_base(db)
    service = BillingService(db)
    _configure_ready(service, monkeypatch)

    result = service.process_proforma(
        ProformaRequest(entity_type="TASK", job_id=50021, task_id=60015, action_type="LINK_EXISTING", proforma_no="PRO-EXT-1001")
    )

    assert result["proforma_no"] == "PRO-EXT-1001"


def test_create_invoice_success(monkeypatch):
    db = setup_db()
    seed_base(db)
    service = BillingService(db)
    _configure_ready(service, monkeypatch)

    result = service.process_invoice(
        InvoiceRequest(
            entity_type="TASK",
            job_id=50021,
            task_id=60015,
            action_type="CREATE",
            billed_amount=Decimal("250"),
        )
    )

    assert result["invoice_no"].startswith("INV-")
    assert result["billing_status"] == "Partially Billed"


def test_link_invoice_non_ready_fails(monkeypatch):
    db = setup_db()
    seed_base(db)
    service = BillingService(db)
    monkeypatch.setattr(service.tez_client, "master_exists", lambda *args, **kwargs: True)
    service.configure_billing(
        BillingConfigureRequest(
            entity_type="TASK",
            job_id=50021,
            task_id=60015,
            customer_id=30,
            billable_flag=True,
            billing_model="TIME_MATERIAL",
        )
    )

    with pytest.raises(HTTPException):
        service.process_invoice(
            InvoiceRequest(
                entity_type="TASK",
                job_id=50021,
                task_id=60015,
                action_type="LINK_EXISTING",
                invoice_no="INV-2026-00488",
                billed_amount=Decimal("50"),
            )
        )


def test_partial_then_full_billing_status(monkeypatch):
    db = setup_db()
    seed_base(db)
    service = BillingService(db)
    _configure_ready(service, monkeypatch)

    service.process_invoice(
        InvoiceRequest(
            entity_type="TASK",
            job_id=50021,
            task_id=60015,
            action_type="LINK_EXISTING",
            invoice_no="INV-EXT-1",
            billed_amount=Decimal("100"),
        )
    )

    result = service.process_invoice(
        InvoiceRequest(
            entity_type="TASK",
            job_id=50021,
            task_id=60015,
            action_type="LINK_EXISTING",
            invoice_no="INV-EXT-2",
            billed_amount=Decimal("150"),
        )
    )

    assert result["billing_status"] == "Fully Billed"
    assert result["remaining_unbilled_amount"] == Decimal("0")


def test_duplicate_invoice_reference_fails(monkeypatch):
    db = setup_db()
    seed_base(db)
    service = BillingService(db)
    _configure_ready(service, monkeypatch)

    service.process_invoice(
        InvoiceRequest(
            entity_type="TASK",
            job_id=50021,
            task_id=60015,
            action_type="LINK_EXISTING",
            invoice_no="INV-DUP-1",
            billed_amount=Decimal("100"),
        )
    )

    with pytest.raises(HTTPException):
        service.process_invoice(
            InvoiceRequest(
                entity_type="TASK",
                job_id=50021,
                task_id=60015,
                action_type="LINK_EXISTING",
                invoice_no="INV-DUP-1",
                billed_amount=Decimal("50"),
            )
        )


def test_underbilled_invoice_allowed(monkeypatch):
    db = setup_db()
    seed_base(db)
    service = BillingService(db)
    _configure_ready(service, monkeypatch)

    result = service.process_invoice(
        InvoiceRequest(
            entity_type="TASK",
            job_id=50021,
            task_id=60015,
            action_type="LINK_EXISTING",
            invoice_no="INV-LOW-1",
            billed_amount=Decimal("200"),
            billed_date=date(2026, 4, 30),
            billing_remarks="Lower than recommended",
        )
    )

    assert result["billing_status"] == "Partially Billed"
    row = db.query(WmBillingDocumentLink).filter(WmBillingDocumentLink.billing_reference_no == "INV-LOW-1").first()
    assert Decimal(str(row.billed_amount)) == Decimal("200")
