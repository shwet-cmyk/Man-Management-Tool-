from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, Integer, String

from app.database.session import Base


class WmManManagementSetting(Base):
    __tablename__ = "wm_man_management_setting"

    setting_id = Column(BIGINT, primary_key=True, autoincrement=True)
    company_id = Column(BIGINT, nullable=True)
    timesheet_mandatory_for_completion = Column(Boolean, nullable=False, default=True)
    mandatory_task_completion_for_billing = Column(Boolean, nullable=False, default=True)
    manager_approval_mandatory_for_timesheet = Column(Boolean, nullable=False, default=False)
    job_completion_approval_required = Column(Boolean, nullable=False, default=False)
    max_attachment_size_mb = Column(Integer, nullable=False, default=10)
    allowed_attachment_types = Column(String(200), nullable=False, default="pdf,jpg,jpeg,png")
    overtime_allowed = Column(Boolean, nullable=False, default=True)
    multiple_timesheets_per_day = Column(Boolean, nullable=False, default=True)
    billable_amount_editable_after_completion = Column(Boolean, nullable=False, default=False)
    delete_allowed_after_timesheet_entry = Column(Boolean, nullable=False, default=False)
    expense_approval_required = Column(Boolean, nullable=False, default=False)
    reimbursement_approval_required = Column(Boolean, nullable=False, default=False)
    created_by = Column(BIGINT, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_by = Column(BIGINT, nullable=True)
    updated_at = Column(DateTime, nullable=True)
