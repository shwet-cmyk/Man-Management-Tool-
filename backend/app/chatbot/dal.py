from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from uuid import uuid4


PRIORITY_WEIGHT = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}


class ChatbotDAL:
    """DAL scaffold with in-memory storage and quick-prompt catalog."""

    def __init__(self) -> None:
        self._store: dict[str, list[dict]] = defaultdict(list)
        self._prompt_usage: dict[tuple[int, int], int] = defaultdict(int)
        self._roles_by_user = {
            1: {'role_id': 1, 'role_name': 'Admin'},
            2: {'role_id': 2, 'role_name': 'Manager'},
            3: {'role_id': 3, 'role_name': 'User'},
        }
        self._data_signals = {
            1: {'pending_approvals': 4, 'delayed_tasks': 3, 'timesheet_overlaps': 1, 'sla_breaches': 2},
            2: {'pending_approvals': 2, 'delayed_tasks': 1, 'timesheet_overlaps': 0, 'sla_breaches': 1},
            3: {'pending_approvals': 0, 'delayed_tasks': 0, 'timesheet_overlaps': 0, 'sla_breaches': 0},
        }
        self._prompt_rows = _build_prompt_seed()

    def create_session_id(self) -> str:
        return str(uuid4())

    def append_message(self, session_id: str, role: str, content: str) -> dict:
        row = {
            'id': str(uuid4()),
            'role': role,
            'content': content,
            'created_at': datetime.now(UTC).isoformat(),
        }
        self._store[session_id].append(row)
        return row

    def list_messages(self, session_id: str) -> list[dict]:
        return list(self._store.get(session_id, []))

    def list_quick_prompts(self) -> list[dict]:
        return list(self._prompt_rows)

    def get_user_role(self, user_id: int) -> dict:
        return self._roles_by_user.get(user_id, {'role_id': 3, 'role_name': 'User'})

    def get_user_signals(self, user_id: int) -> dict:
        return self._data_signals.get(user_id, {'pending_approvals': 0, 'delayed_tasks': 0, 'timesheet_overlaps': 0, 'sla_breaches': 0})

    def track_prompt_usage(self, user_id: int, prompt_id: int) -> None:
        self._prompt_usage[(user_id, prompt_id)] += 1

    def get_prompt_usage(self, user_id: int, prompt_id: int) -> int:
        return self._prompt_usage[(user_id, prompt_id)]


def _row(
    prompt_id: int,
    module_name: str,
    prompt_text_en: str,
    intent_code: str,
    action_type: str = 'QUERY',
    *,
    screen_key: str | None = None,
    role_id: int | None = None,
    priority_level: str = 'MEDIUM',
    condition_type: str = 'STATIC',
    condition_query: str | None = None,
    route_path: str | None = None,
    display_order: int = 0,
    prompt_text_hi: str | None = None,
    prompt_text_gu: str | None = None,
    prompt_text_mr: str | None = None,
) -> dict:
    return {
        'prompt_id': prompt_id,
        'module_name': module_name,
        'screen_key': screen_key,
        'role_id': role_id,
        'priority_level': priority_level,
        'condition_type': condition_type,
        'condition_query': condition_query,
        'prompt_text_en': prompt_text_en,
        'prompt_text_hi': prompt_text_hi,
        'prompt_text_gu': prompt_text_gu,
        'prompt_text_mr': prompt_text_mr,
        'intent_code': intent_code,
        'action_type': action_type,
        'route_path': route_path,
        'display_order': display_order,
        'is_active': True,
    }


