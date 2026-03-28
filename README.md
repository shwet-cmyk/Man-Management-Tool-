# IESL Man Management Tool (React + Python + MS SQL)

Use-case driven full-stack implementation for IESL man-management workflows.

## UC-MST-005 Employee Master Sync
- API: `/api/v1/sync/employees*`
- Tables: `ref_employee`, `sync_log`

## UC-JOB-001 Create Job
- API: `POST /api/wm/jobs`, `GET /api/wm/jobs`
- Table: `wm_job`
- Validation: company/customer mandatory and master-validated, branch/department/service checks, manager active employee validation, date and numeric validations, billable/non-billable and recurring support.
- Output: `job_id`, `job_no`.

## UC-TASK-001 Create Task
- API: `POST /api/wm/tasks`, `GET /api/wm/tasks`
- Tables: `wm_task`, `wm_task_workflow_state`, `wm_task_assignment`, `wm_audit_log`, `wm_notification_queue`

## UC-TASK-002 Configure Task Participants
- API: `POST /api/wm/tasks/{task_id}/participants`
- Tables: `wm_task_participant`, `wm_task_participant_dependency`, `wm_audit_log`, `wm_notification_queue`
- Supports participant-level role, own planned start/due, dependency chain, mandatory/optional flags, allocation %, and task-level date rollup from participant schedule.

## UC-TASK-003 Update Task Status
- API: `POST /api/wm/tasks/{task_id}/status-transition`, `POST /api/wm/tasks/status-transition/bulk`
- Tables: `wm_task`, `wm_task_status_history`, `wm_task_workflow_state`, `wm_audit_log`, `wm_gamification_event`

## UC-TASK-003 Stage Submission / Handoff
- API: `POST /api/wm/tasks/{task_id}/participants/{participant_id}/submit`
- Tables: `wm_task_participant_submission`, `wm_task_participant_handoff`, `wm_task_participant`, `wm_audit_log`
- Supports participant stage submission, successor handoff creation, acceptance-aware blocking/unblocking, and audit/notification trail.

## UC-TASK-004 Accept / Reject Submitted Work
- API: `POST /api/wm/tasks/{task_id}/submissions/{submission_id}/decision`
- Tables: `wm_task_participant_submission`, `wm_task_participant_handoff`, `wm_task_participant`, `wm_audit_log`
- Supports formal accept/reject decision, override controls, rework routing, and downstream unlock behavior.

## UC-TASK-005 Add Subtask / Checklist / To-Do
- API:
  - `POST /api/wm/tasks/{task_id}/child-items`
  - `POST /api/wm/tasks/{task_id}/child-items/bulk`
  - `GET /api/wm/tasks/{task_id}/child-items`
  - `POST /api/wm/tasks/{task_id}/child-items/{child_item_id}/status`
  - `POST /api/wm/tasks/{task_id}/child-items/{child_item_id}/convert-to-subtask`
  - `POST /api/wm/tasks/{task_id}/child-items/reorder`
- Tables: `wm_task_child_item`, `wm_task_child_item_conversion`, `wm_audit_log`

## UC-TS-001 Add Timesheet against Job / Task / Participant
- API: `POST /api/wm/timesheets`
- Tables: `wm_timesheet`, `wm_audit_log`, `wm_task_participant`, `wm_task`, `wm_job`
- Supports job-task-participant timesheet capture, draft/submit mode, overlap checks, billable/overtime validation, and optional auto-start to `In Progress`.

## UC-TS-002 Submit / Approve / Reject Timesheet
- API:
  - `POST /api/wm/timesheets/{timesheet_id}/submit`
  - `POST /api/wm/timesheets/{timesheet_id}/decision`
- Tables: `wm_timesheet`, `wm_timesheet_approval_history`, `wm_audit_log`
- Supports controlled state transitions (`Draft/Rejected -> Submitted -> Approved/Rejected`) with decision notes, override controls, and status history audit.

## UC-EXP-001 Create Reimbursement / Expense Claim
- API: `POST /api/wm/expense-claims`
- Tables: `wm_expense_claim`, `wm_expense_claim_attachment`, `wm_audit_log`
- Supports claim creation in draft/submitted mode with job/task/participant/timesheet linkage, receipt policy checks, duplicate detection, and cost-context derivation.

## UC-EXP-002 Submit / Approve / Reject Expense Claim
- API:
  - `POST /api/wm/expense-claims/{claim_id}/submit`
  - `POST /api/wm/expense-claims/{claim_id}/decision`
- Tables: `wm_expense_claim`, `wm_expense_claim_approval_history`, `wm_audit_log`
- Supports controlled status transitions with rejection/override controls and approval history audit.

