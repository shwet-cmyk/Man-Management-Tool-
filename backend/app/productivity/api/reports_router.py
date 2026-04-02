from __future__ import annotations
from datetime import date
from fastapi import APIRouter, Query
from app.productivity.api._deps import breach_service, daily_summary_service, screenshot_service, underproductive_service
from app.productivity.schemas.breach_schema import PolicyBreachResponse
from app.productivity.schemas.summary_schema import DailySummaryResponse, TeamSummaryRecord

router = APIRouter(prefix='/productivity', tags=['Productivity Reports'])

@router.get('/summary/daily', response_model=DailySummaryResponse)
async def daily_summary(date_value: date = Query(alias='date'), user_id: int = Query(...)):
    rows = [r for r in await daily_summary_service.list_all() if r['user_id'] == user_id and r['summary_date'] == date_value]
    if rows:
        return DailySummaryResponse(**rows[-1])
    return DailySummaryResponse(summary_date=date_value, user_id=user_id, present_minutes=0, active_minutes=0, productive_minutes=0, neutral_minutes=0, unproductive_minutes=0, idle_minutes=0, locked_minutes=0, hibernate_minutes=0, offline_minutes=0, shutdown_count=0, reboot_count=0, productivity_status='PRODUCTIVE')

@router.get('/team-summary', response_model=list[TeamSummaryRecord])
async def team_summary(date_value: date = Query(alias='date'), manager_id: int = Query(...)):
    rows = await daily_summary_service.list_all()
    return [TeamSummaryRecord(user_id=r['user_id'], employee_name=f'Employee {r["user_id"]}', productive_minutes=r['productive_minutes'], idle_minutes=r['idle_minutes'], status=r['productivity_status']) for r in rows if r['summary_date'] == date_value]

@router.get('/activity-logs')
async def activity_logs(user_id: int | None = None):
    from app.productivity.api._deps import activity_ingestion_service
    rows = await activity_ingestion_service.raw_repo.list_all()
    if user_id:
        rows = [r for r in rows if r['user_id']==user_id]
    return {'success': True, 'records': rows}

@router.get('/policy-breaches', response_model=list[PolicyBreachResponse])
async def policy_breaches():
    rows = await breach_service.list_all()
    return [PolicyBreachResponse(**r) for r in rows]

@router.get('/underproductive-report')
async def underproductive_report(date_value: date = Query(alias='date')):
    rows = [r for r in await daily_summary_service.list_all() if r['summary_date'] == date_value and r['productivity_status'] in {'UNDERPRODUCTIVE','BORDERLINE'}]
    return {'success': True, 'records': rows}

@router.get('/screenshots')
async def screenshots(user_id: int | None = None):
    rows = await screenshot_service.list_all()
    if user_id:
        rows = [r for r in rows if r['user_id'] == user_id]
    return {'success': True, 'records': rows}

@router.get('/dashboard/widgets')
async def dashboard_widgets(scope: str = Query('admin'), date_value: date = Query(alias='date')):
    rows = [r for r in await daily_summary_service.list_all() if r['summary_date'] == date_value]
    return {'success': True, 'widgets': {'underproductive_count': len([r for r in rows if r['productivity_status']=='UNDERPRODUCTIVE']), 'blacklisted_url_attempts': len(await breach_service.list_all()), 'department_productivity_trend': [], 'top_idle_users': sorted([{'user_id': r['user_id'], 'idle_minutes': r['idle_minutes']} for r in rows], key=lambda x: -x['idle_minutes'])[:5]}}
