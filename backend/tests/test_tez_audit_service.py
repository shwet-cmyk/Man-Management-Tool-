from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.modules.tez_audit.schemas import TezAuditLogRequest
from app.modules.tez_audit.service import TezAuditService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_audit_log_masks_sensitive_and_reads_back():
    db = setup_db()
    svc = TezAuditService(db)

    logged = svc.log_event(
        TezAuditLogRequest(
            entity_type="TASK",
            entity_id="uuid-1",
            action="UPDATE",
            user_id="user-1",
            old_data={"password": "abc", "amount": 1},
            new_data={"password": "xyz", "amount": 2},
        )
    )

    assert logged["status"] == "logged"
    rows = svc.get_entity_logs("TASK", "uuid-1")
    assert len(rows) == 1
    assert rows[0]["action"] == "UPDATE"
