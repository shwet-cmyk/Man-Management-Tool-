from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.modules.login.router import router as login_router
from app.modules.rbac.router import router as rbac_router
from app.modules.users.router import router as users_router
from app.modules.org.router import router as org_router
from app.modules.governance.router import router as governance_router
from app.modules.interconnect.router import router as interconnect_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.analytics_engine.router import router as analytics_router
from app.modules.reporting_engine.router import router as reporting_router
from app.modules.projects.router import router as projects_router
from app.modules.status_engine.router import router as status_engine_router
from app.modules.tickets.router import router as tickets_router
from app.modules.tasks.router import router as tasks_router
from app.modules.approval.router import router as approval_router
from app.modules.automation.router import router as automation_router
from app.modules.calendar_intelligence.router import router as calendar_router
from app.modules.task_master.router import router as task_master_router
from app.modules.governance_dashboard.router import router as governance_dashboard_router
from app.modules.gamification.router import router as gamification_router
from app.modules.collaboration.router import router as collaboration_router
from app.modules.notification_engine.router import router as notification_router
from app.modules.system_audit.router import router as system_audit_router

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url=settings.docs_url,
    openapi_url=settings.openapi_url,
    redoc_url=settings.redoc_url,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}


app.include_router(login_router, prefix=settings.api_v1_prefix)
app.include_router(rbac_router, prefix=settings.api_v1_prefix)
app.include_router(users_router, prefix=settings.api_v1_prefix)
app.include_router(org_router, prefix=settings.api_v1_prefix)
app.include_router(governance_router, prefix=settings.api_v1_prefix)

app.include_router(interconnect_router, prefix=settings.api_v1_prefix)
app.include_router(dashboard_router, prefix=settings.api_v1_prefix)
app.include_router(analytics_router, prefix=settings.api_v1_prefix)
app.include_router(reporting_router, prefix=settings.api_v1_prefix)
app.include_router(projects_router, prefix=settings.api_v1_prefix)
app.include_router(status_engine_router, prefix=settings.api_v1_prefix)
app.include_router(tickets_router, prefix=settings.api_v1_prefix)
app.include_router(tasks_router, prefix=settings.api_v1_prefix)
app.include_router(approval_router, prefix=settings.api_v1_prefix)
app.include_router(automation_router, prefix=settings.api_v1_prefix)
app.include_router(calendar_router, prefix=settings.api_v1_prefix)
app.include_router(task_master_router, prefix=settings.api_v1_prefix)
app.include_router(governance_dashboard_router, prefix=settings.api_v1_prefix)
app.include_router(gamification_router, prefix=settings.api_v1_prefix)
app.include_router(collaboration_router, prefix=settings.api_v1_prefix)
app.include_router(notification_router, prefix=settings.api_v1_prefix)
app.include_router(system_audit_router, prefix=settings.api_v1_prefix)
