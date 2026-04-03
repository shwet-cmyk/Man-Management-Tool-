from __future__ import annotations

MODULES = [
    'RBAC', 'USERS', 'ORG', 'DASHBOARD', 'PROJECT', 'PHASE', 'TASK_MASTER', 'TASK', 'JOB', 'TICKET',
    'TIMESHEET', 'BILLING', 'COSTING', 'PROFITABILITY', 'STATUS_ENGINE', 'SLA_ENGINE', 'DEPENDENCY_ENGINE',
    'ROLLOVER_ENGINE', 'APPROVAL', 'AUTOMATION', 'NOTIFICATION', 'AUDIT', 'CHAT', 'COLLABORATION',
    'CALENDAR', 'AI_SCHEDULING', 'GAMIFICATION', 'PRODUCTIVITY', 'PRODUCT_INTELLIGENCE', 'DESKTOP_AGENT',
    'CHATBOT', 'RELEASE_NOTES', 'HELP', 'WORKFLOW_TEMPLATE', 'INTAKE_FORM', 'GOALS_KPI', 'PORTFOLIO',
    'CLIENT_PORTAL', 'DOCUMENTATION', 'ANALYTICS', 'REPORTS',
    'GLOBAL_SEARCH', 'SETTINGS_REGISTRY', 'EXCEPTION_REGISTER', 'FEATURE_FLAG',
    'MONITORING_CONSENT', 'IMPORT_MIGRATION', 'WEBHOOK_GOVERNANCE',
    'IMPERSONATION_CONTROL', 'DATA_ARCHIVAL',
]

ACTIONS = [
    'VIEW', 'CREATE', 'EDIT', 'DELETE', 'APPROVE', 'REJECT', 'EXPORT', 'ANALYTICS_VIEW', 'REPORT_VIEW',
    'AUDIT_VIEW', 'CONFIGURE', 'TRIGGER', 'PUBLISH', 'RUN',
]

SURFACES = ['SCREEN', 'PANEL', 'TAB', 'BUTTON', 'WIDGET', 'FIELD_VISIBLE', 'FIELD_EDITABLE']


def build_catalog() -> list[dict]:
    items = []
    i = 1
    for module in MODULES:
        for action in ACTIONS:
            for surface in SURFACES:
                items.append({
                    'privilege_id': f'PRV-{i:05d}',
                    'code': f'{module}_{action}_{surface}',
                    'module': module,
                    'action': action,
                    'surface': surface,
                })
                i += 1
    return items


ROLE_GRANTS: dict[str, list[str]] = {
    'SuperAdmin': ['*'],
    'Admin': ['*_VIEW_*', '*_CREATE_*', '*_EDIT_*', '*_EXPORT_*', '*_ANALYTICS_VIEW_*', '*_REPORT_VIEW_*', '*_CONFIGURE_*', '*_TRIGGER_*', '*_RUN_*', '*_PUBLISH_*'],
    'Manager': ['*_VIEW_*', 'TASK_EDIT_*', 'JOB_EDIT_*', 'APPROVAL_APPROVE_*', 'APPROVAL_REJECT_*', 'TIMESHEET_REPORT_VIEW_*', 'DASHBOARD_ANALYTICS_VIEW_*'],
    'Auditor': ['*_VIEW_*', '*_AUDIT_VIEW_*', '*_REPORT_VIEW_*', 'PRODUCTIVITY_ANALYTICS_VIEW_*', 'PRODUCT_INTELLIGENCE_ANALYTICS_VIEW_*'],
    'Employee': ['DASHBOARD_VIEW_SCREEN', 'TASK_VIEW_SCREEN', 'TASK_EDIT_FIELD_EDITABLE', 'JOB_VIEW_SCREEN', 'TIMESHEET_CREATE_SCREEN', 'TIMESHEET_VIEW_SCREEN', 'CHAT_VIEW_SCREEN', 'CHATBOT_VIEW_PANEL', 'HELP_VIEW_PANEL', 'RELEASE_NOTES_VIEW_SCREEN'],
    'Developer': ['*_VIEW_*', 'INTERCONNECT_VIEW_*', 'ANALYTICS_VIEW_*', 'REPORTS_VIEW_*', 'AUDIT_AUDIT_VIEW_*', 'PRODUCT_INTELLIGENCE_ANALYTICS_VIEW_*', 'GLOBAL_SEARCH_VIEW_*'],
}


def is_granted(role: str, privilege_code: str) -> bool:
    grants = ROLE_GRANTS.get(role, [])
    if '*' in grants:
        return True
    for pattern in grants:
        if pattern == privilege_code:
            return True
        if '*' in pattern:
            prefix, _, suffix = pattern.partition('*')
            if privilege_code.startswith(prefix) and privilege_code.endswith(suffix):
                return True
    return False