## UC-EXP-003 Convert Approved Expense Claim to Voucher
- API: `POST /api/wm/expense-claims/{claim_id}/convert-to-voucher`
- Tables: `wm_expense_claim`, `wm_expense_claim_conversion_log`, `wm_audit_log`
- Supports conversion eligibility validation, voucher reference capture, conversion status tracking, failure logging, and retry traceability.


## UC-BILL-001 Mark Job / Task / Time / Expense as Billable and Ready for Billing
- API:
  - `POST /api/wm/billing/configure`
  - `POST /api/wm/billing/mark-ready`
  - `POST /api/wm/billing/remove-ready`
- Tables: `wm_billing_configuration`, `wm_billing_readiness`, `wm_timesheet`, `wm_expense_claim`, `wm_audit_log`
- Supports billable-model configuration, readiness validation, approved billable-hours + recoverable-expense inclusion for T&M, fixed-fee readiness without pool dependency, and auditable rollback from ready to billable.


## UC-BILL-002 Create / Link Proforma or Invoice and Mark as Billed
- API:
  - `POST /api/wm/billing/proforma`
  - `POST /api/wm/billing/invoice`
- Tables: `wm_billing_document_link`, `wm_billing_status_history`, `wm_billing_configuration`, `wm_billing_readiness`, `wm_audit_log`
- Supports proforma/invoice create-or-link flows, duplicate reference prevention, partial/full billing status transitions, billed amount traceability, and remaining unbilled amount calculation.


## UC-ANL-001 Cost, Unbilled, Underbilling and Profitability Analytics
- API:
  - `GET /api/wm/analytics/profitability`
  - `GET /api/wm/analytics/exceptions`
- Sources: `wm_timesheet`, `wm_expense_claim`, `wm_billing_document_link`, `wm_billing_configuration`, `wm_billing_readiness`, `ref_employee`
- Supports approved-only cost analytics, billed/unbilled/underbilling calculations, margin and profit metrics, and exception queues (`UNBILLED`, `UNDERBILLED`, `NEGATIVE_MARGIN`, `MISSING_COST_RATE`).


## UC-ANL-002 Operational and Commercial Exception Detection
- API:
  - `GET /api/wm/analytics/exceptions`
  - `POST /api/wm/analytics/exceptions/refresh`
- Tables: `wm_exception_rule`, `wm_exception_instance`, `wm_exception_history`
- Supports exception scan for rolled-over, overrun, unmanaged, no-timesheet, blocked dependency, stale/lost work, unbilled-ready, underbilled/billed-below-cost, and approval-delay conditions with severity and queue filters.




## UC-REPORT-001 Advanced Reporting Engine with MIS, Financial + Operational Reports
- API:
  - `POST /api/wm/reports`
  - `POST /api/wm/reports/config`
  - `POST /api/wm/reports/run`
  - `POST /api/wm/reports/export`
  - `POST /api/wm/reports/schedule`
  - `POST /api/wm/reports/schedule/run-due`
  - `GET /api/wm/reports/standard/job-profitability`
  - `GET /api/wm/reports/standard/client-profitability`
  - `GET /api/wm/reports/standard/employee-productivity`
  - `GET /api/wm/reports/standard/unbilled-work`
  - `GET /api/wm/reports/standard/overrun-analysis`
  - `GET /api/wm/reports/standard/exceptions`
- Tables: `wm_report`, `wm_report_config`, `wm_report_schedule`
- Supports reusable report definitions, user-defined filters/grouping/aggregation, paginated execution, CSV/Excel/PDF export payload generation, and scheduled MIS notification dispatch (daily/weekly/monthly).



## UC-API-001 Integration API Hub + Webhooks + External System Sync
- API:
  - `POST /api/wm/integrations/api-keys`
  - `POST /api/wm/integrations/webhooks`
  - `POST /api/wm/integrations/task`
  - `PUT /api/wm/integrations/task/{task_id}`
  - `GET /api/wm/integrations/jobs/{job_id}`
  - `POST /api/wm/integrations/timesheets`
  - `POST /api/wm/integrations/expenses`
  - `POST /api/wm/integrations/finance/transactions`
- Tables: `wm_api_key`, `wm_api_log`, `wm_webhook`, `wm_webhook_log`
- Supports API-key authentication, per-key rate limiting, mandatory API logging, webhook registration, event dispatch logging for task/timesheet/expense/finance events, and integration endpoints for external systems.

## UC-AI-001 AI Intelligence Layer (Predictive + Prescriptive + Autonomous ERP)
- API:
  - `POST /api/wm/ai/insights`
  - `GET /api/wm/ai/task/{task_id}`
  - `POST /api/wm/ai/apply`
- Tables: `wm_ai_prediction`, `wm_ai_recommendation`
- Supports rule-based predictive signals (delay/cost/completion), prescriptive recommendations (escalation/cost correction/resource reallocation), and auditable recommendation application.



