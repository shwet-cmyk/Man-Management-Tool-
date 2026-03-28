# API Endpoint Inventory by Module

Generated via static parsing of `backend/app/main.py` and each module `router.py`.

## ai

| Method | Path | Handler |
|---|---|---|
| `POST` | `/api/v1/wm/ai/apply` | `apply_recommendation` |
| `POST` | `/api/v1/wm/ai/insights` | `generate_insight` |
| `GET` | `/api/v1/wm/ai/task/{task_id}` | `get_task_insight` |
| `POST` | `/api/wm/ai/apply` | `apply_recommendation` |
| `POST` | `/api/wm/ai/insights` | `generate_insight` |
| `GET` | `/api/wm/ai/task/{task_id}` | `get_task_insight` |

## ai_forecasting

| Method | Path | Handler |
|---|---|---|
| `GET` | `/api/ai/customer/{customer_id}/prediction` | `get_customer_prediction` |
| `GET` | `/api/ai/forecast` | `get_forecast` |
| `POST` | `/api/ai/sales-history` | `ingest_sales` |
| `POST` | `/api/ai/targets/generate` | `generate_targets` |
| `GET` | `/api/v1/ai/customer/{customer_id}/prediction` | `get_customer_prediction` |
| `GET` | `/api/v1/ai/forecast` | `get_forecast` |
| `POST` | `/api/v1/ai/sales-history` | `ingest_sales` |
| `POST` | `/api/v1/ai/targets/generate` | `generate_targets` |

## analytics

| Method | Path | Handler |
|---|---|---|
| `GET` | `/api/v1/wm/analytics/dashboard` | `analytics_dashboard` |
| `GET` | `/api/v1/wm/analytics/exceptions` | `get_exceptions` |
| `POST` | `/api/v1/wm/analytics/exceptions/refresh` | `refresh_exceptions` |
| `GET` | `/api/v1/wm/analytics/profitability` | `get_profitability` |
| `POST` | `/api/v1/wm/analytics/query` | `query_analytics` |
| `POST` | `/api/v1/wm/analytics/report` | `generate_report` |
| `GET` | `/api/wm/analytics/dashboard` | `analytics_dashboard` |
| `GET` | `/api/wm/analytics/exceptions` | `get_exceptions` |
| `POST` | `/api/wm/analytics/exceptions/refresh` | `refresh_exceptions` |
| `GET` | `/api/wm/analytics/profitability` | `get_profitability` |
| `POST` | `/api/wm/analytics/query` | `query_analytics` |
| `POST` | `/api/wm/analytics/report` | `generate_report` |

## analytics_framework

| Method | Path | Handler |
|---|---|---|
| `GET` | `/api/v1/wm/analytics-framework/catalog` | `catalog` |
| `POST` | `/api/v1/wm/analytics-framework/comparison` | `comparison` |
| `POST` | `/api/v1/wm/analytics-framework/drilldown` | `drilldown` |
| `POST` | `/api/v1/wm/analytics-framework/leaderboard` | `leaderboard` |
| `POST` | `/api/v1/wm/analytics-framework/matrix` | `matrix` |
| `POST` | `/api/v1/wm/analytics-framework/summary-cards` | `summary_cards` |
| `POST` | `/api/v1/wm/analytics-framework/trend` | `trend_dataset` |
| `POST` | `/api/v1/wm/analytics-framework/widget-dataset` | `widget_dataset` |
| `GET` | `/api/wm/analytics-framework/catalog` | `catalog` |
| `POST` | `/api/wm/analytics-framework/comparison` | `comparison` |
| `POST` | `/api/wm/analytics-framework/drilldown` | `drilldown` |
| `POST` | `/api/wm/analytics-framework/leaderboard` | `leaderboard` |
| `POST` | `/api/wm/analytics-framework/matrix` | `matrix` |
| `POST` | `/api/wm/analytics-framework/summary-cards` | `summary_cards` |
| `POST` | `/api/wm/analytics-framework/trend` | `trend_dataset` |
| `POST` | `/api/wm/analytics-framework/widget-dataset` | `widget_dataset` |

## approval

| Method | Path | Handler |
|---|---|---|
| `POST` | `/api/approval/action` | `take_action` |
| `GET` | `/api/approval/status/{entity_id}` | `get_status` |
| `POST` | `/api/approval/submit` | `submit_for_approval` |
| `POST` | `/api/approval/workflows` | `create_workflow` |
| `POST` | `/api/v1/approval/action` | `take_action` |
| `GET` | `/api/v1/approval/status/{entity_id}` | `get_status` |
| `POST` | `/api/v1/approval/submit` | `submit_for_approval` |
| `POST` | `/api/v1/approval/workflows` | `create_workflow` |

## attendance

| Method | Path | Handler |
|---|---|---|
| `GET` | `/api/v1/attendance` | `get_attendance` |
| `POST` | `/api/v1/attendance` | `add_attendance` |

## audit

| Method | Path | Handler |
|---|---|---|
| `POST` | `/api/audit/log` | `log_audit` |
| `GET` | `/api/audit/version/{entity_type}/{entity_id}/{version_no}` | `get_version` |
| `GET` | `/api/audit/{audit_log_id}/changes` | `get_field_changes` |
| `GET` | `/api/audit/{entity_type}/{entity_id}` | `get_audit_logs` |
| `POST` | `/api/v1/audit/log` | `log_audit` |
| `GET` | `/api/v1/audit/version/{entity_type}/{entity_id}/{version_no}` | `get_version` |
| `GET` | `/api/v1/audit/{audit_log_id}/changes` | `get_field_changes` |
| `GET` | `/api/v1/audit/{entity_type}/{entity_id}` | `get_audit_logs` |

## billing

