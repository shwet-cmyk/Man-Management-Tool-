from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.modules.rules.schemas import RuleCreateRequest, RuleEvaluateRequest
from app.modules.rules.service import RuleService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_rule_priority_and_evaluation():
    db = setup_db()
    svc = RuleService(db)

    svc.create_rule(
        RuleCreateRequest(
            module="BILLING",
            condition={"field": "amount", "operator": ">", "value": 100000},
            action={"type": "APPROVAL", "level": "DIRECTOR"},
            priority=10,
        )
    )
    svc.create_rule(
        RuleCreateRequest(
            module="BILLING",
            condition={"field": "amount", "operator": ">", "value": 10000},
            action={"type": "APPROVAL", "level": "MANAGER"},
            priority=20,
        )
    )

    out = svc.evaluate(RuleEvaluateRequest(module="BILLING", context={"amount": 150000}))
    assert out["results"][0]["matched"] is True
    assert out["results"][0]["action"]["level"] == "DIRECTOR"
    assert out["results"][1]["matched"] is True
