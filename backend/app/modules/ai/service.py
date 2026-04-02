from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.wm_ai_prediction import WmAiPrediction
from app.models.wm_ai_recommendation import WmAiRecommendation
from app.models.wm_expense_claim import WmExpenseClaim
from app.models.wm_task import WmTask
from app.models.wm_timesheet import WmTimesheet
from app.modules.ai.schemas import GenerateInsightRequest


class AiService:
    def __init__(self, db: Session):
        self.db = db

    def generate_insight(self, payload: GenerateInsightRequest):
        if payload.entity_type == "TASK":
            return self._task_insight(payload.entity_id)
        return self._job_insight(payload.entity_id)

    def get_task_insight(self, task_id: int):
        return self._task_insight(task_id)

    def apply_recommendation(self, rec_id: int, applied_by: int):
        rec = self.db.query(WmAiRecommendation).filter(WmAiRecommendation.rec_id == rec_id).first()
        if not rec:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        rec.is_applied = True
        rec.recommendation_text = f"{rec.recommendation_text} | Applied by {applied_by} on {datetime.utcnow().isoformat()}"
        self.db.commit()
        return {"rec_id": rec_id, "is_applied": True}

    def _task_insight(self, task_id: int):
        task = self.db.query(WmTask).filter(WmTask.task_id == task_id, WmTask.is_active.is_(True)).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        approved_hours = Decimal(
            str(
                self.db.query(func.coalesce(func.sum(WmTimesheet.hours), 0)).filter(
                    WmTimesheet.task_id == task_id,
                    WmTimesheet.approval_status == "Approved",
                    WmTimesheet.is_active.is_(True),
                ).scalar()
            )
        )
        estimated_hours = Decimal(str(task.estimated_hours or 0))
        if estimated_hours <= 0:
            estimated_hours = Decimal("1")

        delay_probability = min(Decimal("95"), max(Decimal("5"), (approved_hours / estimated_hours) * Decimal("100")))
        cost_predicted = approved_hours * Decimal("250")
        completion_probability = max(Decimal("10"), Decimal("100") - delay_probability)

        rows = [
            WmAiPrediction(entity_type="TASK", entity_id=task_id, prediction_type="DELAY", predicted_value=approved_hours, probability=delay_probability),
            WmAiPrediction(entity_type="TASK", entity_id=task_id, prediction_type="COST", predicted_value=cost_predicted, probability=Decimal("80")),
            WmAiPrediction(entity_type="TASK", entity_id=task_id, prediction_type="COMPLETION", predicted_value=completion_probability, probability=Decimal("75")),
        ]
        for row in rows:
            self.db.add(row)

        recommendations = []
        if delay_probability >= Decimal("70"):
            recommendations.append(
                WmAiRecommendation(
                    entity_id=task_id,
                    recommendation_type="AUTO_ESCALATE",
                    recommendation_text="High delay risk detected. Escalate to manager and add backup reviewer.",
                    priority=1,
                )
            )
        if approved_hours > estimated_hours:
            recommendations.append(
                WmAiRecommendation(
                    entity_id=task_id,
                    recommendation_type="COST_CORRECTION",
                    recommendation_text="Actual effort exceeded estimate. Rebaseline budget and revise due date.",
                    priority=2,
                )
            )
        if not recommendations:
            recommendations.append(
                WmAiRecommendation(
                    entity_id=task_id,
                    recommendation_type="MONITOR",
                    recommendation_text="Task is stable. Continue monitoring cadence.",
                    priority=3,
                )
            )
        for rec in recommendations:
            self.db.add(rec)

        self.db.commit()
        return {
            "entity_type": "TASK",
            "entity_id": task_id,
            "predictions": [
                {
                    "prediction_type": x.prediction_type,
                    "predicted_value": x.predicted_value,
                    "probability": x.probability,
                }
                for x in rows
            ],
            "recommendations": [
                {
                    "rec_id": x.rec_id,
                    "recommendation_type": x.recommendation_type,
                    "recommendation_text": x.recommendation_text,
                    "priority": x.priority,
                }
                for x in recommendations
            ],
        }

    def _job_insight(self, job_id: int):
        total_hours = Decimal(
            str(
                self.db.query(func.coalesce(func.sum(WmTimesheet.hours), 0)).filter(
                    WmTimesheet.job_id == job_id,
                    WmTimesheet.approval_status == "Approved",
                    WmTimesheet.is_active.is_(True),
                ).scalar()
            )
        )
        total_expense = Decimal(
            str(
                self.db.query(func.coalesce(func.sum(WmExpenseClaim.total_amount), 0)).filter(
                    WmExpenseClaim.job_id == job_id,
                    WmExpenseClaim.approval_status == "Approved",
                    WmExpenseClaim.is_active.is_(True),
                ).scalar()
            )
        )
        predicted_cost = total_expense + (total_hours * Decimal("250"))
        row = WmAiPrediction(entity_type="JOB", entity_id=job_id, prediction_type="COST", predicted_value=predicted_cost, probability=Decimal("82"))
        self.db.add(row)
        rec = WmAiRecommendation(
            entity_id=job_id,
            recommendation_type="RESOURCE_REALLOCATION",
            recommendation_text="Shift senior reviewer capacity to improve completion probability.",
            priority=2,
        )
        self.db.add(rec)
        self.db.commit()
        return {
            "entity_type": "JOB",
            "entity_id": job_id,
            "predictions": [{"prediction_type": "COST", "predicted_value": predicted_cost, "probability": Decimal("82")}],
            "recommendations": [{"rec_id": rec.rec_id, "recommendation_type": rec.recommendation_type, "recommendation_text": rec.recommendation_text, "priority": rec.priority}],
        }
