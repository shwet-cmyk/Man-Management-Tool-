from fastapi import APIRouter

router = APIRouter(prefix="/rbac", tags=["Users & Roles"])

API_PERMISSION_TREE = {
    "module": "API",
    "children": [
        "API_VIEW_DASHBOARD",
        "API_APPLICATIONS",
        "API_ADD_APPLICATION",
        "API_EDIT_APPLICATION",
        "API_DISABLE_APPLICATION",
        "API_REVOKE_APPLICATION",
        "API_KEYS",
        "API_GENERATE_KEY",
        "API_REGENERATE_KEY",
        "API_REVOKE_KEY",
        "API_VIEW_KEY_USAGE",
        "API_SCOPES",
        "API_ASSIGN_SCOPES",
        "API_EDIT_SCOPE_MAPPING",
        "API_ENDPOINT_REGISTRY",
        "API_VIEW_ENDPOINT_REGISTRY",
        "API_EDIT_ENDPOINT_METADATA",
        "API_MARK_ENDPOINT_DEPRECATED",
        "API_WEBHOOKS",
        "API_ADD_WEBHOOK",
        "API_EDIT_WEBHOOK",
        "API_PAUSE_WEBHOOK",
        "API_RESUME_WEBHOOK",
        "API_TEST_WEBHOOK",
        "API_RETRY_FAILED_WEBHOOK",
        "API_LOGS",
        "API_VIEW_LOGS",
        "API_EXPORT_LOGS",
        "API_VIEW_FAILED_LOGS",
        "API_USAGE_RATE_LIMITS",
        "API_VIEW_USAGE_ANALYTICS",
        "API_EDIT_RATE_LIMITS",
        "API_SETTINGS",
        "API_VIEW_SETTINGS",
        "API_EDIT_SETTINGS",
        "API_DOCUMENTATION",
        "API_VIEW_DOCUMENTATION",
        "API_EXPORT_DOCUMENTATION",
        "API_TEST_CONSOLE",
        "API_RUN_TEST_REQUEST",
        "API_SENSITIVE_SCOPE_MGMT",
        "API_VIEW_AUTH_FAILURES",
        "API_VIEW_SECURITY_EVENTS",
        "API_ROTATE_SECRETS",
        "API_MANAGE_ENVIRONMENTS",
    ],
}


@router.get("/permission-tree")
def permission_tree():
    return API_PERMISSION_TREE


@router.get("/default-role-mapping")
def default_role_mapping():
    return {
        "Admin": "full_api_access",
        "Integration Admin": "all_except_global_env_if_restricted",
        "API Operator": "ops_plus_limited_key_ops",
        "Developer/Analyst": "docs_registry_limited_logs",
        "Auditor": "view_only",
    }
