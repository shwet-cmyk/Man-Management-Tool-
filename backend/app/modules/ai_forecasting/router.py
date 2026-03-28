from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.ai_forecasting.schemas import SalesHistoryIngestRequest, TargetGenerateRequest
from app.modules.ai_forecasting.service import AiForecastingService

router = APIRouter(prefix="/ai", tags=["Work Management - AI Forecasting"])


@router.post("/sales-history")
def ingest_sales(payload: SalesHistoryIngestRequest, db: Session = Depends(get_db)):
    return AiForecastingService(db).ingest_sales_history(payload)


@router.get("/forecast")
def get_forecast(type: str = Query("product"), period: str = Query("monthly"), entity_id: int | None = Query(None), db: Session = Depends(get_db)):
    return AiForecastingService(db).get_forecast(type, period, entity_id)


@router.get("/customer/{customer_id}/prediction")
def get_customer_prediction(customer_id: int, db: Session = Depends(get_db)):
    return AiForecastingService(db).get_customer_prediction(customer_id)


@router.post("/targets/generate")
def generate_targets(payload: TargetGenerateRequest, db: Session = Depends(get_db)):
    return AiForecastingService(db).generate_targets(payload)
