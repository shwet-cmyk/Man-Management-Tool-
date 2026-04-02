from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.ai.schemas import ApplyRecommendationRequest, GenerateInsightRequest
from app.modules.ai.service import AiService

router = APIRouter(prefix="/wm/ai", tags=["Work Management - AI Intelligence"])


@router.post("/insights")
def generate_insight(payload: GenerateInsightRequest, db: Session = Depends(get_db)):
    return AiService(db).generate_insight(payload)


@router.get("/task/{task_id}")
def get_task_insight(task_id: int, db: Session = Depends(get_db)):
    return AiService(db).get_task_insight(task_id)


@router.post("/apply")
def apply_recommendation(payload: ApplyRecommendationRequest, db: Session = Depends(get_db)):
    return AiService(db).apply_recommendation(payload.rec_id, payload.applied_by)