| Method | Path | Handler |
|---|---|---|
| `POST` | `/api/v1/wm/billing/configure` | `configure_billing` |
| `POST` | `/api/v1/wm/billing/invoice` | `create_or_link_invoice` |
| `POST` | `/api/v1/wm/billing/mark-ready` | `mark_ready_for_billing` |
| `POST` | `/api/v1/wm/billing/proforma` | `create_or_link_proforma` |
| `POST` | `/api/v1/wm/billing/remove-ready` | `remove_readiness` |
| `POST` | `/api/wm/billing/configure` | `configure_billing` |
| `POST` | `/api/wm/billing/invoice` | `create_or_link_invoice` |
| `POST` | `/api/wm/billing/mark-ready` | `mark_ready_for_billing` |
| `POST` | `/api/wm/billing/proforma` | `create_or_link_proforma` |
| `POST` | `/api/wm/billing/remove-ready` | `remove_readiness` |

## crm

| Method | Path | Handler |
|---|---|---|
| `POST` | `/api/crm/customer/lifecycle` | `upsert_lifecycle` |
| `POST` | `/api/crm/deal` | `create_deal` |
| `POST` | `/api/crm/deal/{deal_id}/invoice` | `deal_to_invoice` |
| `POST` | `/api/crm/followup` | `create_followup` |
| `GET` | `/api/crm/followup/due` | `due_followups` |
| `POST` | `/api/crm/lead` | `create_lead` |
| `POST` | `/api/crm/lead/{lead_id}/convert` | `convert_lead` |
| `POST` | `/api/v1/crm/customer/lifecycle` | `upsert_lifecycle` |
| `POST` | `/api/v1/crm/deal` | `create_deal` |
| `POST` | `/api/v1/crm/deal/{deal_id}/invoice` | `deal_to_invoice` |
| `POST` | `/api/v1/crm/followup` | `create_followup` |
| `GET` | `/api/v1/crm/followup/due` | `due_followups` |
| `POST` | `/api/v1/crm/lead` | `create_lead` |
| `POST` | `/api/v1/crm/lead/{lead_id}/convert` | `convert_lead` |

## dashboard

| Method | Path | Handler |
|---|---|---|
| `POST` | `/api/dashboard` | `create_dashboard` |
| `POST` | `/api/dashboard/widget` | `add_widget` |
| `POST` | `/api/dashboard/widget/data` | `get_widget_data` |
| `GET` | `/api/dashboard/{dashboard_id}` | `get_dashboard` |
| `POST` | `/api/v1/dashboard` | `create_dashboard` |
| `POST` | `/api/v1/dashboard/widget` | `add_widget` |
| `POST` | `/api/v1/dashboard/widget/data` | `get_widget_data` |
| `GET` | `/api/v1/dashboard/{dashboard_id}` | `get_dashboard` |

## departments

| Method | Path | Handler |
|---|---|---|
| `GET` | `/api/v1/departments` | `get_departments` |
| `POST` | `/api/v1/departments` | `add_department` |

## dependency_enforcement

| Method | Path | Handler |
|---|---|---|
| `POST` | `/api/tasks/check-dependency` | `check_dependency` |
| `POST` | `/api/tasks/dependencies` | `create_dependency` |
| `POST` | `/api/tasks/dependency-action` | `dependency_action` |
| `POST` | `/api/v1/tasks/check-dependency` | `check_dependency` |
| `POST` | `/api/v1/tasks/dependencies` | `create_dependency` |
| `POST` | `/api/v1/tasks/dependency-action` | `dependency_action` |

## documents

| Method | Path | Handler |
|---|---|---|
| `POST` | `/api/documents/carry-forward` | `carry_forward` |
| `POST` | `/api/documents/link` | `link_document` |
| `POST` | `/api/documents/upload` | `upload_document` |
| `POST` | `/api/documents/version` | `create_version` |
| `DELETE` | `/api/documents/{document_id}/{entity_type}/{entity_id}` | `unlink_document` |
| `GET` | `/api/documents/{entity_type}/{entity_id}` | `get_documents` |
| `POST` | `/api/v1/documents/carry-forward` | `carry_forward` |
| `POST` | `/api/v1/documents/link` | `link_document` |
| `POST` | `/api/v1/documents/upload` | `upload_document` |
| `POST` | `/api/v1/documents/version` | `create_version` |
| `DELETE` | `/api/v1/documents/{document_id}/{entity_type}/{entity_id}` | `unlink_document` |
| `GET` | `/api/v1/documents/{entity_type}/{entity_id}` | `get_documents` |

## employees

| Method | Path | Handler |
|---|---|---|
| `GET` | `/api/v1/employees` | `get_employees` |
| `POST` | `/api/v1/employees` | `add_employee` |

## expense_claims

| Method | Path | Handler |
|---|---|---|
| `POST` | `/api/v1/wm/expense-claims` | `create_expense_claim` |
| `POST` | `/api/v1/wm/expense-claims/{claim_id}/convert-to-voucher` | `convert_to_voucher` |
| `POST` | `/api/v1/wm/expense-claims/{claim_id}/decision` | `decide_expense_claim` |
| `POST` | `/api/v1/wm/expense-claims/{claim_id}/submit` | `submit_expense_claim` |
| `POST` | `/api/wm/expense-claims` | `create_expense_claim` |
| `POST` | `/api/wm/expense-claims/{claim_id}/convert-to-voucher` | `convert_to_voucher` |
| `POST` | `/api/wm/expense-claims/{claim_id}/decision` | `decide_expense_claim` |
| `POST` | `/api/wm/expense-claims/{claim_id}/submit` | `submit_expense_claim` |

## integration_hub

