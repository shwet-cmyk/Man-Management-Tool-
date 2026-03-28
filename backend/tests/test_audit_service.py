from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.modules.audit.schemas import AuditLogCreateRequest
from app.modules.audit.service import AuditService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_audit_log_creates_changes_and_versions():
    db = setup_db()
    svc = AuditService(db)

    out1 = svc.log_event(
        AuditLogCreateRequest(
            entity_type="INVOICE",
            entity_id=101,
            action="CREATE",
            performed_by=9001,
            old_data={},
            new_data={"amount": 10000, "gst": 18},
            ip_address="10.1.1.1",
            device_info="Chrome",
        )
    )
    assert out1["field_change_count"] == 2
    assert out1["version_no"] == 1

    out2 = svc.log_event(
        AuditLogCreateRequest(
            entity_type="INVOICE",
            entity_id=101,
            action="UPDATE",
            performed_by=9002,
            old_data={"amount": 10000, "gst": 18},
            new_data={"amount": 12500, "gst": 12},
            source="API",
        )
    )
    assert out2["field_change_count"] == 2
    assert out2["version_no"] == 2

    logs = svc.get_audit_logs("INVOICE", 101)
    assert len(logs) == 2
    assert logs[0]["action"] == "UPDATE"

    changes = svc.get_field_changes(out2["audit_log_id"])
    fields = {x["field_name"] for x in changes}
    assert {"amount", "gst"} <= fields

    snapshot = svc.get_version_snapshot("INVOICE", 101, 2)
    assert snapshot["snapshot"]["amount"] == 12500