def _build_prompt_seed() -> list[dict]:
    rows: list[dict] = []
    i = 1

    rows.extend([
        _row(i, 'global', 'Explain this screen', 'EXPLAIN_SCREEN', condition_type='CONTEXT_DRIVEN', display_order=1),
        _row(i + 1, 'global', 'What can I do here?', 'FEATURE_DISCOVERY', condition_type='CONTEXT_DRIVEN', display_order=2),
        _row(i + 2, 'global', 'Show my pending approvals', 'GET_PENDING_APPROVALS', condition_type='DATA_DRIVEN', condition_query='pending_approvals > 0', priority_level='HIGH', display_order=3, prompt_text_hi='मेरे pending approvals दिखाओ', prompt_text_gu='મારા pending approvals બતાવો', prompt_text_mr='माझे pending approvals दाखवा'),
        _row(i + 3, 'global', 'Show delayed tasks', 'GET_DELAYED_TASKS', condition_type='DATA_DRIVEN', condition_query='delayed_tasks > 0', priority_level='HIGH', display_order=4),
    ])
    i += 4

    def add_module(module: str, screen: str, prompts: list[tuple[str, str, str | None]]):
        nonlocal i, rows
        for order, (text, intent, cond) in enumerate(prompts, 1):
            rows.append(_row(i, module, text, intent, screen_key=screen, condition_type='DATA_DRIVEN' if cond else 'CONTEXT_DRIVEN', condition_query=cond, display_order=order, route_path=f'/{module}'))
            i += 1

    add_module('dashboard', 'dashboard_main', [
        ("Show today's tasks", 'SHOW_TODAYS_TASKS', None),
        ('Show my workload', 'SHOW_WORKLOAD', None),
        ('Show SLA breaches', 'SHOW_SLA_BREACHES', 'sla_breaches > 0'),
        ('Show pending approvals', 'GET_PENDING_APPROVALS', 'pending_approvals > 0'),
    ])
    add_module('projects', 'project_detail', [
        ('Show delayed tasks in this project', 'PROJECT_DELAYED_TASKS', 'delayed_tasks > 0'),
        ('Show project budget vs actual', 'PROJECT_BUDGET_VS_ACTUAL', None),
        ('Show project completion %', 'PROJECT_COMPLETION', None),
        ('Show pending approvals for this project', 'PROJECT_PENDING_APPROVALS', 'pending_approvals > 0'),
    ])
    add_module('tasks', 'task_detail', [
        ('Why is this task delayed?', 'TASK_DELAY_REASON', 'delayed_tasks > 0'),
        ('Show dependency status', 'TASK_DEPENDENCY_STATUS', None),
        ('Show all jobs under this task', 'TASK_CHILD_JOBS', None),
        ('Who changed this deadline?', 'TASK_DEADLINE_AUDIT', None),
    ])
    add_module('jobs', 'job_detail', [
        ('Show timesheet for this job', 'JOB_TIMESHEET', None),
        ('Show job cost analysis', 'JOB_COST_ANALYSIS', None),
        ('Why is this job delayed?', 'JOB_DELAY_REASON', 'delayed_tasks > 0'),
        ('Show SLA status', 'JOB_SLA_STATUS', 'sla_breaches > 0'),
    ])
    add_module('approvals', 'approval_inbox', [
        ('What am I approving?', 'APPROVAL_CONTEXT', None),
        ('Show full task details', 'APPROVAL_TASK_DETAILS', None),
        ('Show approval history', 'APPROVAL_HISTORY', None),
        ('Why was this sent back?', 'APPROVAL_SENT_BACK_REASON', None),
    ])
    add_module('tickets', 'ticket_detail', [
        ('Show ticket history', 'TICKET_HISTORY', None),
        ('Show last follow-up', 'TICKET_LAST_FOLLOWUP', None),
        ('What is SLA status?', 'TICKET_SLA_STATUS', 'sla_breaches > 0'),
        ('Show customer details', 'TICKET_CUSTOMER_DETAILS', None),
    ])
    add_module('timesheets', 'timesheet_list', [
        ("Show my today's time entries", 'TIMESHEET_TODAY_ENTRIES', None),
        ('Show overlaps', 'TIMESHEET_OVERLAPS', 'timesheet_overlaps > 0'),
        ('Show total hours today', 'TIMESHEET_TOTAL_HOURS', None),
        ('Show billable vs non-billable', 'TIMESHEET_BILLABLE_SPLIT', None),
    ])
    add_module('audit', 'audit_log_list', [
        ('Who changed this record?', 'AUDIT_WHO_CHANGED', None),
        ('Show field changes', 'AUDIT_FIELD_CHANGES', None),
        ('Show yesterday changes', 'AUDIT_YESTERDAY', None),
        ('Show user activity', 'AUDIT_USER_ACTIVITY', None),
    ])
    add_module('login', 'login_main', [
        ('Why am I unable to login?', 'LOGIN_TROUBLESHOOT', None),
        ('How do I reset my password?', 'LOGIN_FORGOT_PASSWORD', None),
        ('When is OTP required?', 'LOGIN_OTP_POLICY', None),
        ('Why is my account locked?', 'LOGIN_LOCKOUT_REASON', None),
    ])
    add_module('system', 'system_settings_main', [
        ('Is two-factor authentication enabled?', 'SYSTEM_2FA_STATUS', None),
        ('Is guided tour active for new users?', 'SYSTEM_GUIDED_TOUR_STATUS', None),
        ('Is productivity agent enabled?', 'SYSTEM_PRODUCTIVITY_AGENT_STATUS', None),
        ('Which modules are disabled?', 'SYSTEM_DISABLED_MODULES', None),
    ])
    add_module('company', 'company_master_admin', [
        ('How many companies are active?', 'COMPANY_ACTIVE_COUNT', None),
        ('Which is the default company?', 'COMPANY_DEFAULT', None),
        ('Can I deactivate this company?', 'COMPANY_DEACTIVATE_IMPACT', None),
    ])
    add_module('branch', 'branch_master_admin', [
        ('Which company is this branch under?', 'BRANCH_PARENT_COMPANY', None),
        ('How many users are mapped to this branch?', 'BRANCH_USER_COUNT', None),
        ('What happens if I deactivate this branch?', 'BRANCH_DEACTIVATE_IMPACT', None),
    ])
    add_module('department', 'department_master_admin', [
        ('Which department is under which branch?', 'DEPARTMENT_BRANCH_MAP', None),
        ('Who is head of this department?', 'DEPARTMENT_HEAD', None),
        ('Why is this department not visible?', 'DEPARTMENT_VISIBILITY', None),
    ])
    add_module('roles', 'rbac_role_admin', [
        ('Which role can create projects?', 'ROLE_CAN_CREATE_PROJECTS', None),
        ('Who can approve tickets?', 'ROLE_CAN_APPROVE_TICKETS', None),
        ('Why can user view but not edit?', 'ROLE_MISSING_EDIT_PRIVILEGE', None),
    ])
    add_module('users', 'user_master_admin', [
        ('What role is assigned to this user?', 'USER_ROLE_ASSIGNED', None),
        ('Who is this user’s reporting manager?', 'USER_REPORTING_MANAGER', None),
        ('Is Bruno enabled for this user?', 'USER_BRUNO_ENABLED', None),
    ])
    add_module('profile', 'user_profile_main', [
        ('How do I change my password?', 'PROFILE_CHANGE_PASSWORD', None),
        ('How do I change notifications?', 'PROFILE_NOTIFICATION_PREFS', None),
        ('How do I restart the guided tour?', 'PROFILE_RESET_GUIDED_TOUR', None),
    ])
    add_module('dashboard', 'dashboard_role_home', [
        ('What should I work on first today?', 'DASHBOARD_TOP_PRIORITIES', None),
        ('Show my overdue tasks.', 'DASHBOARD_OVERDUE_TASKS', None),
        ('Which tickets are close to SLA breach?', 'DASHBOARD_SLA_RISK_TICKETS', 'sla_breaches > 0'),
        ('What changed since yesterday?', 'DASHBOARD_YESTERDAY_CHANGES', None),
    ])
    add_module('projects', 'project_list_main', [
        ('Which projects are overdue?', 'PROJECTS_OVERDUE', None),
        ('Show high-risk projects.', 'PROJECTS_HIGH_RISK', None),
        ('Which project has the most open tickets?', 'PROJECTS_MAX_OPEN_TICKETS', None),
    ])
    add_module('tasks', 'task_list_main', [
        ('Which tasks are overdue?', 'TASKS_OVERDUE', None),
        ('Show my blocked tasks.', 'TASKS_BLOCKED', None),
        ('Which tasks are close to SLA breach?', 'TASKS_SLA_RISK', None),
    ])
    add_module('jobs', 'job_list_main', [
        ('Which jobs are pending under this task?', 'JOBS_PENDING_BY_TASK', None),
        ('Who is working on this job?', 'JOB_CURRENT_ASSIGNEE', None),
        ('Why is actual time higher than planned time?', 'JOB_TIME_VARIANCE_REASON', None),
    ])
    add_module('tickets', 'ticket_list_main', [
        ('Which tickets are critical?', 'TICKETS_CRITICAL', None),
        ('Which tickets are overdue?', 'TICKETS_OVERDUE', None),
        ('Show my assigned tickets.', 'TICKETS_MY_ASSIGNED', None),
    ])
    add_module('approvals', 'approval_inbox_main', [
        ('What approvals are pending for me?', 'APPROVALS_PENDING_ME', None),
        ('Which approvals are near SLA breach?', 'APPROVALS_SLA_RISK', None),
        ('Show high-priority approvals first.', 'APPROVALS_HIGH_PRIORITY', None),
    ])
    add_module('sla', 'sla_monitor_main', [
        ('Which items are about to breach SLA?', 'SLA_NEAR_BREACH', None),
        ('Show me breached tickets.', 'SLA_BREACHED_TICKETS', None),
        ('Which assignee has the most at-risk items?', 'SLA_AT_RISK_BY_ASSIGNEE', None),
    ])
    add_module('timesheets', 'timesheet_list_main', [
        ('Which timesheets are pending my approval?', 'TIMESHEET_PENDING_APPROVAL', None),
        ('Have I submitted all my entries for this week?', 'TIMESHEET_SUBMISSION_COMPLIANCE', None),
        ('Show rejected entries.', 'TIMESHEET_REJECTED', None),
    ])
    add_module('billing', 'billing_costing_main', [
        ('Which billable hours are still unbilled?', 'BILLING_UNBILLED_HOURS', None),
        ('What is the current profitability of this project?', 'BILLING_PROJECT_PROFITABILITY', None),
        ('Why is this project’s margin lower than expected?', 'BILLING_MARGIN_DROP_REASON', None),
    ])
    add_module('productivity', 'productivity_dashboard_main', [
        ('Which users have the highest idle time today?', 'PRODUCTIVITY_HIGH_IDLE_USERS', None),
        ('Is my agent syncing properly?', 'PRODUCTIVITY_AGENT_SYNC_STATUS', None),
        ('Show top productive apps.', 'PRODUCTIVITY_TOP_APPS', None),
    ])
    add_module('ux', 'ux_analytics_dashboard', [
        ('Which screen has the most dead clicks?', 'UX_MAX_DEAD_CLICKS', None),
        ('Show highest drop-off screens.', 'UX_HIGHEST_DROPOFF', None),
        ('What changed in friction after the last release?', 'UX_RELEASE_FRICTION_DELTA', None),
    ])
    add_module('devlogs', 'devlogs_dashboard', [
        ('What broke after the last release?', 'DEVLOGS_POST_RELEASE_BREAK', None),
        ('Which APIs are failing most?', 'DEVLOGS_TOP_FAILING_APIS', None),
        ('Show critical unresolved errors.', 'DEVLOGS_CRITICAL_UNRESOLVED', None),
    ])
    add_module('automation', 'automation_engine_list_main', [
        ('Which automations are failing?', 'AUTOMATION_FAILING_RULES', None),
        ('Show disabled rules.', 'AUTOMATION_DISABLED_RULES', None),
        ('What automation sends SLA alerts?', 'AUTOMATION_SLA_ALERT_RULE', None),
    ])
    add_module('audit', 'audit_logs_main', [
        ('Who changed this record?', 'AUDIT_CHANGED_RECORD', None),
        ('When was this project closed?', 'AUDIT_PROJECT_CLOSED_TIME', None),
        ('Show deletions from this week.', 'AUDIT_WEEKLY_DELETIONS', None),
    ])

    return rows