| Method | Path | Handler |
|---|---|---|
| `POST` | `/api/v1/wm/integrations/api-keys` | `create_api_key` |
| `POST` | `/api/v1/wm/integrations/expenses` | `push_expense` |
| `POST` | `/api/v1/wm/integrations/finance/transactions` | `push_transaction` |
| `GET` | `/api/v1/wm/integrations/jobs/{job_id}` | `fetch_job` |
| `POST` | `/api/v1/wm/integrations/task` | `create_task` |
| `PUT` | `/api/v1/wm/integrations/task/{task_id}` | `update_task` |
| `POST` | `/api/v1/wm/integrations/timesheets` | `push_timesheet` |
| `POST` | `/api/v1/wm/integrations/webhooks` | `register_webhook` |
| `POST` | `/api/wm/integrations/api-keys` | `create_api_key` |
| `POST` | `/api/wm/integrations/expenses` | `push_expense` |
| `POST` | `/api/wm/integrations/finance/transactions` | `push_transaction` |
| `GET` | `/api/wm/integrations/jobs/{job_id}` | `fetch_job` |
| `POST` | `/api/wm/integrations/task` | `create_task` |
| `PUT` | `/api/wm/integrations/task/{task_id}` | `update_task` |
| `POST` | `/api/wm/integrations/timesheets` | `push_timesheet` |
| `POST` | `/api/wm/integrations/webhooks` | `register_webhook` |

## jobs

| Method | Path | Handler |
|---|---|---|
| `POST` | `/api/v1/wm/jobs` | `create_job` |
| `GET` | `/api/v1/wm/jobs/dashboard-metrics` | `dashboard_metrics` |
| `POST` | `/api/v1/wm/jobs/governance-config` | `configure` |
| `GET` | `/api/v1/wm/jobs/reports/registers` | `report_registers` |
| `POST` | `/api/v1/wm/jobs/task-shell` | `create_task_shell` |
| `POST` | `/api/v1/wm/jobs/{job_id}/status` | `transition_job` |
| `POST` | `/api/v1/wm/jobs/{job_id}/transfer-decision` | `transfer_decision` |
| `POST` | `/api/wm/jobs` | `create_job` |
| `GET` | `/api/wm/jobs/dashboard-metrics` | `dashboard_metrics` |
| `POST` | `/api/wm/jobs/governance-config` | `configure` |
| `GET` | `/api/wm/jobs/reports/registers` | `report_registers` |
| `POST` | `/api/wm/jobs/task-shell` | `create_task_shell` |
| `POST` | `/api/wm/jobs/{job_id}/status` | `transition_job` |
| `POST` | `/api/wm/jobs/{job_id}/transfer-decision` | `transfer_decision` |

## man_management

| Method | Path | Handler |
|---|---|---|
| `POST` | `/api/v1/wm/man-management/approvals/action` | `approval_action` |
| `GET` | `/api/v1/wm/man-management/dashboard` | `dashboard` |
| `GET` | `/api/v1/wm/man-management/employee-groups` | `list_employee_groups` |
| `POST` | `/api/v1/wm/man-management/employee-groups` | `create_employee_group` |
| `GET` | `/api/v1/wm/man-management/holidays` | `list_holidays` |
| `POST` | `/api/v1/wm/man-management/holidays` | `create_holiday` |
| `POST` | `/api/v1/wm/man-management/job-task-lines` | `add_job_task_line` |
| `POST` | `/api/v1/wm/man-management/job-task-lines/{job_task_id}/status` | `update_job_task_status` |
| `GET` | `/api/v1/wm/man-management/jobs` | `job_register` |
| `POST` | `/api/v1/wm/man-management/jobs` | `create_job` |
| `POST` | `/api/v1/wm/man-management/jobs/billing` | `mark_billed` |
| `DELETE` | `/api/v1/wm/man-management/jobs/{job_id}` | `delete_job` |
| `GET` | `/api/v1/wm/man-management/jobs/{job_id}` | `view_job` |
| `PUT` | `/api/v1/wm/man-management/jobs/{job_id}` | `edit_job` |
| `GET` | `/api/v1/wm/man-management/jobs/{job_id}/billing-readiness` | `billing_readiness` |
| `POST` | `/api/v1/wm/man-management/jobs/{job_id}/copy` | `copy_job` |
| `POST` | `/api/v1/wm/man-management/settings` | `upsert_settings` |
| `GET` | `/api/v1/wm/man-management/timesheets` | `timesheet_register` |
| `POST` | `/api/v1/wm/man-management/timesheets` | `add_timesheet` |
| `POST` | `/api/wm/man-management/approvals/action` | `approval_action` |
| `GET` | `/api/wm/man-management/dashboard` | `dashboard` |
| `GET` | `/api/wm/man-management/employee-groups` | `list_employee_groups` |
| `POST` | `/api/wm/man-management/employee-groups` | `create_employee_group` |
| `GET` | `/api/wm/man-management/holidays` | `list_holidays` |
| `POST` | `/api/wm/man-management/holidays` | `create_holiday` |
| `POST` | `/api/wm/man-management/job-task-lines` | `add_job_task_line` |
| `POST` | `/api/wm/man-management/job-task-lines/{job_task_id}/status` | `update_job_task_status` |
| `GET` | `/api/wm/man-management/jobs` | `job_register` |
| `POST` | `/api/wm/man-management/jobs` | `create_job` |
| `POST` | `/api/wm/man-management/jobs/billing` | `mark_billed` |
| `DELETE` | `/api/wm/man-management/jobs/{job_id}` | `delete_job` |
| `GET` | `/api/wm/man-management/jobs/{job_id}` | `view_job` |
| `PUT` | `/api/wm/man-management/jobs/{job_id}` | `edit_job` |
| `GET` | `/api/wm/man-management/jobs/{job_id}/billing-readiness` | `billing_readiness` |
| `POST` | `/api/wm/man-management/jobs/{job_id}/copy` | `copy_job` |
| `POST` | `/api/wm/man-management/settings` | `upsert_settings` |
| `GET` | `/api/wm/man-management/timesheets` | `timesheet_register` |
| `POST` | `/api/wm/man-management/timesheets` | `add_timesheet` |

