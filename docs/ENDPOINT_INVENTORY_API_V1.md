# Endpoint Inventory (v1)

Base path: `/api/v1`

## Login
- `POST /login`

## RBAC Master
- `GET /rbac/permission-tree`
- `GET /rbac/default-role-mapping`

## User Master
- `GET /users`
- `POST /users`

## Masters
- `GET /masters/companies`
- `POST /masters/companies`

## Governance Engines
- `GET /governance/validation-rules`
- `GET /governance/audit-events`

## Interconnect Master
- `GET /interconnects/modules`
- `GET /interconnects`
- `POST /interconnects`
- `PATCH /interconnects/{interconnect_id}/coverage`
- `GET /interconnects/coverage-matrix`
- `GET /interconnects/reports/summary`

## Dashboard Engine
- `GET /dashboard/default`
- `GET /dashboard/datasets`
- `POST /dashboard/widgets/preview`
- `POST /dashboard/widgets`
- `GET /dashboard/widgets`
- `PUT /dashboard/widgets/{widget_id}`
- `DELETE /dashboard/widgets/{widget_id}`
- `GET /dashboard/reports/usage`
- `GET /dashboard/analytics/summary`

## Global Analytics Engine
- `GET /analytics/filters/constants`
- `GET /analytics/module/{module_code}/prebuilt`
- `POST /analytics/query`
- `GET /analytics/saved-views`
- `POST /analytics/saved-views`
- `GET /analytics/alerts/rules`
- `POST /analytics/alerts/rules`

## Global Reporting Engine
- `GET /reports/templates`
- `POST /reports/run`
- `POST /reports/export`
- `GET /reports/schedules`
- `POST /reports/schedules`

## Project Module
- `GET /projects`
- `POST /projects`
- `GET /projects/{project_id}`
- `PATCH /projects/{project_id}/status`
- `GET /projects/{project_id}/dashboard`
- `GET /projects/{project_id}/reports/summary`

## Status Engine
- `GET /status-engine/status-master`
- `POST /status-engine/status-master`
- `PATCH /status-engine/status-master/{status_id}`
- `DELETE /status-engine/status-master/{status_id}`
- `GET /status-engine/transition-matrix`
- `POST /status-engine/transition-matrix`
- `POST /status-engine/{item_type}`
- `GET /status-engine/{item_type}`
- `PATCH /status-engine/{item_type}/{item_id}/status`
- `GET /status-engine/sla/priority-rules`
- `GET /status-engine/notifications`
- `GET /status-engine/reports/status-transitions`
- `GET /status-engine/reports/task-lifecycle`
- `GET /status-engine/reports/sla-vs-status`
- `GET /status-engine/reports/dependency`
- `GET /status-engine/analytics`
- `GET /status-engine/project-linkage/{project_id}`
- `GET /status-engine/audit-log`
- `GET /status-engine/interconnect-events`

## Ticket Module
- `GET /tickets`
- `POST /tickets`
- `GET /tickets/{ticket_id}`
- `PUT /tickets/{ticket_id}`
- `PATCH /tickets/{ticket_id}/status`
- `GET /tickets/{ticket_id}/followups`
- `POST /tickets/{ticket_id}/followups`
- `GET /tickets/dashboard/summary`
- `GET /tickets/reports/summary`
- `GET /tickets/analytics/summary`
- `GET /tickets/notifications`
- `GET /tickets/audit-log`
- `POST /tickets/sync`

## Task Management Module
- `GET /tasks/rbac/permissions`
- `GET /tasks`
- `POST /tasks`
- `POST /tasks/create`
- `GET /tasks/{task_id}`
- `PUT /tasks/{task_id}`
- `PATCH /tasks/{task_id}/status`
- `GET /tasks/{task_id}/jobs`
- `PATCH /tasks/jobs/{job_id}/status`
- `POST /tasks/jobs/update-status`
- `POST /tasks/timesheets`
- `POST /tasks/timesheets/add`
- `GET /tasks/timesheets`
- `GET /tasks/timesheets/overlap-report`
- `GET /tasks/{task_id}/costing`
- `GET /tasks/dashboard/summary`
- `GET /tasks/reports/summary`
- `GET /tasks/analytics/summary`
- `GET /tasks/notifications`
- `GET /tasks/audit-log`
- `POST /tasks/billing/finalize`

## Approval Engine
- `GET /approvals/config`
- `PUT /approvals/config/{module}`
- `POST /approvals/trigger`
- `GET /approvals/inbox`
- `GET /approvals/{approval_id}`
- `POST /approvals/{approval_id}/action`
- `POST /approvals/{approval_id}/resubmit`
- `POST /approvals/escalations/run`
- `GET /approvals/reports/summary`
- `GET /approvals/analytics/summary`
- `GET /approvals/notifications`
- `GET /approvals/audit-log`
- `POST /approvals/approve`

