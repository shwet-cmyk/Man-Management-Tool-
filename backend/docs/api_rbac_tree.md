# API Module RBAC Permission Tree

The API module permission tree is implemented in `RbacService._tree_seed_rows()` under module code `API`.

## Tree (module -> child permissions)
- `API`
  - `API_VIEW_DASHBOARD`
  - `API_APPLICATIONS`
  - `API_ADD_APPLICATION`
  - `API_EDIT_APPLICATION`
  - `API_DISABLE_APPLICATION` *(sensitive)*
  - `API_REVOKE_APPLICATION` *(sensitive)*
  - `API_KEYS`
  - `API_GENERATE_KEY` *(sensitive)*
  - `API_REGENERATE_KEY` *(sensitive)*
  - `API_REVOKE_KEY` *(sensitive)*
  - `API_VIEW_KEY_USAGE`
  - `API_SCOPES`
  - `API_ASSIGN_SCOPES` *(sensitive)*
  - `API_EDIT_SCOPE_MAPPING` *(sensitive)*
  - `API_ENDPOINT_REGISTRY`
  - `API_VIEW_ENDPOINT_REGISTRY`
  - `API_EDIT_ENDPOINT_METADATA` *(sensitive)*
  - `API_MARK_ENDPOINT_DEPRECATED` *(sensitive)*
  - `API_WEBHOOKS`
  - `API_ADD_WEBHOOK`
  - `API_EDIT_WEBHOOK`
  - `API_PAUSE_WEBHOOK` *(sensitive)*
  - `API_RESUME_WEBHOOK` *(sensitive)*
  - `API_TEST_WEBHOOK` *(sensitive)*
  - `API_RETRY_FAILED_WEBHOOK` *(sensitive)*
  - `API_LOGS`
  - `API_VIEW_LOGS`
  - `API_EXPORT_LOGS` *(sensitive)*
  - `API_VIEW_FAILED_LOGS`
  - `API_USAGE_RATE_LIMITS`
  - `API_VIEW_USAGE_ANALYTICS`
  - `API_EDIT_RATE_LIMITS` *(sensitive)*
  - `API_SETTINGS`
  - `API_VIEW_SETTINGS`
  - `API_EDIT_SETTINGS` *(sensitive)*
  - `API_DOCUMENTATION`
  - `API_VIEW_DOCUMENTATION`
  - `API_EXPORT_DOCUMENTATION`
  - `API_TEST_CONSOLE` *(sensitive)*
  - `API_RUN_TEST_REQUEST` *(sensitive)*
  - `API_SENSITIVE_SCOPE_MGMT` *(sensitive)*
  - `API_VIEW_AUTH_FAILURES` *(sensitive)*
  - `API_VIEW_SECURITY_EVENTS` *(sensitive)*
  - `API_ROTATE_SECRETS` *(sensitive)*
  - `API_MANAGE_ENVIRONMENTS` *(sensitive)*

## Default role mapping examples
- **Admin**: Full API permissions.
- **Integration Admin**: All API permissions except optionally global environment controls.
- **API Operator**: Operational views/logs/webhooks/apps/docs; key regeneration optional.
- **Developer/Analyst**: Docs + endpoint registry + limited logs.
- **Auditor**: View-only logs, usage, settings, docs.

Use `POST /api/permissions/tree/seed` and `GET /api/permissions/tree` to apply/retrieve the tree.
