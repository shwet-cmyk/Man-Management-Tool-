from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database.session import Base, engine
from app.modules.ai.router import router as ai_router
from app.modules.ai_forecasting.router import router as ai_forecasting_router
from app.modules.analytics.router import router as analytics_router
from app.modules.audit.router import router as audit_router
from app.modules.approval.router import router as approval_router
from app.modules.attendance.router import router as attendance_router
from app.modules.billing.router import router as billing_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.departments.router import router as departments_router
from app.modules.crm.router import router as crm_router
from app.modules.documents.router import router as documents_router
from app.modules.employees.router import router as employees_router
from app.modules.expense_claims.router import router as expense_claims_router
from app.modules.integration_hub.router import router as integration_hub_router
from app.modules.master_sync.router import router as employee_sync_router
from app.modules.reports.router import router as reports_router
from app.modules.rules.router import router as rules_router
from app.modules.sla.router import router as sla_router
from app.modules.sla_enforcement.router import router as sla_enforcement_router
from app.modules.platform.router import router as platform_router
from app.modules.rbac.router import router as rbac_router
from app.modules.tasks.router import router as tasks_router
from app.modules.dependency_enforcement.router import router as dependency_enforcement_router
from app.modules.timesheets.router import router as timesheets_router
from app.modules.tickets.router import router as tickets_router
from app.modules.tez_audit.router import router as tez_audit_router
from app.modules.workflows.router import router as workflows_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok", "environment": settings.app_env}


app.include_router(departments_router, prefix="/api/v1")
app.include_router(employees_router, prefix="/api/v1")
app.include_router(attendance_router, prefix="/api/v1")
app.include_router(employee_sync_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(ai_forecasting_router, prefix="/api")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(ai_forecasting_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api")
app.include_router(crm_router, prefix="/api")
app.include_router(dependency_enforcement_router, prefix="/api")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(crm_router, prefix="/api/v1")
app.include_router(dependency_enforcement_router, prefix="/api/v1")
app.include_router(timesheets_router, prefix="/api")
app.include_router(timesheets_router, prefix="/api/v1")
app.include_router(expense_claims_router, prefix="/api")
app.include_router(integration_hub_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(expense_claims_router, prefix="/api/v1")
app.include_router(integration_hub_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(billing_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(rbac_router, prefix="/api")
app.include_router(approval_router, prefix="/api")
app.include_router(rules_router, prefix="/api")
app.include_router(workflows_router, prefix="/api")
app.include_router(sla_router, prefix="/api")
app.include_router(sla_enforcement_router, prefix="/api")
app.include_router(platform_router, prefix="/api")
app.include_router(tickets_router, prefix="/api")
app.include_router(tez_audit_router, prefix="/api")
app.include_router(billing_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(rbac_router, prefix="/api/v1")
app.include_router(approval_router, prefix="/api/v1")
app.include_router(rules_router, prefix="/api/v1")
app.include_router(workflows_router, prefix="/api/v1")
app.include_router(sla_router, prefix="/api/v1")
app.include_router(sla_enforcement_router, prefix="/api/v1")
app.include_router(platform_router, prefix="/api/v1")
app.include_router(tickets_router, prefix="/api/v1")
app.include_router(tez_audit_router, prefix="/api/v1")
