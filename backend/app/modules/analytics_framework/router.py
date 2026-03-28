from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.analytics_framework.schemas import DrilldownRequest, TrendQueryRequest, WidgetQueryRequest, AnalyticsFilter
from app.modules.analytics_framework.service import DashboardAggregationService

router = APIRouter(prefix="/wm/analytics-framework", tags=["Analytics Framework"])


@router.get("/catalog")
def catalog(db: Session = Depends(get_db)):
    return DashboardAggregationService(db).metric_catalog()


@router.post("/summary-cards")
def summary_cards(filters: AnalyticsFilter, db: Session = Depends(get_db)):
    return DashboardAggregationService(db).summary_cards(filters)


@router.post("/widget-dataset")
def widget_dataset(payload: WidgetQueryRequest, db: Session = Depends(get_db)):
    return DashboardAggregationService(db).widget_dataset(payload)


@router.post("/trend")
def trend_dataset(payload: TrendQueryRequest, db: Session = Depends(get_db)):
    return DashboardAggregationService(db).trend_dataset(payload)


@router.post("/leaderboard")
def leaderboard(payload: WidgetQueryRequest, db: Session = Depends(get_db)):
    group = payload.group_by[0] if payload.group_by else "employee"
    return DashboardAggregationService(db).leaderboard(payload.metric_code, group, payload.filters, payload.top_n)


@router.post("/matrix")
def matrix(payload: WidgetQueryRequest, db: Session = Depends(get_db)):
    row_dim = payload.group_by[0] if payload.group_by else "employee"
    col_dim = payload.group_by[1] if len(payload.group_by) > 1 else "client"
    return DashboardAggregationService(db).matrix(payload.metric_code, row_dim, col_dim, payload.filters, payload.top_n)


@router.post("/comparison")
def comparison(metric_code: str, left_filters: AnalyticsFilter, right_filters: AnalyticsFilter, db: Session = Depends(get_db)):
    return DashboardAggregationService(db).comparison(metric_code, left_filters, right_filters)


@router.post("/drilldown")
def drilldown(payload: DrilldownRequest, db: Session = Depends(get_db)):
    return DashboardAggregationService(db).drilldown(payload)