## master_sync

| Method | Path | Handler |
|---|---|---|
| `POST` | `/api/v1/sync/employees` | `sync_employees` |
| `GET` | `/api/v1/sync/employees/cache` | `employee_cache` |
| `GET` | `/api/v1/sync/employees/logs` | `employee_sync_logs` |
| `GET` | `/api/v1/sync/employees/summary` | `employee_sync_summary` |

## performance_engine

| Method | Path | Handler |
|---|---|---|
| `POST` | `/api/performance-engine/calendar/drilldown` | `calendar_drilldown` |
| `POST` | `/api/performance-engine/calendar/employee/day` | `employee_calendar_day` |
| `POST` | `/api/performance-engine/calendar/employee/month` | `employee_calendar_month` |
| `POST` | `/api/performance-engine/calendar/employee/week` | `employee_calendar_week` |
| `POST` | `/api/performance-engine/calendar/team-summary` | `team_calendar_summary` |
| `POST` | `/api/performance-engine/capacity` | `employee_capacity` |
| `POST` | `/api/performance-engine/employee-scorecard` | `employee_scorecard` |
| `POST` | `/api/performance-engine/reports/capacity` | `capacity_report` |
| `GET` | `/api/performance-engine/reports/points-ledger` | `points_ledger` |
| `POST` | `/api/performance-engine/score-task` | `score_task` |
| `POST` | `/api/performance-engine/widgets/calendar-capacity` | `calendar_capacity_widget` |
| `POST` | `/api/v1/performance-engine/calendar/drilldown` | `calendar_drilldown` |
| `POST` | `/api/v1/performance-engine/calendar/employee/day` | `employee_calendar_day` |
| `POST` | `/api/v1/performance-engine/calendar/employee/month` | `employee_calendar_month` |
| `POST` | `/api/v1/performance-engine/calendar/employee/week` | `employee_calendar_week` |
| `POST` | `/api/v1/performance-engine/calendar/team-summary` | `team_calendar_summary` |
| `POST` | `/api/v1/performance-engine/capacity` | `employee_capacity` |
| `POST` | `/api/v1/performance-engine/employee-scorecard` | `employee_scorecard` |
| `POST` | `/api/v1/performance-engine/reports/capacity` | `capacity_report` |
| `GET` | `/api/v1/performance-engine/reports/points-ledger` | `points_ledger` |
| `POST` | `/api/v1/performance-engine/score-task` | `score_task` |
| `POST` | `/api/v1/performance-engine/widgets/calendar-capacity` | `calendar_capacity_widget` |

## platform

| Method | Path | Handler |
|---|---|---|
| `GET` | `/api/sla/status` | `sla_status_alias` |
| `GET` | `/api/v1/sla/status` | `sla_status_alias` |
| `POST` | `/api/v1/widget` | `create_widget_alias` |
| `POST` | `/api/v1/workflow` | `create_workflow_alias` |
| `POST` | `/api/v1/workflow/execute` | `execute_workflow_alias` |
| `POST` | `/api/widget` | `create_widget_alias` |
| `POST` | `/api/workflow` | `create_workflow_alias` |
| `POST` | `/api/workflow/execute` | `execute_workflow_alias` |

## project_collab

| Method | Path | Handler |
|---|---|---|
| `POST` | `/api/project-collab/access/resolve` | `resolve_access` |
| `POST` | `/api/project-collab/chat/message` | `post_message` |
| `POST` | `/api/project-collab/chat/{message_id}/pin` | `pin_message` |
| `GET` | `/api/project-collab/chat/{project_id}` | `list_messages` |
| `POST` | `/api/project-collab/file` | `add_file` |
| `GET` | `/api/project-collab/file/{project_id}` | `list_files` |
| `POST` | `/api/project-collab/project` | `create_project` |
| `POST` | `/api/project-collab/project/list` | `list_projects` |
| `GET` | `/api/project-collab/project/{project_id}` | `get_project` |
| `GET` | `/api/project-collab/project/{project_id}/overview` | `overview` |
| `POST` | `/api/project-collab/project/{project_id}/status` | `update_status` |
| `GET` | `/api/project-collab/project/{project_id}/team` | `list_team` |
| `POST` | `/api/project-collab/project/{project_id}/team` | `add_member` |
| `GET` | `/api/project-collab/project/{project_id}/views` | `multi_views` |
| `POST` | `/api/project-collab/reports` | `reports` |
| `POST` | `/api/project-collab/scenarios/seed` | `seed_scenarios` |
| `PATCH` | `/api/project-collab/team-member/{project_team_member_id}` | `update_member` |
| `POST` | `/api/project-collab/watch/follow` | `follow` |
| `POST` | `/api/project-collab/watch/{watcher_id}/unfollow` | `unfollow` |
| `GET` | `/api/project-collab/widgets` | `widgets` |
| `POST` | `/api/v1/project-collab/access/resolve` | `resolve_access` |
| `POST` | `/api/v1/project-collab/chat/message` | `post_message` |
| `POST` | `/api/v1/project-collab/chat/{message_id}/pin` | `pin_message` |
| `GET` | `/api/v1/project-collab/chat/{project_id}` | `list_messages` |
| `POST` | `/api/v1/project-collab/file` | `add_file` |
| `GET` | `/api/v1/project-collab/file/{project_id}` | `list_files` |
| `POST` | `/api/v1/project-collab/project` | `create_project` |
| `POST` | `/api/v1/project-collab/project/list` | `list_projects` |
| `GET` | `/api/v1/project-collab/project/{project_id}` | `get_project` |
| `GET` | `/api/v1/project-collab/project/{project_id}/overview` | `overview` |
| `POST` | `/api/v1/project-collab/project/{project_id}/status` | `update_status` |
| `GET` | `/api/v1/project-collab/project/{project_id}/team` | `list_team` |
| `POST` | `/api/v1/project-collab/project/{project_id}/team` | `add_member` |
| `GET` | `/api/v1/project-collab/project/{project_id}/views` | `multi_views` |
| `POST` | `/api/v1/project-collab/reports` | `reports` |
| `POST` | `/api/v1/project-collab/scenarios/seed` | `seed_scenarios` |
| `PATCH` | `/api/v1/project-collab/team-member/{project_team_member_id}` | `update_member` |
| `POST` | `/api/v1/project-collab/watch/follow` | `follow` |
| `POST` | `/api/v1/project-collab/watch/{watcher_id}/unfollow` | `unfollow` |
| `GET` | `/api/v1/project-collab/widgets` | `widgets` |