## UC-RBAC-001 Enterprise Role Based Access Control (RBAC)
- API:
  - `POST /api/roles`
  - `GET /api/roles`
  - `PUT /api/roles/{role_id}`
  - `DELETE /api/roles/{role_id}`
  - `POST /api/roles/{role_id}/permissions`
  - `GET /api/roles/{role_id}/permissions`
  - `POST /api/users/{user_id}/assign-role`
  - `POST /api/users/roles`
  - `GET /api/users/{user_id}/permissions`
  - `POST /api/permissions/{permission_id}/scope`
  - `POST /api/role-inheritance`
  - `POST /api/overrides`
  - `POST /api/access/check`
  - `POST /api/auth/check-permission`
  - `POST /api/users/{user_id}/approval-limit`
  - `POST /api/approvals/check`
- Tables: `wm_rbac_role`, `wm_rbac_user_role`, `wm_rbac_module`, `wm_rbac_feature`, `wm_rbac_action`, `wm_rbac_permission`, `wm_rbac_permission_scope`, `wm_rbac_role_inheritance`, `wm_rbac_user_permission_override`, `wm_rbac_approval_limit`, `wm_rbac_access_log`
- Supports multi-role users, feature/action permission matrix, company/branch/department scope checks, deny-over-allow resolution, role inheritance, user-level overrides, strict approval-limit checks, and mandatory access decision logging.



## UC-WF-001 Enterprise Workflow Builder (Event → Condition → Action)
- API:
  - `POST /api/workflows` (or `/api/workflows/create`)
  - `GET /api/workflows`
  - `PUT /api/workflows/{workflow_id}`
  - `DELETE /api/workflows/{workflow_id}`
  - `POST /api/workflows/{workflow_id}/nodes`
  - `POST /api/workflows/{workflow_id}/edges`
  - `POST /api/workflows/{workflow_id}/sla`
  - `POST /api/workflows/trigger`
  - `POST /api/workflows/approve` (or `/api/workflows/approval/approve`)
  - `POST /api/workflows/approval/reject`
  - `GET /api/workflows/status/{instance_id}`
  - `POST /api/workflows/sla/process`
- Tables: `wm_workflow`, `wm_workflow_node`, `wm_workflow_edge`, `wm_workflow_instance`, `wm_workflow_log`, `wm_sla_rule`, `wm_sla_log`, `wm_workflow_approval`
- Supports low-code workflow definitions, nested AND/OR conditions, multi-approver/threshold approvals, SLA pause-resume + breach escalation, workflow version pinning per instance, external action queueing (`CALL_API`/`CALL_WEBHOOK`), and execution logging with loop-guard handling.


## UC-APP-001 Action-Level Multi-Approval Engine (Threshold + Sequential/Parallel)
- API:
  - `POST /api/approval/workflows`
  - `POST /api/approval/submit`
  - `POST /api/approval/action`
  - `GET /api/approval/status/{entity_id}`
- Tables: `wm_approval_workflow`, `wm_approval_step`, `wm_approval_rule`, `wm_approval_transaction`, `wm_approval_log`
- Supports action-level approvals across modules, threshold-based auto-bypass vs pending routing, sequential + parallel approvals, role/user approver resolution, dependency-aware step progression, immutable approval logs, and accounting trigger flag on final approval.


## UC-DOC-001 Document Attachment + Carry Forward (Audit + Continuity)
- API:
  - `POST /api/documents/upload`
  - `POST /api/documents/link`
  - `GET /api/documents/{entity_type}/{entity_id}`
  - `POST /api/documents/version`
  - `POST /api/documents/carry-forward`
- Tables: `wm_document`, `wm_document_link`, `wm_document_audit`
- Supports multi-document attachment, tag/file metadata, version history immutability, hash-based duplicate guard, cross-entity carry-forward without duplication, RBAC-gated document read access, and audit events for upload/link/version/carry-forward/unlink.


## UC-AUD-001 Voucher History + Full Audit Log (Forensic Compliance)
- API:
  - `POST /api/audit/log`
  - `GET /api/audit/{entity_type}/{entity_id}`
  - `GET /api/audit/{audit_log_id}/changes`
  - `GET /api/audit/version/{entity_type}/{entity_id}/{version_no}`
- Tables: `wm_audit_log`, `wm_audit_field_change`, `wm_entity_version`
- Supports immutable audit event recording, field-level before/after change capture, per-entity version snapshots, source/IP/device attribution, and legal-grade traceability across create/update/approve/cancel flows.


