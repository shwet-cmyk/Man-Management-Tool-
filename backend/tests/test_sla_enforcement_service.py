from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.models.sla_tracking import SlaTracking
from app.modules.sla_enforcement.service import SlaEnforcementService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_sla_deadline_and_breach_monitoring():
    db = setup_db()
    svc = SlaEnforcementService(db)

    start = datetime.utcnow().replace(microsecond=0).isoformat()
    out = svc.start_tracking(ticket_id="T-1", priority="HIGH", created_at=start)
    assert out["status"] == "WITHIN_SLA"

    row = db.query(SlaTracking).filter(SlaTracking.id == out["sla_id"]).first()
    row.deadline = datetime.utcnow() - timedelta(minutes=1)
    db.commit()

    check = svc.monitor_and_escalate()
    assert check["breached"] == 1


def test_working_days_skip_weekend():
    db = setup_db()
    svc = SlaEnforcementService(db)

    # Friday
    friday = datetime(2026, 3, 27, 10, 0, 0)
    deadline = svc.add_working_days(friday, 1)
    assert deadline.weekday() == 0
