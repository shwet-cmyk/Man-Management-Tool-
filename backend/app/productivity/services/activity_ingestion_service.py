from __future__ import annotations
from collections import Counter
from datetime import date
from app.productivity.repositories.raw_activity_log_repository import RawActivityLogRepository
from app.productivity.repositories.daily_summary_repository import DailySummaryRepository
from app.productivity.repositories.policy_breach_repository import PolicyBreachRepository
from app.productivity.services.idle_computation_service import IdleComputationService
from app.productivity.services.productivity_classification_service import classify_status

class ActivityIngestionService:
    def __init__(self, raw_repo: RawActivityLogRepository, daily_repo: DailySummaryRepository, breach_repo: PolicyBreachRepository, idle_service: IdleComputationService) -> None:
        self.raw_repo = raw_repo
        self.daily_repo = daily_repo
        self.breach_repo = breach_repo
        self.idle_service = idle_service

    async def sync(self, device_id: int, user_id: int, events: list[dict], policy: dict) -> dict:
        processed = 0
        breaches = 0
        class_counter = Counter()
        for event in events:
            event_type = event['event_type'].upper()
            cls = event.get('classification_type') or ('PRODUCTIVE' if 'TEZ' in (event.get('active_domain') or '').upper() else 'NEUTRAL')
            class_counter[cls] += 1
            row = {**event, 'device_id': device_id, 'user_id': user_id, 'classification_type': cls, 'is_idle': False, 'is_locked': event_type=='SESSION_LOCKED', 'is_hibernated': event_type=='SYSTEM_SLEEP'}
            await self.raw_repo.insert(row)
            processed += 1
            if cls in {'BLOCKED','RESTRICTED'}:
                breaches += 1
                await self.breach_repo.insert({'user_id': user_id, 'device_id': device_id, 'breach_timestamp': event['event_timestamp'], 'breach_type': 'BLOCKED_URL' if cls=='BLOCKED' else 'RESTRICTED_APP', 'domain_name': event.get('active_domain'), 'app_name': event.get('active_app_name'), 'action_taken': 'WARNED' if policy.get('warn_on_blacklisted_url', True) else 'LOGGED'})

        idle_minutes = self.idle_service.compute_idle_minutes(events, int(policy['idle_threshold_minutes']))
        productive_minutes = class_counter['PRODUCTIVE']
        summary = {
            'summary_date': date.today(), 'user_id': user_id, 'device_id': device_id,
            'company_id': 1, 'branch_id': None, 'department_id': None,
            'present_minutes': processed, 'active_minutes': processed-idle_minutes,
            'productive_minutes': productive_minutes, 'neutral_minutes': class_counter['NEUTRAL'],
            'unproductive_minutes': class_counter['UNPRODUCTIVE'] + class_counter['RESTRICTED'] + class_counter['BLOCKED'],
            'idle_minutes': idle_minutes, 'locked_minutes': class_counter['LOCKED'],
            'hibernate_minutes': class_counter['HIBERNATE'], 'offline_minutes': 0,
            'shutdown_count': class_counter['SYSTEM_SHUTDOWN'], 'reboot_count': class_counter['SYSTEM_RESTART'],
            'productivity_status': classify_status(productive_minutes, policy),
        }
        await self.daily_repo.insert(summary)
        return {'processed_count': processed, 'breach_count': breaches, 'warnings': []}
