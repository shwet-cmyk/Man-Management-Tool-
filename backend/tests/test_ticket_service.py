from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.models.wm_ticket import WmTicket
from app.modules.sla.schemas import SlaRuleCreateRequest
from app.modules.sla.service import SlaService
from app.modules.tickets.schemas import TicketAssignRequest, TicketCommentRequest, TicketCreateRequest, TicketUpdateRequest
from app.modules.tickets.service import TicketService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_ticket_create_assign_comment_timeline_and_close_rule():
    db = setup_db()
    # optional SLA rule for ticket creation integration
    SlaService(db).create_rule(
        SlaRuleCreateRequest(
            module="TICKET",
            condition={"priority": "HIGH"},
            response_time=1,
            resolution_time=4,
            unit="hours",
            escalation_config={"levels": [], "notify": ["in_app"]},
        )
    )

    svc = TicketService(db)
    out = svc.create_ticket(
        TicketCreateRequest(
            customer_id=1001,
            subject="Payment gateway not working",
            description="Unable to receive callbacks",
            priority="HIGH",
            channel="EMAIL",
            created_by=10,
            company_id=1,
            branch_id=10,
            department_id=20,
            auto_assign=True,
        )
    )
    assert out["ticket_id"] > 0

    ticket_id = out["ticket_id"]
    svc.assign_users(ticket_id, TicketAssignRequest(user_ids=[2001, 2002], role="WATCHER"))
    svc.add_comment(ticket_id, TicketCommentRequest(user_id=2001, message="Investigating issue", is_internal=True))

    # close without resolution should fail
    failed = False
    try:
        svc.update_ticket(ticket_id, TicketUpdateRequest(status="CLOSED", changed_by=2001))
    except Exception:
        failed = True
    assert failed

    updated = svc.update_ticket(ticket_id, TicketUpdateRequest(status="RESOLVED", resolution_note="Webhook URL fixed", changed_by=2001))
    assert updated["status"] == "RESOLVED"

    timeline = svc.timeline(ticket_id)
    assert timeline["ticket"]["ticket_id"] == ticket_id
    assert len(timeline["history"]) >= 1


def test_ticket_duplicate_detection():
    db = setup_db()
    svc = TicketService(db)
    p = TicketCreateRequest(subject="Duplicate test", description="x", created_by=1, customer_id=1)
    first = svc.create_ticket(p)
    second = svc.create_ticket(p)
    assert first["ticket_id"] == second["ticket_id"]
    assert "Duplicate" in second["message"]

    # ensure persisted
    assert db.query(WmTicket).count() == 1
