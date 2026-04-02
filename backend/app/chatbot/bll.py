from __future__ import annotations

from app.chatbot.dal import PRIORITY_WEIGHT, ChatbotDAL


ROLE_INTENTS = {
    1: {'*'},
    2: {'*'},
    3: {
        'EXPLAIN_SCREEN',
        'FEATURE_DISCOVERY',
        'SHOW_TODAYS_TASKS',
        'SHOW_WORKLOAD',
        'TIMESHEET_TODAY_ENTRIES',
        'TIMESHEET_TOTAL_HOURS',
        'TIMESHEET_BILLABLE_SPLIT',
    },
}


class ChatbotBLL:
    def __init__(self, dal: ChatbotDAL) -> None:
        self.dal = dal

    def build_reply(self, message: str, route_path: str, module_name: str | None = None) -> str:
        module = module_name or route_path.strip('/').split('/')[0] or 'dashboard'
        return (
            f"You are in '{module}'. "
            f"I captured route context '{route_path}'. "
            f"Request noted: {message}"
        )


class QuickPromptService:
    def __init__(self, dal: ChatbotDAL) -> None:
        self.dal = dal

    def get_prompts(self, *, module_name: str, screen_key: str | None, user_id: int, language: str = 'en', limit: int = 7) -> list[dict]:
        role = self.dal.get_user_role(user_id)
        role_id = role['role_id']
        signals = self.dal.get_user_signals(user_id)

        ranked: list[dict] = []
        for row in self.dal.list_quick_prompts():
            if not row['is_active']:
                continue

            if row['role_id'] and row['role_id'] != role_id:
                continue

            if not self._match_context(row=row, module_name=module_name, screen_key=screen_key):
                continue

            if not self._is_intent_allowed(role_id=role_id, intent_code=row['intent_code']):
                continue

            if not self._passes_condition(row=row, signals=signals):
                continue

            ranked.append(self._project_row(row, language, module_name, screen_key, user_id))

        ranked.sort(key=lambda item: (-item['rank_score'], item['display_order'], item['prompt_id']))
        return ranked[:limit]

    def register_prompt_usage(self, user_id: int, prompt_id: int) -> None:
        self.dal.track_prompt_usage(user_id=user_id, prompt_id=prompt_id)

    def _match_context(self, *, row: dict, module_name: str, screen_key: str | None) -> bool:
        module = (module_name or 'global').lower()
        row_module = row['module_name'].lower()

        if row_module not in {'global', module}:
            return False

        row_screen = row.get('screen_key')
        if row_screen and screen_key and row_screen != screen_key:
            return False
        return True

    def _is_intent_allowed(self, *, role_id: int, intent_code: str) -> bool:
        allowed = ROLE_INTENTS.get(role_id, set())
        return '*' in allowed or intent_code in allowed

    def _passes_condition(self, *, row: dict, signals: dict) -> bool:
        condition_query = row.get('condition_query')
        if not condition_query:
            return True

        if 'pending_approvals > 0' in condition_query:
            return signals.get('pending_approvals', 0) > 0
        if 'delayed_tasks > 0' in condition_query:
            return signals.get('delayed_tasks', 0) > 0
        if 'timesheet_overlaps > 0' in condition_query:
            return signals.get('timesheet_overlaps', 0) > 0
        if 'sla_breaches > 0' in condition_query:
            return signals.get('sla_breaches', 0) > 0
        return True

    def _project_row(self, row: dict, language: str, module_name: str, screen_key: str | None, user_id: int) -> dict:
        localized_text = row['prompt_text_en']
        if language == 'hi' and row.get('prompt_text_hi'):
            localized_text = row['prompt_text_hi']
        if language == 'gu' and row.get('prompt_text_gu'):
            localized_text = row['prompt_text_gu']
        if language == 'mr' and row.get('prompt_text_mr'):
            localized_text = row['prompt_text_mr']

        context_score = 0
        if row.get('module_name', '').lower() == module_name.lower():
            context_score += 2
        if screen_key and row.get('screen_key') == screen_key:
            context_score += 3

        usage_score = self.dal.get_prompt_usage(user_id=user_id, prompt_id=row['prompt_id'])
        priority_score = PRIORITY_WEIGHT.get(row.get('priority_level') or 'LOW', 1)

        return {
            'prompt_id': row['prompt_id'],
            'text': localized_text,
            'intent_code': row['intent_code'],
            'action_type': row['action_type'],
            'route_path': row.get('route_path'),
            'display_order': row['display_order'],
            'rank_score': priority_score + context_score + usage_score,
        }
