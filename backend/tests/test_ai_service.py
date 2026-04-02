from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.models.wm_ai_prediction import WmAiPrediction
from app.models.wm_ai_recommendation import WmAiRecommendation
from app.models.wm_expense_claim import WmExpenseClaim
from app.models.wm_task import WmTask
from app.models.wm_timesheet import WmTimesheet
from app.modules.ai.schemas import GenerateInsightRequest
from app.modules.ai.service import AiService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def seed(db):
    now = datetime.utcnow()
    db.add(
        WmTask(
            task_id=6001,
            task_no="TSK-1",
            company_id=1,
            job_id=5001,
            title="AI Task",
            task_type="Task",
            priority_code="Medium",
            status_code="In Progress",
            primary_owner_emp_id=101,
            manager_emp_id=999,
            billable_flag=True,
            estimated_hours=Decimal("5"),
            planned_start=now - timedelta(days=3),
            due_at=now + timedelta(days=2),
            created_by=1,
            source_type="MANUAL",
        )
    )
    db.add(
        WmTimesheet(
            timesheet_id=8001,
            company_id=1,
            job_id=5001,
            task_id=6001,
            emp_id=101,
            work_date=now.date(),
            hours=Decimal("7"),
            billable_hours=Decimal("7"),
            overtime_hours=Decimal("0"),
            approval_status="Approved",
            created_by=1,
        )
    )
    db.add(
        WmExpenseClaim(
            claim_id=9001,
            claim_no="EXP-1",
            claim_type="REIMBURSEMENT",
            expense_type="Travel",
            company_id=1,
            emp_id=101,
            job_id=5001,
            expense_date=now.date(),
            amount=Decimal("50"),
            tax_amount=Decimal("0"),
            total_amount=Decimal("50"),
            recoverable_flag=True,
            approval_status="Approved",
            created_by=1,
        )
    )
    db.commit()


def test_ai_predictions_and_apply_recommendation():
    db = setup_db()
    seed(db)
    svc = AiService(db)

    task_out = svc.generate_insight(GenerateInsightRequest(entity_type="TASK", entity_id=6001))
    assert task_out["entity_type"] == "TASK"
    assert db.query(WmAiPrediction).count() >= 3
    assert db.query(WmAiRecommendation).count() >= 1

    job_out = svc.generate_insight(GenerateInsightRequest(entity_type="JOB", entity_id=5001))
    assert job_out["entity_type"] == "JOB"

    rec_id = db.query(WmAiRecommendation).first().rec_id
    apply_out = svc.apply_recommendation(rec_id=rec_id, applied_by=77)
    assert apply_out["is_applied"] is True
