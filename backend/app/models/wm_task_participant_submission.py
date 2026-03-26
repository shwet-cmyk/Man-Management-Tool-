from datetime import datetime

from sqlalchemy import BIGINT, DECIMAL, Boolean, Column, DateTime, ForeignKey, String, Text

from app.database.session import Base


class WmTaskParticipantSubmission(Base):
    __tablename__ = "wm_task_participant_submission"

    submission_id = Column(BIGINT, primary_key=True, autoincrement=True)
    job_id = Column(BIGINT, nullable=False)
    task_id = Column(BIGINT, ForeignKey("wm_task.task_id"), nullable=False, index=True)
    from_participant_id = Column(BIGINT, ForeignKey("wm_task_participant.task_participant_id"), nullable=False)
    to_participant_id = Column(BIGINT, ForeignKey("wm_task_participant.task_participant_id"), nullable=True)
    handoff_type = Column(String(30), nullable=False)
    submission_status = Column(String(30), nullable=False)
    submission_note = Column(Text, nullable=True)
    deliverable_link = Column(String(1000), nullable=True)
    attachment_ref = Column(String(1000), nullable=True)
    completion_pct = Column(DECIMAL(5, 2), nullable=True)
    acceptance_required = Column(Boolean, nullable=False, default=False)
    submitted_by = Column(BIGINT, nullable=False)
    submitted_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    accepted_on = Column(DateTime, nullable=True)
    accepted_by = Column(BIGINT, nullable=True)
    rejected_on = Column(DateTime, nullable=True)
    rejected_by = Column(BIGINT, nullable=True)
    decision_note = Column(Text, nullable=True)
    override_flag = Column(Boolean, nullable=False, default=False)
    override_reason = Column(String(1000), nullable=True)
    remarks = Column(String(1000), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
