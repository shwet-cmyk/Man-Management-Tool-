# TEZ Execution System — SRS (Implementation Baseline v4.2)

Implemented layers:
1. Execution Control (Login, RBAC, Users, Masters, Governance)
2. Interconnect Dependency Layer
3. Dashboard Intelligence Layer
4. Global Analytics Engine
5. Global Reporting Engine
6. Project Module with phase/progress/health baseline
7. Centralized Status Engine (status master, transition matrix, SLA/dependency/reminders)
8. Ticket Module with Status/SLA integration and followup timeline
9. Task Management Module with Job/Timesheet/Billing/Costing integration
10. Approval Engine with L1/L2 + comeback flow + escalation
11. Automation Engine with Trigger/Condition/Action + Template/Variable system
12. Algorithm + Calendar Intelligence engine for conflict-aware scheduling
13. AI-assisted scheduling + workload balancing + self-optimizing task benchmark engine
14. Governance Dashboard (Admin/Super Admin) configurable control panel
15. Gamification + Appraisal Engine (points, transparency, appraisal caps)
16. Collaboration Engine (Slack-like DM/channels/context chat/presence/threads/search)
17. Unified Notification Engine (backend-first, template-traceable, escalation-aware)
18. System Audit Module (immutable field-level logging + search/report/export)

## Project Module implemented baseline
- Project create/list/detail/status update
- Mandatory employee group POC validation
- Project status lifecycle validation (Draft→Active/On Hold, Completed→Closed)
- Project dashboard summary (execution/effort/financial/progress)
- Health indicator calculation (On Track / At Risk / Delayed)
- Project interconnect references (Task/Ticket/Job/SLA/Costing)
- Project report/analytics summary endpoint

## User Master enhancement
- Added mandatory `employee_group` in user creation.

## Status Engine implemented baseline
- Central status master for Project/Phase/Task/Job/Ticket status definitions.
- Transition matrix with role gate, approval gate, SLA/interconnect trigger switches.
- Central status transition API with RBAC validation, transition rule validation, and audit logging.
- Task/Job dependency checks (cannot create dependent item until parent completed).
- SLA rule engine with priority durations (High=3, Medium=3, Low=7) and showstopper override (24h).
- Pause/resume SLA hooks driven by status behavior flags.
- Reminder/notification event feed for create and dependency-ready events.
- Reports for status transitions, task lifecycle, SLA vs status, and dependency coverage.
- Analytics summary for bottlenecks, delay reasons, average time-per-status (baseline approximation).

## Ticket Module implemented baseline
- Ticket list with status tabs + filters (ticket no, executive, category, date range, customer).
- Ticket create/edit with mandatory customer, remark, priority, and executive.
- Predefined ticket lifecycle is mapped to Status Engine (OPEN, CUSTOMER_INPUT, DEVELOPMENT, DESIGN_TEAM, FUTURE, SUGGESTION, PUBLISHED, CLOSED).
- Ticket status transition endpoint validates transition/RBAC via central Status Engine.
- SLA starts at ticket creation and follows priority rules (3/3/7 days + showstopper 24-hour override).
- CUSTOMER_INPUT is a pause status for SLA, with resume handling on next workflow status.
- Followup grid + add followup API with optional charges/collection/travel fields.
- Close guardrail: ticket closure requires at least one followup.
- Ticket dashboard summary with execution/SLA/financial metrics.
- Ticket reports and analytics endpoints (status, SLA, executive performance, repeat issues).
- ERP sync hook endpoint (`POST /tickets/sync`) for API-driven ticket intake.

## Task Management Module implemented baseline
- Enforced hierarchy and execution backbone: Project/Phase required at task level, auto-generated Jobs per assigned employee.
- Task create/list/detail/edit/status APIs with dependency handling (Task/Job dependency).
- Job status APIs with status validation through centralized Status Engine.
- Timesheet engine with job linkage validation, start/end duration validation, and closed-job restriction.
- Overlap detection engine (save allowed, overlap flagged), overlap report endpoint with manager/admin scope.
- Costing engine (job cost = hours × hourly rate; task cost = sum of job cost).
- Billing engine (fixed or derived) with expected billing benchmark (₹1500/hour), profitability and efficiency metrics.
- Completion guardrails:
  - task cannot complete while any job remains incomplete,
  - job cannot complete without at least one timesheet entry.
- Notifications for cost overrun and negative profitability.
- Task dashboard, reports, and analytics endpoints covering SLA/cost/productivity/variance/overlaps.

## Approval Engine implemented baseline
- Approval configuration master by module (Task/Job/Timesheet/Billing/Rollover/Cost).
- L1 (Reporting Manager) then L2 (Department POC role) flow.
- Auto-approval path when user-level `approval_required = false` or module config disables approval.
- Reject/Send Back with mandatory remarks.
- Comeback flow: creator resubmits and chain restarts from L1.
- Escalation runner with optional auto-approval after timeout.
- Immutable audit feed + notifications + summary reports/analytics.

