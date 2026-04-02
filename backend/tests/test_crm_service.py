from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.modules.crm.schemas import DealCreateRequest, DealInvoiceRequest, FollowupCreateRequest, LeadCreateRequest, LifecycleUpdateRequest
from app.modules.crm.service import CrmService
from app.modules.rbac.schemas import ApprovalLimitRequest
from app.modules.rbac.service import RbacService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_lead_to_opportunity_to_deal_to_invoice_flow():
    db = setup_db()
    crm = CrmService(db)
    rbac = RbacService(db)

    lead = crm.create_lead(LeadCreateRequest(name="Acme Lead", source="REFERRAL", assigned_users=[10], estimated_value=150000), performed_by=10)
    crm.create_followup(
        FollowupCreateRequest(
            entity_type="LEAD",
            entity_id=lead["lead_id"],
            next_followup_date=datetime.utcnow() - timedelta(hours=1),
            remarks="Initial follow-up done",
            assigned_to=10,
        )
    )

    opp = crm.convert_lead_to_opportunity(lead["lead_id"], performed_by=10)
    assert opp["probability"] >= 50

    deal = crm.create_deal(DealCreateRequest(opportunity_id=opp["opportunity_id"], negotiated_value=120000, customer_name="Acme"), performed_by=10)
    rbac.upsert_approval_limit(99, ApprovalLimitRequest(module_name="SALES", max_amount=200000))
    invoice = crm.convert_deal_to_invoice(deal["deal_id"], DealInvoiceRequest(approved_by=99, push_to_tez=False))
    assert invoice["status"] == "INVOICED"
    assert invoice["invoice_voucher_no"].startswith("INV-")


def test_followup_due_and_lifecycle_update():
    db = setup_db()
    crm = CrmService(db)

    lead = crm.create_lead(LeadCreateRequest(name="Beta", source="WEB", assigned_users=[], estimated_value=10000), performed_by=1)
    crm.create_followup(
        FollowupCreateRequest(
            entity_type="LEAD",
            entity_id=lead["lead_id"],
            next_followup_date=datetime.utcnow() - timedelta(days=1),
            remarks="due",
            assigned_to=5,
        )
    )
    due = crm.due_followups()
    assert len(due) >= 1

    lifecycle = crm.upsert_customer_lifecycle(LifecycleUpdateRequest(customer_id=5001, stage="AT_RISK", churn_risk_score=78))
    assert lifecycle["stage"] == "AT_RISK"