## rbac

| Method | Path | Handler |
|---|---|---|
| `POST` | `/api/access/check` | `check_access` |
| `POST` | `/api/access/effective` | `effective_access` |
| `POST` | `/api/approvals/check` | `check_approval_limit` |
| `POST` | `/api/auth/check-permission` | `check_access_alias` |
| `POST` | `/api/overrides` | `add_override` |
| `GET` | `/api/permissions/tree` | `permission_tree` |
| `POST` | `/api/permissions/tree/seed` | `seed_permission_tree` |
| `POST` | `/api/permissions/{permission_id}/scope` | `assign_scope` |
| `GET` | `/api/reports` | `rbac_reports` |
| `POST` | `/api/role-inheritance` | `add_role_inheritance` |
| `GET` | `/api/roles` | `list_roles` |
| `POST` | `/api/roles` | `create_role` |
| `POST` | `/api/roles/seed-templates` | `seed_role_templates` |
| `DELETE` | `/api/roles/{role_id}` | `delete_role` |
| `PUT` | `/api/roles/{role_id}` | `update_role` |
| `GET` | `/api/roles/{role_id}/permissions` | `list_role_permissions` |
| `POST` | `/api/roles/{role_id}/permissions` | `assign_permission` |
| `POST` | `/api/users/roles` | `assign_role_alias` |
| `PUT` | `/api/users/{user_id}/access-profile` | `upsert_access_profile` |
| `POST` | `/api/users/{user_id}/approval-limit` | `upsert_approval_limit` |
| `POST` | `/api/users/{user_id}/assign-role` | `assign_role` |
| `GET` | `/api/users/{user_id}/permissions` | `list_user_permissions` |
| `GET` | `/api/users/{user_id}/scopes` | `get_user_scope` |
| `PUT` | `/api/users/{user_id}/scopes` | `set_user_scope` |
| `POST` | `/api/v1/access/check` | `check_access` |
| `POST` | `/api/v1/access/effective` | `effective_access` |
| `POST` | `/api/v1/approvals/check` | `check_approval_limit` |
| `POST` | `/api/v1/auth/check-permission` | `check_access_alias` |
| `POST` | `/api/v1/overrides` | `add_override` |
| `GET` | `/api/v1/permissions/tree` | `permission_tree` |
| `POST` | `/api/v1/permissions/tree/seed` | `seed_permission_tree` |
| `POST` | `/api/v1/permissions/{permission_id}/scope` | `assign_scope` |
| `GET` | `/api/v1/reports` | `rbac_reports` |
| `POST` | `/api/v1/role-inheritance` | `add_role_inheritance` |
| `GET` | `/api/v1/roles` | `list_roles` |
| `POST` | `/api/v1/roles` | `create_role` |
| `POST` | `/api/v1/roles/seed-templates` | `seed_role_templates` |
| `DELETE` | `/api/v1/roles/{role_id}` | `delete_role` |
| `PUT` | `/api/v1/roles/{role_id}` | `update_role` |
| `GET` | `/api/v1/roles/{role_id}/permissions` | `list_role_permissions` |
| `POST` | `/api/v1/roles/{role_id}/permissions` | `assign_permission` |
| `POST` | `/api/v1/users/roles` | `assign_role_alias` |
| `PUT` | `/api/v1/users/{user_id}/access-profile` | `upsert_access_profile` |
| `POST` | `/api/v1/users/{user_id}/approval-limit` | `upsert_approval_limit` |
| `POST` | `/api/v1/users/{user_id}/assign-role` | `assign_role` |
| `GET` | `/api/v1/users/{user_id}/permissions` | `list_user_permissions` |
| `GET` | `/api/v1/users/{user_id}/scopes` | `get_user_scope` |
| `PUT` | `/api/v1/users/{user_id}/scopes` | `set_user_scope` |

## reports

