from __future__ import annotations
from fastapi import APIRouter, Query
from app.productivity.api._deps import policy_service
from app.productivity.schemas.policy_schema import ProductivityPolicyResponse, ProductivityPolicyUpsertRequest

router = APIRouter(prefix='/productivity/policy', tags=['Productivity Policy'])

@router.get('/current', response_model=ProductivityPolicyResponse)
async def current_policy(user_id: int = Query(...)):
    policy = await policy_service.current_for_user(user_id)
    return ProductivityPolicyResponse(
        policy_id=policy.get('id', 0),
        policy_name=policy['policy_name'],
        scope_type=policy['scope_type'],
        scope_reference_id=policy.get('scope_reference_id'),
        idle_threshold_minutes=policy['idle_threshold_minutes'],
        productive_target_hours=policy['productive_target_hours'],
        borderline_lower_hours=policy['borderline_lower_hours'],
        underproductive_lower_hours=policy['underproductive_lower_hours'],
        warn_on_blacklisted_url=policy['warn_on_blacklisted_url'],
        block_blacklisted_url=policy['block_blacklisted_url'],
        effective_from=policy['effective_from'],
    )

@router.post('', response_model=ProductivityPolicyResponse)
async def upsert_policy(payload: ProductivityPolicyUpsertRequest):
    row = await policy_service.upsert(payload.model_dump())
    return ProductivityPolicyResponse(
        policy_id=row['id'], policy_name=row['policy_name'], scope_type=row['scope_type'], scope_reference_id=row.get('scope_reference_id'),
        idle_threshold_minutes=row['idle_threshold_minutes'], productive_target_hours=row['productive_target_hours'], borderline_lower_hours=row['borderline_lower_hours'], underproductive_lower_hours=row['underproductive_lower_hours'], warn_on_blacklisted_url=row['warn_on_blacklisted_url'], block_blacklisted_url=row['block_blacklisted_url'], effective_from=row['effective_from']
    )
