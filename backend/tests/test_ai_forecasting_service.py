from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.modules.ai_forecasting.schemas import SalesHistoryIngestRequest, TargetGenerateRequest
from app.modules.ai_forecasting.service import AiForecastingService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_forecast_with_history_and_targets():
    db = setup_db()
    svc = AiForecastingService(db)

    for m in range(1, 8):
        svc.ingest_sales_history(
            SalesHistoryIngestRequest(
                sales_date=date(2025, m, 1),
                product_id=100,
                customer_id=200 + m,
                quantity=10 + m,
                revenue=10000 + (m * 1500),
                branch_id=1,
            )
        )

    fc = svc.get_forecast("product", "monthly", entity_id=100)
    assert fc["model"] == "LINEAR_TREND"
    assert len(fc["forecast"]) == 6

    targets = svc.generate_targets(TargetGenerateRequest(period="monthly", entity_type="product"))
    assert len(targets["targets"]) == 2


def test_customer_prediction_fallback_and_computed():
    db = setup_db()
    svc = AiForecastingService(db)

    empty = svc.get_customer_prediction(999)
    assert empty["churn_score"] >= 0.7

    svc.ingest_sales_history(
        SalesHistoryIngestRequest(
            sales_date=date.today(),
            product_id=1,
            customer_id=500,
            quantity=2,
            revenue=1200,
            branch_id=1,
        )
    )
    pred = svc.get_customer_prediction(500)
    assert pred["lifetime_value"] >= 1200
    assert pred["repeat_probability"] > 0
