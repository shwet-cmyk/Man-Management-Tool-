from sqlalchemy import BIGINT, Column, String, Text

from app.database.session import Base


class WmWorkflowNode(Base):
    __tablename__ = "wm_workflow_node"

    node_id = Column(BIGINT, primary_key=True, autoincrement=True)
    workflow_id = Column(BIGINT, nullable=False, index=True)
    node_type = Column(String(30), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    sequence_no = Column(BIGINT, nullable=False, default=1)
    config_json = Column(Text, nullable=True)