| Method | Path | Handler |
|---|---|---|
| `POST` | `/api/v1/wm/reports` | `create_report` |
| `POST` | `/api/v1/wm/reports/config` | `save_report_config` |
| `POST` | `/api/v1/wm/reports/export` | `export_report` |
| `POST` | `/api/v1/wm/reports/run` | `run_report` |
| `POST` | `/api/v1/wm/reports/schedule` | `create_schedule` |
| `POST` | `/api/v1/wm/reports/schedule/run-due` | `run_due_schedules` |
| `GET` | `/api/v1/wm/reports/standard/client-profitability` | `client_profitability` |
| `GET` | `/api/v1/wm/reports/standard/employee-productivity` | `employee_productivity` |
| `GET` | `/api/v1/wm/reports/standard/exceptions` | `exception_report` |
| `GET` | `/api/v1/wm/reports/standard/job-profitability` | `job_profitability` |
| `GET` | `/api/v1/wm/reports/standard/overrun-analysis` | `overrun_analysis` |
| `GET` | `/api/v1/wm/reports/standard/unbilled-work` | `unbilled_work` |
| `POST` | `/api/wm/reports` | `create_report` |
| `POST` | `/api/wm/reports/config` | `save_report_config` |
| `POST` | `/api/wm/reports/export` | `export_report` |
| `POST` | `/api/wm/reports/run` | `run_report` |
| `POST` | `/api/wm/reports/schedule` | `create_schedule` |
| `POST` | `/api/wm/reports/schedule/run-due` | `run_due_schedules` |
| `GET` | `/api/wm/reports/standard/client-profitability` | `client_profitability` |
| `GET` | `/api/wm/reports/standard/employee-productivity` | `employee_productivity` |
| `GET` | `/api/wm/reports/standard/exceptions` | `exception_report` |
| `GET` | `/api/wm/reports/standard/job-profitability` | `job_profitability` |
| `GET` | `/api/wm/reports/standard/overrun-analysis` | `overrun_analysis` |
| `GET` | `/api/wm/reports/standard/unbilled-work` | `unbilled_work` |

## rules

| Method | Path | Handler |
|---|---|---|
| `POST` | `/api/rule` | `create_rule` |
| `GET` | `/api/rule/evaluate` | `evaluate` |
| `POST` | `/api/v1/rule` | `create_rule` |
| `GET` | `/api/v1/rule/evaluate` | `evaluate` |

## sla

| Method | Path | Handler |
|---|---|---|
| `POST` | `/api/v1/wm/sla/check` | `check_breaches` |
| `POST` | `/api/v1/wm/sla/escalate` | `escalate` |
| `POST` | `/api/v1/wm/sla/holiday` | `add_holiday` |
| `POST` | `/api/v1/wm/sla/pause` | `pause` |
| `POST` | `/api/v1/wm/sla/resume` | `resume` |
| `POST` | `/api/v1/wm/sla/rule` | `create_rule` |
| `POST` | `/api/v1/wm/sla/start` | `start_sla` |
| `GET` | `/api/v1/wm/sla/status/{entity_type}/{entity_id}` | `get_status` |
| `POST` | `/api/wm/sla/check` | `check_breaches` |
| `POST` | `/api/wm/sla/escalate` | `escalate` |
| `POST` | `/api/wm/sla/holiday` | `add_holiday` |
| `POST` | `/api/wm/sla/pause` | `pause` |
| `POST` | `/api/wm/sla/resume` | `resume` |
| `POST` | `/api/wm/sla/rule` | `create_rule` |
| `POST` | `/api/wm/sla/start` | `start_sla` |
| `GET` | `/api/wm/sla/status/{entity_type}/{entity_id}` | `get_status` |

## sla_enforcement

| Method | Path | Handler |
|---|---|---|
| `POST` | `/api/sla/enforcement/monitor` | `monitor` |
| `POST` | `/api/sla/enforcement/pause-resume` | `pause_resume` |
| `POST` | `/api/sla/enforcement/start` | `start` |
| `GET` | `/api/sla/enforcement/{sla_id}` | `get_status` |
| `POST` | `/api/v1/sla/enforcement/monitor` | `monitor` |
| `POST` | `/api/v1/sla/enforcement/pause-resume` | `pause_resume` |
| `POST` | `/api/v1/sla/enforcement/start` | `start` |
| `GET` | `/api/v1/sla/enforcement/{sla_id}` | `get_status` |

## strategic_ops

| Method | Path | Handler |
|---|---|---|
| `GET` | `/api/strategic-ops/goals` | `list_goals` |
| `POST` | `/api/strategic-ops/goals` | `create_goal` |
| `POST` | `/api/strategic-ops/goals/{goal_id}/link` | `link_goal` |
| `POST` | `/api/strategic-ops/goals/{goal_id}/progress` | `update_goal_progress` |
| `POST` | `/api/strategic-ops/goals/{goal_id}/rollup` | `rollup_goal` |
| `GET` | `/api/strategic-ops/intake` | `intake_register` |
| `POST` | `/api/strategic-ops/intake` | `submit_intake` |
| `POST` | `/api/strategic-ops/intake/{intake_id}/convert` | `intake_convert` |
| `POST` | `/api/strategic-ops/intake/{intake_id}/status` | `intake_status` |
| `GET` | `/api/strategic-ops/launch` | `launch_register` |
| `POST` | `/api/strategic-ops/launch` | `create_launch` |
| `POST` | `/api/strategic-ops/launch/{launch_id}/milestone` | `add_milestone` |
| `POST` | `/api/strategic-ops/launch/{launch_id}/readiness` | `launch_readiness` |
| `POST` | `/api/strategic-ops/launch/{launch_id}/status` | `launch_status` |
| `POST` | `/api/strategic-ops/reports` | `strategic_reports` |
| `POST` | `/api/strategic-ops/resource/allocation` | `allocate_resource` |
| `POST` | `/api/strategic-ops/resource/views` | `resource_views` |
| `GET` | `/api/strategic-ops/widgets` | `strategic_widgets` |
| `GET` | `/api/v1/strategic-ops/goals` | `list_goals` |
| `POST` | `/api/v1/strategic-ops/goals` | `create_goal` |
| `POST` | `/api/v1/strategic-ops/goals/{goal_id}/link` | `link_goal` |
| `POST` | `/api/v1/strategic-ops/goals/{goal_id}/progress` | `update_goal_progress` |
| `POST` | `/api/v1/strategic-ops/goals/{goal_id}/rollup` | `rollup_goal` |
| `GET` | `/api/v1/strategic-ops/intake` | `intake_register` |
| `POST` | `/api/v1/strategic-ops/intake` | `submit_intake` |
| `POST` | `/api/v1/strategic-ops/intake/{intake_id}/convert` | `intake_convert` |
| `POST` | `/api/v1/strategic-ops/intake/{intake_id}/status` | `intake_status` |
| `GET` | `/api/v1/strategic-ops/launch` | `launch_register` |
| `POST` | `/api/v1/strategic-ops/launch` | `create_launch` |
| `POST` | `/api/v1/strategic-ops/launch/{launch_id}/milestone` | `add_milestone` |
| `POST` | `/api/v1/strategic-ops/launch/{launch_id}/readiness` | `launch_readiness` |
| `POST` | `/api/v1/strategic-ops/launch/{launch_id}/status` | `launch_status` |
| `POST` | `/api/v1/strategic-ops/reports` | `strategic_reports` |
| `POST` | `/api/v1/strategic-ops/resource/allocation` | `allocate_resource` |
| `POST` | `/api/v1/strategic-ops/resource/views` | `resource_views` |
| `GET` | `/api/v1/strategic-ops/widgets` | `strategic_widgets` |