## Automation Engine implemented baseline
- Rule list and CRUD with triggers, conditions, actions, activate/deactivate, and cloning.
- Template master (email/notification/alert) with CRUD.
- Variable master endpoint for module-wise `#Variable#` placeholders.
- Execution endpoint to resolve matching rules, render template variables, and log runs.
- Reports and analytics endpoints for execution and usage patterns.

## Algorithm + Calendar Intelligence implemented baseline
- Calendar entry engine with conflict validation using overlap algorithm.
- Hard-block behavior on conflicting task/job slots + smart action hints and next-slot suggestion.
- Next available slot suggestion endpoint respecting working hours.
- Employee calendar dashboard endpoint with day/week/month style view parameter.
- Scheduling reports/analytics + audit log for conflict attempts and planning insights.

## AI-assisted Scheduling + Self-Optimization implemented baseline
- Task Master + Task Group module with standard/min/max hours and historical average.
- Mandatory task mapping to Task Master for task creation (no free-text-only baseline path).
- Over-estimation control that allows save but triggers approval with warning context.
- Auto-learning benchmark update when approved task completion beats current standard.
- Workload engine endpoint with utilization classification:
  - Underutilized (<50%), Optimal (50–85%), Fully Utilized (85–100%), Overutilized (>100%).
- AI scheduling suggestion endpoint for assignment/capacity/reassignment/efficiency warning.

## Governance Dashboard implemented baseline
- Suggested governance widgets catalog endpoint.
- Admin/Super Admin dashboard configuration endpoint with active/locked widgets.
- Main governance dashboard endpoint that composes execution/SLA/utilization/financial/approval widgets.
- Widget usage analytics endpoint (most viewed, most enabled, admin behavior).

## Gamification + Appraisal Engine implemented baseline
- Central points event ledger for jobs/tickets/tasks/projects/dependencies with traceable source + reason.
- Positive/negative points rule map (on-time completion rewards, delay penalties, dependency penalties, project-level penalty).
- Employee gamification widget endpoint with:
  - total points,
  - utilization snapshot,
  - delay counters,
  - appraisal indicator and cap warning,
  - points breakdown with source drilldown payload.
- Appraisal calculator with hard cap rule:
  - tasks delayed > 5, jobs delayed > 10, projects delayed > 2 ⇒ final appraisal capped at 5%.
- Admin scoreboard endpoint (`employee/points/utilization/delays/appraisal%`).
- Reports + analytics endpoints for top performers, chronic delayers, dependency hotspots, team performance.
- Manual override endpoint is available only through explicit logged API and persists immutable override audit entries.

## Collaboration Engine implemented baseline
- Direct Messaging (1:1) chat start endpoint with persistent chat history.
- Project channel creation and sync endpoint; project create flow auto-creates `#project-name` channel.
- Contextual chat creation for Project/Task/Job/Ticket.
- Message system with:
  - text,
  - mentions,
  - attachments,
  - reply-to support.
- Thread reply endpoint with separate thread store.
- Presence engine with online/offline/away/busy + last-seen.
- Typing indicator endpoint and read receipt endpoint.
- Notification feed for new messages / mentions and mark-all-read.
- Global search endpoint for messages/files/users/projects.
- Collaboration reports and analytics endpoints.
- WebSocket endpoint for low-latency messaging events and heartbeat (`PING`/`PONG`).

## Unified Notification Engine implemented baseline
- Backend-first trigger endpoint with predefined templates (no frontend rule builder dependency).
- Delivery channels modeled as In-App/Email/Push/Chat enums.
- Notification rendering pipeline stores template + variables + final message.
- Delivery/read/click/escalation state tracking with timestamps.
- Notification audit listing with filters:
  - date range,
  - module,
  - user,
  - channel type,
  - delivery status,
  - read status.
- Notification detail drill-down exposes message info, delivery trace, and context linkage.
- Escalation runner flags unread notifications over threshold and writes audit events.

## System Audit Module implemented baseline
- Central immutable audit event store with field-level old/new values.
- Filterable audit log list by user/action/module/reference/date.
- Drill-down action summary + field-level change + contextual payload.
- Search endpoint by user/reference/field/value.
- Reports for user activity, change logs, critical changes, rollover/approval subsets.
- Analytics for active users, edited fields, delay frequency, misuse patterns.
- Export endpoint for Excel/PDF payload formatting.

## Existing implemented highlights
- Interconnect structure + coverage matrix + dependency reports
- Dashboard widget engine with RBAC-aware dataset selection
- Analytics constant filters + saved views + alert rules
- Reporting templates + field toggling + exports + schedules

## Next increments
1. MSSQL persistence and migrations.
2. Real drag/drop dashboard canvas persistence.
3. Phase/step/task/job entity persistence + auto task generation.
4. Advanced health/progress recalculation hooks on task/SLA/cost updates.
5. Immutable audit event bus across modules.
