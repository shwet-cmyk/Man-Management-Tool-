from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.modules.ai_forecasting.schemas import SalesHistoryIngestRequest
from app.modules.ai_forecasting.service import AiForecastingService
from app.modules.analytics.service import AnalyticsService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_analytics_query_report_dashboard():
    db = setup_db()
    ai = AiForecastingService(db)
    analytics = AnalyticsService(db)

    ai.ingest_sales_history(SalesHistoryIngestRequest(sales_date=date(2025, 1, 1), product_id=1, customer_id=1, quantity=5, revenue=1000, branch_id=1))
    ai.ingest_sales_history(SalesHistoryIngestRequest(sales_date=date(2025, 2, 1), product_id=1, customer_id=2, quantity=6, revenue=1200, branch_id=1))

    query = analytics.query_analytics(dimensions=["product", "branch"], metrics=["revenue", "profit"], filters={})
    assert query["count"] >= 1

    report = analytics.generate_report("Revenue by Product", dimensions=["product"], metrics=["revenue"], filters={})
    assert report["report_name"] == "Revenue by Product"
    assert report["row_count"] >= 1

    dash = analytics.get_dashboard_summary()
    assert "kpis" in dash
    assert dash["kpis"]["revenue"] >= 0
