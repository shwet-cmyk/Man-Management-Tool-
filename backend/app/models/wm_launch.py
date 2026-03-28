from datetime import datetime

from sqlalchemy import BIGINT, DECIMAL, Boolean, Column, Date, DateTime, String

from app.database.session import Base


class WmLaunch(Base):
    __tablename__ = "wm_launch"

    launch_id = Column(BIGINT, primary_key=True, autoincrement=True)
    launch_code = Column(String(50), nullable=False, unique=True, index=True)
    launch_name = Column(String(255), nullable=False)
    product_id = Column(BIGINT, nullable=True)
    product_name = Column(String(255), nullable=True)
    launch_type = Column(String(50), nullable=False)
    launch_owner_id = Column(BIGINT, nullable=False)
    launch_manager_id = Column(BIGINT, nullable=True)
    client_id = Column(BIGINT, nullable=True)
    project_id = Column(BIGINT, nullable=True)
    start_date = Column(Date, nullable=True)
    target_launch_date = Column(Date, nullable=True)
    actual_launch_date = Column(Date, nullable=True)
    launch_status = Column(String(30), nullable=False, default="Planning")
    launch_priority = Column(String(20), nullable=False, default="Medium")
    budget_amount = Column(DECIMAL(14, 2), nullable=True)
    billed_amount_rollup = Column(DECIMAL(14, 2), nullable=False, default=0)
    cost_to_company_rollup = Column(DECIMAL(14, 2), nullable=False, default=0)
    profit_or_loss_rollup = Column(DECIMAL(14, 2), nullable=False, default=0)
    readiness_percent = Column(DECIMAL(5, 2), nullable=False, default=0)
    risk_status = Column(String(30), nullable=False, default="On Track")
    dependency_health = Column(String(30), nullable=False, default="Healthy")
    active_flag = Column(Boolean, nullable=False, default=True)
    created_by = Column(BIGINT, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_by = Column(BIGINT, nullable=True)
    updated_at = Column(DateTime, nullable=True)