## Automation Engine
- `GET /automation/variables`
- `GET /automation/templates`
- `POST /automation/templates`
- `PUT /automation/templates/{template_id}`
- `DELETE /automation/templates/{template_id}`
- `GET /automation/rules`
- `POST /automation/rules`
- `PUT /automation/rules/{rule_id}`
- `POST /automation/rules/{rule_id}/clone`
- `PATCH /automation/rules/{rule_id}/active`
- `DELETE /automation/rules/{rule_id}`
- `POST /automation/execute`
- `GET /automation/reports/execution`
- `GET /automation/analytics/summary`

## Algorithm + Calendar Intelligence
- `POST /calendar-intelligence/entries`
- `GET /calendar-intelligence/entries`
- `POST /calendar-intelligence/validate-conflict`
- `GET /calendar-intelligence/suggestions/next-slot`
- `GET /calendar-intelligence/dashboard`
- `GET /calendar-intelligence/reports/summary`
- `GET /calendar-intelligence/analytics/summary`
- `GET /calendar-intelligence/audit-log`

## Task Master + Task Group
- `GET /task-master/groups`
- `POST /task-master/groups`
- `GET /task-master`
- `POST /task-master`
- `PUT /task-master/{task_master_id}`

## Governance Dashboard
- `GET /governance-dashboard/suggested-widgets`
- `GET /governance-dashboard/config/{user_id}`
- `PUT /governance-dashboard/config/{user_id}`
- `GET /governance-dashboard/main/{user_id}`
- `GET /governance-dashboard/analytics/usage`
- `GET /governance-dashboard/export`

## Gamification + Appraisal Engine
- `POST /gamification/events`
- `GET /gamification/employee/{employee}`
- `GET /gamification/admin/scoreboard`
- `GET /gamification/reports/summary`
- `GET /gamification/analytics/summary`
- `POST /gamification/admin/manual-override`
- `GET /gamification/audit-log`

## Collaboration Engine
- `GET /collaboration/shortcuts`
- `GET /collaboration/sidebar/{user}`
- `POST /collaboration/dms/start`
- `POST /collaboration/channels`
- `POST /collaboration/channels/project/{project_id}/sync`
- `POST /collaboration/context/{context_type}/{context_id}`
- `POST /collaboration/messages`
- `POST /collaboration/messages/{message_id}/thread`
- `GET /collaboration/messages/{chat_id}`
- `POST /collaboration/messages/{message_id}/read`
- `POST /collaboration/typing/{chat_id}`
- `GET /collaboration/presence/{user}`
- `PUT /collaboration/presence`
- `GET /collaboration/search`
- `GET /collaboration/notifications/{user}`
- `POST /collaboration/notifications/{user}/mark-all-read`
- `GET /collaboration/reports/summary`
- `GET /collaboration/analytics/summary`
- `WS /collaboration/ws/{user}`

## Unified Notification Engine
- `POST /notifications/trigger`
- `GET /notifications/{user}`
- `POST /notifications/{notification_id}/read`
- `POST /notifications/escalations/run`
- `GET /notifications/audit/logs`
- `GET /notifications/audit/{notification_id}`
- `GET /notifications/reports/summary`

## System Audit Module
- `POST /system-audit/events`
- `GET /system-audit/logs`
- `GET /system-audit/logs/{audit_id}`
- `GET /system-audit/search`
- `GET /system-audit/reports/summary`
- `GET /system-audit/analytics/summary`
- `GET /system-audit/export`
- `GET /audit/logs`

## Auth (API Contract Alignment)
- `POST /auth/login`
- `POST /auth/logout`
- `POST /auth/refresh`

## Goals & KPI Management
- `POST /goals`
- `GET /goals`
- `GET /goals/{goal_id}`
- `PATCH /goals/{goal_id}/progress`
- `GET /goals/reports/achievement`

## Portfolio Management
- `POST /portfolios`
- `GET /portfolios`
- `GET /portfolios/{portfolio_id}/dashboard`

## Workflow Template Library
- `POST /workflow-templates`
- `GET /workflow-templates`
- `POST /workflow-templates/{template_id}/apply`

## Request Intake Forms
- `POST /intake-forms`
- `POST /intake-forms/{form_id}/submit`

## Client Portal
- `POST /client-portal/guest-login`
- `GET /client-portal/projects/{project_id}`
- `POST /client-portal/tickets`

## Documentation Module
- `POST /documentation`
- `GET /documentation`
- `PATCH /documentation/{document_id}`

## Mobile App Layer
- `POST /mobile/security/bind-device`
- `GET /mobile/home`
- `GET /mobile/offline/bootstrap`

## Contextual Help System
- `GET /help/{screen_key}`
- `GET /help`
- `GET /help/route/map`
- `GET /help/route/resolve`


## Contextual Chatbot
- `POST /chatbot/query`
- `GET /chatbot/sessions/{session_id}/messages`
- `GET /chatbot/quick-prompts`
- `POST /chatbot/quick-prompts/usage`