## tasks

| Method | Path | Handler |
|---|---|---|
| `GET` | `/api/v1/wm/tasks` | `get_tasks` |
| `POST` | `/api/v1/wm/tasks` | `create_task` |
| `POST` | `/api/v1/wm/tasks/assign/bulk` | `bulk_assign` |
| `POST` | `/api/v1/wm/tasks/status-transition/bulk` | `bulk_status_transition` |
| `POST` | `/api/v1/wm/tasks/{task_id}/assign` | `assign_users` |
| `GET` | `/api/v1/wm/tasks/{task_id}/child-items` | `get_child_items` |
| `POST` | `/api/v1/wm/tasks/{task_id}/child-items` | `create_child_item` |
| `POST` | `/api/v1/wm/tasks/{task_id}/child-items/bulk` | `bulk_create_child_items` |
| `POST` | `/api/v1/wm/tasks/{task_id}/child-items/reorder` | `reorder_child_items` |
| `POST` | `/api/v1/wm/tasks/{task_id}/child-items/{child_item_id}/convert-to-subtask` | `convert_child_item` |
| `POST` | `/api/v1/wm/tasks/{task_id}/child-items/{child_item_id}/status` | `update_child_item_status` |
| `POST` | `/api/v1/wm/tasks/{task_id}/participants` | `configure_participants` |
| `POST` | `/api/v1/wm/tasks/{task_id}/participants/{participant_id}/submit` | `submit_participant_work` |
| `POST` | `/api/v1/wm/tasks/{task_id}/status-transition` | `status_transition` |
| `POST` | `/api/v1/wm/tasks/{task_id}/submissions/{submission_id}/decision` | `decide_submission` |
| `GET` | `/api/wm/tasks` | `get_tasks` |
| `POST` | `/api/wm/tasks` | `create_task` |
| `POST` | `/api/wm/tasks/assign/bulk` | `bulk_assign` |
| `POST` | `/api/wm/tasks/status-transition/bulk` | `bulk_status_transition` |
| `POST` | `/api/wm/tasks/{task_id}/assign` | `assign_users` |
| `GET` | `/api/wm/tasks/{task_id}/child-items` | `get_child_items` |
| `POST` | `/api/wm/tasks/{task_id}/child-items` | `create_child_item` |
| `POST` | `/api/wm/tasks/{task_id}/child-items/bulk` | `bulk_create_child_items` |
| `POST` | `/api/wm/tasks/{task_id}/child-items/reorder` | `reorder_child_items` |
| `POST` | `/api/wm/tasks/{task_id}/child-items/{child_item_id}/convert-to-subtask` | `convert_child_item` |
| `POST` | `/api/wm/tasks/{task_id}/child-items/{child_item_id}/status` | `update_child_item_status` |
| `POST` | `/api/wm/tasks/{task_id}/participants` | `configure_participants` |
| `POST` | `/api/wm/tasks/{task_id}/participants/{participant_id}/submit` | `submit_participant_work` |
| `POST` | `/api/wm/tasks/{task_id}/status-transition` | `status_transition` |
| `POST` | `/api/wm/tasks/{task_id}/submissions/{submission_id}/decision` | `decide_submission` |

## tez_audit

| Method | Path | Handler |
|---|---|---|
| `POST` | `/api/audit/log` | `log_audit` |
| `GET` | `/api/audit/{entity_type}/{entity_id}` | `get_audit_logs` |
| `POST` | `/api/audit/{entity_type}/{entity_id}/soft-delete/{user_id}` | `soft_delete` |
| `POST` | `/api/v1/audit/log` | `log_audit` |
| `GET` | `/api/v1/audit/{entity_type}/{entity_id}` | `get_audit_logs` |
| `POST` | `/api/v1/audit/{entity_type}/{entity_id}/soft-delete/{user_id}` | `soft_delete` |

## ticket_integration

| Method | Path | Handler |
|---|---|---|
| `POST` | `/api/v1/wm/ticket-integration/config` | `configure` |
| `GET` | `/api/v1/wm/ticket-integration/dashboard` | `dashboard` |
| `POST` | `/api/v1/wm/ticket-integration/sync` | `sync_tickets` |
| `POST` | `/api/v1/wm/ticket-integration/tasks/from-ticket` | `create_task_from_ticket` |
| `POST` | `/api/wm/ticket-integration/config` | `configure` |
| `GET` | `/api/wm/ticket-integration/dashboard` | `dashboard` |
| `POST` | `/api/wm/ticket-integration/sync` | `sync_tickets` |
| `POST` | `/api/wm/ticket-integration/tasks/from-ticket` | `create_task_from_ticket` |

