from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.models.wm_rbac_user_role import WmRbacUserRole
from app.models.wm_sla_escalation import WmSlaEscalation
from app.models.wm_sla_instance import WmSlaInstance
from app.modules.sla.schemas import HolidayCreateRequest, SlaRuleCreateRequest, SlaStartRequest
from app.modules.sla.service import SlaService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_sla_start_pause_resume_breach_and_escalate():
    db = setup_db()
    svc = SlaService(db)

    # escalation targets must have RBAC role
    db.add(WmRbacUserRole(user_id=9001, role_id=1))
    db.add(WmRbacUserRole(user_id=9002, role_id=2))
    db.commit()

    rule = svc.create_rule(
        SlaRuleCreateRequest(
            module="TASK",
            condition={"priority": "HIGH"},
            response_time=2,
            resolution_time=1,
            unit="hours",
            escalation_config={"levels": [{"user_id": 9001}, {"user_id": 9002}], "notify": ["email", "in_app"]},
            company_id=1,
            branch_id=10,
        )
    )
    assert rule["sla_policy_id"] > 0

    svc.add_holiday(HolidayCreateRequest(holiday_date="2026-01-01", name="New Year", company_id=1, branch_id=10))

    started = svc.start_sla(
        SlaStartRequest(
            module="TASK",
            entity_type="TASK",
            entity_id=501,
            assignee_user_id=101,
            company_id=1,
            branch_id=10,
            context={"priority": "HIGH"},
        )
    )
    sid = started["sla_instance_id"]
    assert sid > 0

    assert svc.pause(sid)["status"] == "PAUSED"
    assert svc.resume(sid)["status"] == "RUNNING"

    row = db.query(WmSlaInstance).filter(WmSlaInstance.sla_instance_id == sid).first()
    row.due_time = datetime.utcnow() - timedelta(minutes=1)
    db.commit()

    out = svc.check_and_escalate()
    assert out["breached"] >= 1
    assert db.query(WmSlaEscalation).filter(WmSlaEscalation.sla_instance_id == sid).count() >= 2


def test_sla_status_lookup():
    db = setup_db()
    svc = SlaService(db)
    db.add(WmRbacUserRole(user_id=1, role_id=1))
    db.commit()
    svc.create_rule(
        SlaRuleCreateRequest(
            module="APPROVAL",
            condition={},
            response_time=30,
            resolution_time=60,
            unit="minutes",
            escalation_config={"levels": [{"user_id": 1}], "notify": ["in_app"]},
        )
    )
    svc.start_sla(SlaStartRequest(module="APPROVAL", entity_type="INVOICE", entity_id=9001, context={}))
    status = svc.get_status("INVOICE", 9001)
    assert len(status) == 1
