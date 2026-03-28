from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, Date, DateTime, DECIMAL, String, Text

from app.database.session import Base


class WmIntakeRequest(Base):
    __tablename__ = "wm_intake_request"

    intake_request_id = Column(BIGINT, primary_key=True, autoincrement=True)
    request_code = Column(String(50), nullable=False, unique=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    request_type = Column(String(50), nullable=False)
    source_type = Column(String(30), nullable=False, default="manual")
    form_template = Column(String(80), nullable=False, default="Project Request")
    client_id = Column(BIGINT, nullable=True)
    client_name = Column(String(255), nullable=True)
    company_id = Column(BIGINT, nullable=False)
    branch_id = Column(BIGINT, nullable=True)
    department_id = Column(BIGINT, nullable=True)
    category = Column(String(80), nullable=True)
    product_service = Column(String(120), nullable=True)
    urgency = Column(String(20), nullable=False, default="Medium")
    expected_due_date = Column(Date, nullable=True)
    estimated_value = Column(DECIMAL(14, 2), nullable=True)
    requester_id = Column(BIGINT, nullable=False)
    requester_name = Column(String(255), nullable=False)
    approval_required = Column(Boolean, nullable=False, default=False)
    custom_fields_json = Column(Text, nullable=True)
    status = Column(String(40), nullable=False, default="New")
    converted_entity_type = Column(String(30), nullable=True)
    converted_entity_id = Column(BIGINT, nullable=True)
    triage_owner_id = Column(BIGINT, nullable=True)
    triage_owner_name = Column(String(255), nullable=True)
    active_flag = Column(Boolean, nullable=False, default=True)
    created_by = Column(BIGINT, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_by = Column(BIGINT, nullable=True)
    updated_at = Column(DateTime, nullable=True)
