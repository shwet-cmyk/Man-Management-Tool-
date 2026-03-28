from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.modules.tickets.schemas import (
    TaskRolloverRequest,
    TicketConvertToTaskRequest,
    TicketCreateRequest,
    TicketDashboardRequest,
    TicketFollowupRequest,
    TicketPauseRequest,
    TicketUpdateRequest,
)
from app.modules.tickets.service import TicketService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_ticket_lifecycle_sla_pause_reopen_and_dashboard():
    db = setup_db()
    svc = TicketService(db)

    created = svc.create_ticket(
        TicketCreateRequest(
            created_by=1,
            subject="Login service down",
            description="Cannot login",
            priority="High",
            customer_id=100,
            customer_name="ABC Corp",
            assign_executive_id=501,
            assign_executive_name="Exec A",
            company_id=1,
            branch_id=1,
            department_id=10,
            category="AUTH",
        )
    )
    assert created["status"] == "ASSIGNED"

    ticket_id = created["ticket_id"]

    svc.update_ticket(
        ticket_id,
        TicketUpdateRequest(status="In_Progress", changed_by=501, remark="Investigating"),
    )

    followup = svc.add_followup(
        ticket_id,
        TicketFollowupRequest(
            action_type="RESPONSE",
            previous_status="IN_PROGRESS",
            new_status="WAITING_FOR_CUSTOMER",
            note="Please share logs",
            created_by=501,
            is_customer_visible=True,
        ),
    )
    assert followup["followup_id"] > 0

    paused = svc.pause_or_resume(ticket_id, TicketPauseRequest(paused=True, reason="Awaiting customer", changed_by=501))
    assert paused["paused"] is True

    resumed = svc.pause_or_resume(ticket_id, TicketPauseRequest(paused=False, reason="Customer replied", changed_by=501))
    assert resumed["paused"] is False

    svc.update_ticket(
        ticket_id,
        TicketUpdateRequest(status="Resolved", changed_by=501, resolution_note="Fix deployed"),
    )
    closed = svc.update_ticket(
        ticket_id,
        TicketUpdateRequest(status="Closed", changed_by=501, resolution_note="Customer confirmed"),
    )
    assert closed["status"] == "CLOSED"

    reopened = svc.update_ticket(
        ticket_id,
        TicketUpdateRequest(status="Reopened", changed_by=501, remark="Issue returned"),
    )
    assert reopened["status"] == "REOPENED"

    task_link = svc.convert_to_task(ticket_id, TicketConvertToTaskRequest(created_by=501))
    assert task_link["task_id"] > 0

    metrics = svc.dashboard_metrics(TicketDashboardRequest())
    assert "ticket_dashboard" in metrics
    assert "rollover_dashboard" in metrics


def test_rollover_counting_and_critical_threshold():
    db = setup_db()
    svc = TicketService(db)

    base = datetime.utcnow().replace(microsecond=0)
    out1 = svc.register_task_rollover(
        TaskRolloverRequest(
            task_id=11,
            previous_due_at=base.isoformat(),
            revised_due_at=(base + timedelta(days=1)).isoformat(),
            changed_by=7,
            reason="Dependency delay",
        )
    )
    assert out1["rollover_count"] == 1

    out2 = svc.register_task_rollover(
        TaskRolloverRequest(
            task_id=11,
            previous_due_at=(base + timedelta(days=1)).isoformat(),
            revised_due_at=(base + timedelta(days=2)).isoformat(),
            changed_by=7,
            reason="Re-test needed",
        )
    )
    assert out2["rollover_count"] == 2

    out3 = svc.register_task_rollover(
        TaskRolloverRequest(
            task_id=11,
            previous_due_at=(base + timedelta(days=2)).isoformat(),
            revised_due_at=(base + timedelta(days=3)).isoformat(),
            changed_by=7,
            reason="Customer delay",
        )
    )
    assert out3["rollover_count"] >= 3
    assert out3["is_critical"] is True
