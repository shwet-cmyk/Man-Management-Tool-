# Modules and Features Inventory

## Core platform modules (`backend/app/modules`)

1. **master_sync**
   - Employee master synchronization from TezERP
   - Sync logs and reconciliation status
2. **employees**
   - Employee master CRUD and listing
3. **departments**
   - Department management
4. **attendance**
   - Attendance capture and reporting
5. **tasks**
   - Task lifecycle (create/update/status)
   - Assignment, participants, dependencies, handoff, child items
6. **timesheets**
   - Time entry, approval routing, utilization records
7. **expense_claims**
   - Expense submission, approvals, attachments, billing conversion tracking
8. **billing**
   - Billing readiness checks
   - Billing status history and document links
9. **approval**
   - Approval workflow configuration
   - Approval execution and logs
10. **analytics**
    - KPI and analytical aggregation APIs
    - BI-style query/report/dashboard endpoints
11. **ai**
    - AI recommendations and prediction APIs
12. **ai_forecasting**
    - Sales/workload forecasting services
13. **reports**
    - Operational report generation and schedules
14. **dashboard**
    - Dashboard widgets and snapshot views
15. **rbac**
    - Role/module/feature/action based permissions
    - Role inheritance and user overrides
16. **documents**
    - Document metadata, links, and audit trail
17. **workflows**
    - Workflow node/edge definitions and instance execution logs
18. **rules**
    - Rule definitions and execution logs
19. **sla**
    - SLA policy/rule/instance tracking
    - Escalation and breach logs
20. **tickets**
    - Ticket lifecycle, user mapping, comments, history
21. **crm**
    - Leads, opportunities, deals, follow-ups, lifecycle scoring
22. **integration_hub**
    - API keys, webhooks, notification queue, integration dispatch
23. **audit**
    - Centralized audit events and field-level change tracking
24. **platform**
    - Shared platform endpoints and health-level utilities
25. **dependency_enforcement**
    - Hard dependency checks (`/tasks/check-dependency`) for START/SUBMIT/APPROVE
    - Sequential/parallel chain support with approval-only dependency closure
26. **tez_audit**
    - Entity-level immutable audit logging with before/after payloads
    - Sensitive field masking and soft-delete audit pattern
27. **sla_enforcement**
    - Priority SLA engine (HIGH=24h, LOW=3 working days, CUSTOM=2 working days)
    - Breach monitor and escalation-level updates

## Enterprise control-plane scaffold (`enterprise-saas/apps/api/src/modules`)

1. **billing**
   - Usage event capture primitives (`USER`, `WORKFLOW_EXECUTION`, `API_CALL`, `AI_TOKENS`)
   - Invoice composition placeholder with ledger posting contract
2. **workflow**
   - Workflow version publication
   - Sandbox simulation endpoint contract
3. **notifications**
   - Channel-agnostic template enqueue (`EMAIL`, `WHATSAPP`, `PUSH`)
   - Retry policy contract
4. **common middleware/guards**
   - Tenant context middleware (`x-tenant-id`, `x-branch-id`)
   - RBAC permission guard
5. **queue + etl**
   - Usage-event worker stub (BullMQ-ready)
   - ETL pipeline stub (extract/transform/load counters)

## Cross-cutting capabilities already represented in models/services

- Multi-role RBAC with scoped permissions
- Workflow engine and approval routing
- CRM lifecycle: Lead → Opportunity → Deal
- Ticketing + SLA tracking/escalation structures
- Audit trails for critical entities
- Billing + ledger related structures
- Document attachments and linkage
- AI forecasting and recommendation service layer
- Integration/webhook primitives

## Current error/conflict check status

- **Merge conflict markers:** none found.
- **Python syntax compilation:** pass for backend app and tests.
- **Pytest execution:** blocked in current environment due missing dependencies (`sqlalchemy`, `fastapi`).
