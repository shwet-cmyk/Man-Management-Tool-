from datetime import datetime

from sqlalchemy import BIGINT, DECIMAL, Boolean, Column, Date, DateTime, String

from app.database.session import Base


class WmResourceAllocation(Base):
    __tablename__ = "wm_resource_allocation"

    resource_allocation_id = Column(BIGINT, primary_key=True, autoincrement=True)
    employee_id = Column(BIGINT, nullable=False, index=True)
    employee_name = Column(String(255), nullable=False)
    manager_id = Column(BIGINT, nullable=True)
    department_id = Column(BIGINT, nullable=True)
    project_id = Column(BIGINT, nullable=True)
    launch_id = Column(BIGINT, nullable=True)
    linked_entity_type = Column(String(30), nullable=False)
    linked_entity_id = Column(BIGINT, nullable=False)
    allocation_date = Column(Date, nullable=False)
    planned_hours = Column(DECIMAL(10, 2), nullable=False, default=0)
    actual_hours = Column(DECIMAL(10, 2), nullable=False, default=0)
    variance_hours = Column(DECIMAL(10, 2), nullable=False, default=0)
    utilization_percent = Column(DECIMAL(5, 2), nullable=False, default=0)
    overload_flag = Column(Boolean, nullable=False, default=False)
    active_flag = Column(Boolean, nullable=False, default=True)
    created_by = Column(BIGINT, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
