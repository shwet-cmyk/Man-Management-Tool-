from __future__ import annotations

REQUIRED_CAPABILITIES = [
    'menu_option',
    'actionable',
    'clickable',
    'savable',
    'rbac_privileges',
    'user_master_link',
    'approvals',
    'audit_logs',
    'chatbot_context',
    'analytics',
    'custom_reports',
]

MODULE_CAPABILITY_MAP: dict[str, set[str]] = {
    'dashboard': {'menu_option', 'actionable', 'clickable', 'rbac_privileges', 'user_master_link', 'audit_logs', 'chatbot_context', 'analytics', 'custom_reports'},
    'projects': set(REQUIRED_CAPABILITIES),
    'tasks': set(REQUIRED_CAPABILITIES),
    'tickets': set(REQUIRED_CAPABILITIES),
    'approvals': set(REQUIRED_CAPABILITIES),
    'automation': {'menu_option', 'actionable', 'clickable', 'savable', 'rbac_privileges', 'audit_logs', 'analytics', 'custom_reports'},
    'calendar_intelligence': {'menu_option', 'actionable', 'clickable', 'savable', 'rbac_privileges', 'user_master_link', 'audit_logs', 'chatbot_context', 'analytics', 'custom_reports'},
    'collaboration': {'menu_option', 'actionable', 'clickable', 'savable', 'rbac_privileges', 'user_master_link', 'audit_logs', 'chatbot_context', 'analytics'},
    'notification_engine': {'menu_option', 'actionable', 'clickable', 'savable', 'rbac_privileges', 'user_master_link', 'audit_logs', 'analytics', 'custom_reports'},
    'system_audit': {'menu_option', 'actionable', 'clickable', 'rbac_privileges', 'user_master_link', 'audit_logs', 'analytics', 'custom_reports'},
    'status_engine': {'menu_option', 'actionable', 'clickable', 'savable', 'rbac_privileges', 'user_master_link', 'approvals', 'audit_logs', 'chatbot_context', 'analytics', 'custom_reports'},
    'interconnect': {'menu_option', 'actionable', 'clickable', 'savable', 'rbac_privileges', 'user_master_link', 'audit_logs', 'analytics', 'custom_reports'},
    'reporting_engine': {'menu_option', 'actionable', 'clickable', 'savable', 'rbac_privileges', 'user_master_link', 'audit_logs', 'analytics', 'custom_reports'},
    'analytics_engine': {'menu_option', 'actionable', 'clickable', 'savable', 'rbac_privileges', 'user_master_link', 'audit_logs', 'custom_reports'},
    'productivity': set(REQUIRED_CAPABILITIES),
    'chatbot': {'menu_option', 'actionable', 'clickable', 'savable', 'rbac_privileges', 'user_master_link', 'audit_logs', 'analytics'},
    'help': {'menu_option', 'actionable', 'clickable', 'rbac_privileges', 'user_master_link', 'audit_logs', 'chatbot_context'},
}


def module_compliance_report() -> dict:
    modules = []
    compliant_count = 0
    for module_name, capabilities in sorted(MODULE_CAPABILITY_MAP.items()):
        missing = [cap for cap in REQUIRED_CAPABILITIES if cap not in capabilities]
        compliant = not missing
        compliant_count += 1 if compliant else 0
        modules.append(
            {
                'module_name': module_name,
                'compliant': compliant,
                'capabilities': sorted(capabilities),
                'missing_capabilities': missing,
            }
        )

    return {
        'required_capabilities': REQUIRED_CAPABILITIES,
        'summary': {
            'total_modules': len(modules),
            'compliant_modules': compliant_count,
            'non_compliant_modules': len(modules) - compliant_count,
        },
        'modules': modules,
    }
