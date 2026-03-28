from sqlalchemy import BIGINT, Column, String

from app.database.session import Base


class WmWorkflowEdge(Base):
    __tablename__ = "wm_workflow_edge"

    edge_id = Column(BIGINT, primary_key=True, autoincrement=True)
    workflow_id = Column(BIGINT, nullable=False, index=True)
    from_node_id = Column(BIGINT, nullable=False, index=True)
    to_node_id = Column(BIGINT, nullable=False, index=True)
    edge_condition = Column(String(50), nullable=True)