## tickets

| Method | Path | Handler |
|---|---|---|
| `POST` | `/api/v1/wm/tickets` | `create_ticket` |
| `POST` | `/api/v1/wm/tickets/dashboard` | `dashboard_metrics` |
| `POST` | `/api/v1/wm/tickets/escalation/daily-digest` | `daily_digest` |
| `POST` | `/api/v1/wm/tickets/rollovers` | `register_rollover` |
| `PUT` | `/api/v1/wm/tickets/{ticket_id}` | `update_ticket` |
| `POST` | `/api/v1/wm/tickets/{ticket_id}/assign` | `assign_users` |
| `POST` | `/api/v1/wm/tickets/{ticket_id}/comments` | `add_comment` |
| `POST` | `/api/v1/wm/tickets/{ticket_id}/convert-to-task` | `convert_to_task` |
| `POST` | `/api/v1/wm/tickets/{ticket_id}/followups` | `add_followup` |
| `POST` | `/api/v1/wm/tickets/{ticket_id}/pause` | `pause_or_resume` |
| `GET` | `/api/v1/wm/tickets/{ticket_id}/timeline` | `get_timeline` |
| `POST` | `/api/wm/tickets` | `create_ticket` |
| `POST` | `/api/wm/tickets/dashboard` | `dashboard_metrics` |
| `POST` | `/api/wm/tickets/escalation/daily-digest` | `daily_digest` |
| `POST` | `/api/wm/tickets/rollovers` | `register_rollover` |
| `PUT` | `/api/wm/tickets/{ticket_id}` | `update_ticket` |
| `POST` | `/api/wm/tickets/{ticket_id}/assign` | `assign_users` |
| `POST` | `/api/wm/tickets/{ticket_id}/comments` | `add_comment` |
| `POST` | `/api/wm/tickets/{ticket_id}/convert-to-task` | `convert_to_task` |
| `POST` | `/api/wm/tickets/{ticket_id}/followups` | `add_followup` |
| `POST` | `/api/wm/tickets/{ticket_id}/pause` | `pause_or_resume` |
| `GET` | `/api/wm/tickets/{ticket_id}/timeline` | `get_timeline` |

## timesheets

| Method | Path | Handler |
|---|---|---|
| `POST` | `/api/v1/wm/timesheets` | `create_timesheet` |
| `POST` | `/api/v1/wm/timesheets/{timesheet_id}/decision` | `decide_timesheet` |
| `POST` | `/api/v1/wm/timesheets/{timesheet_id}/submit` | `submit_timesheet` |
| `POST` | `/api/wm/timesheets` | `create_timesheet` |
| `POST` | `/api/wm/timesheets/{timesheet_id}/decision` | `decide_timesheet` |
| `POST` | `/api/wm/timesheets/{timesheet_id}/submit` | `submit_timesheet` |

## workflows

| Method | Path | Handler |
|---|---|---|
| `GET` | `/api/v1/workflows` | `list_workflows` |
| `POST` | `/api/v1/workflows` | `create_workflow` |
| `POST` | `/api/v1/workflows/approval/approve` | `approve` |
| `POST` | `/api/v1/workflows/approval/reject` | `reject` |
| `POST` | `/api/v1/workflows/approve` | `approve_alias` |
| `POST` | `/api/v1/workflows/create` | `create_workflow_alias` |
| `POST` | `/api/v1/workflows/sla/pause` | `pause_sla` |
| `POST` | `/api/v1/workflows/sla/process` | `process_sla` |
| `POST` | `/api/v1/workflows/sla/resume` | `resume_sla` |
| `GET` | `/api/v1/workflows/status/{instance_id}` | `get_workflow_status` |
| `POST` | `/api/v1/workflows/trigger` | `trigger_workflow` |
| `DELETE` | `/api/v1/workflows/{workflow_id}` | `delete_workflow` |
| `PUT` | `/api/v1/workflows/{workflow_id}` | `update_workflow` |
| `POST` | `/api/v1/workflows/{workflow_id}/edges` | `add_edge` |
| `POST` | `/api/v1/workflows/{workflow_id}/nodes` | `add_node` |
| `POST` | `/api/v1/workflows/{workflow_id}/sla` | `add_sla` |
| `GET` | `/api/workflows` | `list_workflows` |
| `POST` | `/api/workflows` | `create_workflow` |
| `POST` | `/api/workflows/approval/approve` | `approve` |
| `POST` | `/api/workflows/approval/reject` | `reject` |
| `POST` | `/api/workflows/approve` | `approve_alias` |
| `POST` | `/api/workflows/create` | `create_workflow_alias` |
| `POST` | `/api/workflows/sla/pause` | `pause_sla` |
| `POST` | `/api/workflows/sla/process` | `process_sla` |
| `POST` | `/api/workflows/sla/resume` | `resume_sla` |
| `GET` | `/api/workflows/status/{instance_id}` | `get_workflow_status` |
| `POST` | `/api/workflows/trigger` | `trigger_workflow` |
| `DELETE` | `/api/workflows/{workflow_id}` | `delete_workflow` |
| `PUT` | `/api/workflows/{workflow_id}` | `update_workflow` |
| `POST` | `/api/workflows/{workflow_id}/edges` | `add_edge` |
| `POST` | `/api/workflows/{workflow_id}/nodes` | `add_node` |
| `POST` | `/api/workflows/{workflow_id}/sla` | `add_sla` |

