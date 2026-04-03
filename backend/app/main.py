from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.rate_limit import RateLimitMiddleware
from app.modules.login.router import auth_router
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
from app.modules.jobs.router import router as jobs_router
from app.modules.sla.router import router as sla_router
from app.modules.timesheet.router import router as timesheet_router
from app.modules.billing.router import router as billing_router
from app.modules.approval.router import router as approval_router
from app.modules.automation.router import router as automation_router
from app.modules.calendar_intelligence.router import router as calendar_router
from app.modules.task_master.router import router as task_master_router
from app.modules.governance_dashboard.router import router as governance_dashboard_router
from app.modules.gamification.router import router as gamification_router
from app.modules.collaboration.router import router as collaboration_router
from app.modules.notification_engine.router import router as notification_router
from app.modules.system_audit.router import alias_router as audit_alias_router
from app.modules.system_audit.router import router as system_audit_router
from app.modules.goals_kpi.router import router as goals_kpi_router
from app.modules.portfolio.router import router as portfolio_router
from app.modules.workflow_templates.router import router as workflow_templates_router
from app.modules.intake_forms.router import router as intake_forms_router
from app.modules.client_portal.router import router as client_portal_router
from app.modules.knowledge_base.router import router as knowledge_base_router
from app.modules.mobile_app.router import router as mobile_app_router
from app.modules.execution_governance.router import router as execution_governance_router
from app.modules.help.router import router as help_router
from app.modules.ux_analytics.router import router as ux_analytics_router
from app.modules.devlogs.router import router as devlogs_router
from app.modules.system_settings.router import router as system_settings_router
from app.chatbot.router import router as chatbot_router
from app.productivity.api.productivity_router import router as productivity_router
from app.product_intelligence.api.product_intelligence_router import router as product_intelligence_router
from app.platform_hardening.router import router as platform_hardening_router
from app.workers.scheduler import run_periodic_jobs

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
app.add_middleware(RateLimitMiddleware, limit=200, window_seconds=60)

_scheduler_stop_event = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}


@app.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ready", "env": settings.app_env}


@app.on_event("startup")
async def startup_event():
    global _scheduler_stop_event
    import asyncio

    _scheduler_stop_event = asyncio.Event()
    asyncio.create_task(run_periodic_jobs(_scheduler_stop_event))


@app.on_event("shutdown")
async def shutdown_event():
    if _scheduler_stop_event:
        _scheduler_stop_event.set()


app.include_router(login_router, prefix=settings.api_v1_prefix)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
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
app.include_router(jobs_router, prefix=settings.api_v1_prefix)
app.include_router(sla_router, prefix=settings.api_v1_prefix)
app.include_router(timesheet_router, prefix=settings.api_v1_prefix)
app.include_router(billing_router, prefix=settings.api_v1_prefix)
app.include_router(approval_router, prefix=settings.api_v1_prefix)
app.include_router(automation_router, prefix=settings.api_v1_prefix)
app.include_router(calendar_router, prefix=settings.api_v1_prefix)
app.include_router(task_master_router, prefix=settings.api_v1_prefix)
app.include_router(governance_dashboard_router, prefix=settings.api_v1_prefix)
app.include_router(gamification_router, prefix=settings.api_v1_prefix)
app.include_router(collaboration_router, prefix=settings.api_v1_prefix)
app.include_router(notification_router, prefix=settings.api_v1_prefix)
app.include_router(system_audit_router, prefix=settings.api_v1_prefix)
app.include_router(audit_alias_router, prefix=settings.api_v1_prefix)
app.include_router(goals_kpi_router, prefix=settings.api_v1_prefix)
app.include_router(portfolio_router, prefix=settings.api_v1_prefix)
app.include_router(workflow_templates_router, prefix=settings.api_v1_prefix)
app.include_router(intake_forms_router, prefix=settings.api_v1_prefix)
app.include_router(client_portal_router, prefix=settings.api_v1_prefix)
app.include_router(knowledge_base_router, prefix=settings.api_v1_prefix)
app.include_router(mobile_app_router, prefix=settings.api_v1_prefix)

app.include_router(execution_governance_router, prefix=settings.api_v1_prefix)
app.include_router(help_router, prefix=settings.api_v1_prefix)
app.include_router(ux_analytics_router, prefix=settings.api_v1_prefix)
app.include_router(devlogs_router, prefix=settings.api_v1_prefix)
app.include_router(system_settings_router, prefix=settings.api_v1_prefix)
app.include_router(chatbot_router, prefix=settings.api_v1_prefix)
app.include_router(productivity_router, prefix=settings.api_v1_prefix)
app.include_router(product_intelligence_router, prefix=settings.api_v1_prefix)
app.include_router(platform_hardening_router, prefix=settings.api_v1_prefix)
