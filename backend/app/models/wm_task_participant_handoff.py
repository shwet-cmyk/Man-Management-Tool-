from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, ForeignKey, String

from app.database.session import Base


class WmTaskParticipantHandoff(Base):
    __tablename__ = "wm_task_participant_handoff"

    handoff_id = Column(BIGINT, primary_key=True, autoincrement=True)
    submission_id = Column(BIGINT, ForeignKey("wm_task_participant_submission.submission_id"), nullable=False)
    task_id = Column(BIGINT, ForeignKey("wm_task.task_id"), nullable=False)
    from_participant_id = Column(BIGINT, ForeignKey("wm_task_participant.task_participant_id"), nullable=False)
    to_participant_id = Column(BIGINT, ForeignKey("wm_task_participant.task_participant_id"), nullable=False)
    handoff_status = Column(String(30), nullable=False)
    unlocked_on = Column(DateTime, nullable=True)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