## UC-CRM-001 Lead → Opportunity → Deal → Invoice + Customer Lifecycle
- API:
  - `POST /api/crm/lead`
  - `POST /api/crm/lead/{lead_id}/convert`
  - `POST /api/crm/deal`
  - `POST /api/crm/deal/{deal_id}/invoice`
  - `POST /api/crm/followup`
  - `GET /api/crm/followup/due`
  - `POST /api/crm/customer/lifecycle`
- Tables: `wm_crm_lead`, `wm_crm_opportunity`, `wm_crm_deal`, `wm_crm_followup`, `wm_customer_lifecycle`
- Supports end-to-end revenue pipeline stage progression, mandatory follow-up before lead conversion, multi-user lead assignment, approval-limit check before invoicing high-value deals, lifecycle/churn tracking, and audit log generation for pipeline transitions.


## UC-AIF-001 AI Sales Forecasting + Product Prediction Engine
- API:
  - `POST /api/ai/sales-history`
  - `GET /api/ai/forecast?type=product&period=monthly&entity_id={id}`
  - `GET /api/ai/customer/{id}/prediction`
  - `POST /api/ai/targets/generate`
- Tables: `wm_sales_history`, `wm_forecast`, `wm_customer_score`
- Supports linear-trend sales forecasting with minimum-history guardrail, product/branch slicing, customer churn & repeat propensity scoring, forecast persistence, and target recommendation generation (base/stretch).


## UC-AUTO-001 AI Dashboards + Workflow Builder + Rule Engine
- API:
  - `POST /api/dashboard`
  - `GET /api/dashboard/{id}`
  - `POST /api/widget`
  - `POST /api/workflow`
  - `POST /api/workflow/execute`
  - `POST /api/rule`
  - `GET /api/rule/evaluate`
  - `GET /api/sla/status`
- Tables: `wm_rule`, `wm_rule_execution_log` (plus existing dashboard/workflow/SLA tables)
- Supports no-code workflow execution aliases, priority-based rule evaluation with execution logs, dashboard/widget API aliasing, and SLA status aliasing for orchestration use-cases.


## UC-BI-001 Full Analytics Engine (All Permutations & Combinations)
- API:
  - `POST /api/wm/analytics/query`
  - `POST /api/wm/analytics/report`
  - `GET /api/wm/analytics/dashboard`
- Supports dynamic dimension/metric slice-dice queries, report materialization, KPI dashboard summaries, and cross-module revenue/cost/profit analytics based on fact-like sales history inputs.



## UC-SLA-001 SLA + Escalation Engine (Enterprise Core)
- API:
  - `POST /api/wm/sla/rule`
  - `POST /api/wm/sla/holiday`
  - `POST /api/wm/sla/start`
  - `GET /api/wm/sla/status/{entity_type}/{entity_id}`
  - `POST /api/wm/sla/pause`
  - `POST /api/wm/sla/resume`
  - `POST /api/wm/sla/check`
  - `POST /api/wm/sla/escalate`
- Tables: `wm_sla_policy`, `wm_sla_instance`, `wm_sla_escalation`, `wm_business_holiday`
- Supports module-level SLA policies, business-calendar aware due-time calculation, pause/resume lifecycle, breach detection, multi-level escalation channels, and RBAC-aware escalation target validation.



## UC-TKT-001 Enterprise Ticketing System (Support Engine)
- API:
  - `POST /api/wm/tickets`
  - `PUT /api/wm/tickets/{ticket_id}`
  - `POST /api/wm/tickets/{ticket_id}/comments`
  - `POST /api/wm/tickets/{ticket_id}/assign`
  - `GET /api/wm/tickets/{ticket_id}/timeline`
- Tables: `wm_ticket`, `wm_ticket_user`, `wm_ticket_comment`, `wm_ticket_history`
- Supports multi-channel ticket creation, duplicate detection, manual/auto assignment, audit timeline, internal vs external comments, SLA start integration, and workflow trigger integration.

## UC-DASH-001 Custom Drag-and-Drop Dashboard
- API:
  - `POST /api/dashboard`
  - `POST /api/dashboard/widget`
  - `GET /api/dashboard/{dashboard_id}`
  - `POST /api/dashboard/widget/data`
- Tables: `wm_dashboard`, `wm_dashboard_widget`, `wm_widget_query`
- Supports role/user scoped dashboard definitions, widget layout metadata, dynamic X/Y aggregation with safe field mapping, filter-aware widget queries, and drill-down-ready grouped output.

## Frontend Screens
- `/master-sync`
- `/jobs/create`
- `/tasks/create`
- `/tasks/assign`
- `/tasks/status`
- `/tasks/child-items`

## Setup
1. `cp backend/.env.example backend/.env`
2. Run `db/schema.sql` on MS SQL Server
3. `./scripts/start_backend.sh`
4. `./scripts/start_frontend.sh`
