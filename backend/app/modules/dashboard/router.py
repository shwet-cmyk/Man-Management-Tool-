from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.dashboard.schemas import (
    DashboardCreateRequest,
    DashboardCreateResponse,
    DashboardReadResponse,
    WidgetAddRequest,
    WidgetAddResponse,
    WidgetDataRequest,
    WidgetDataResponse,
)
from app.modules.dashboard.service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.post("", response_model=DashboardCreateResponse)
def create_dashboard(payload: DashboardCreateRequest, db: Session = Depends(get_db)):
    return DashboardService(db).create_dashboard(payload)


@router.post("/widget", response_model=WidgetAddResponse)
def add_widget(payload: WidgetAddRequest, db: Session = Depends(get_db)):
    return DashboardService(db).add_widget(payload)


@router.get("/{dashboard_id}", response_model=DashboardReadResponse)
def get_dashboard(dashboard_id: int, db: Session = Depends(get_db)):
    return DashboardService(db).get_dashboard(dashboard_id)


@router.post("/widget/data", response_model=WidgetDataResponse)
def get_widget_data(payload: WidgetDataRequest, db: Session = Depends(get_db)):
    return DashboardService(db).get_widget_data(payload)
