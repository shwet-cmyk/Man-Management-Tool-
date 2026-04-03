# SRS — TEZ Execution System (v4.4)

## 1. High-Level Architecture
- **Frontend (React)**: dashboards, execution workspace, contextual chat, calendar views.
- **Application Layer (FastAPI/Python)**: APIs, domain engines, services, event dispatcher, workers.
- **Data Layer (MSSQL target)**: master tables, transaction tables, and immutable audit tables.

## 2. Core Layering Model
1. **Foundation Layer**: RBAC, User/Org master, role-privilege scopes.
2. **Execution Layer**: Project → Phase → Task → Job → Timesheet, and Ticket execution.
3. **Control Engines**: Status, SLA, dependency, rollover, approval.
4. **Financial Intelligence**: Timesheet, costing, billing, profitability.
5. **Optimization Intelligence**: Task master/group, efficiency, workload, scheduling.
6. **Behavior Layer**: Gamification, points, appraisal, utilization.
7. **Communication Layer**: collaboration + presence + contextual chat.
8. **Automation/Notification Layer**: backend automations + multi-channel notifications.
9. **Visibility Layer**: governance dashboards, analytics, reporting.
10. **Audit & Compliance Layer**: immutable event/action/field logs.
11. **Scheduling & Time Intelligence**: calendar, conflict detection, availability.

## 3. Added Enterprise Modules in this Revision
- Goals & KPI Management.
- Portfolio Management.
- Workflow Template Library.
- Request Intake Forms (Task/Ticket conversion).
- Advanced access-facing Client Portal.
- Documentation module (knowledge base, linked to project/task).
- Mobile App API layer (security/device + offline bootstrap + home widget data).

## 4. Data Architecture
### 4.1 Master Tables
Users, Roles, Privileges, RolePrivileges, Company, Branch, Department, TaskMaster, TaskGroups, Projects.

### 4.2 Transaction Tables
Tasks, Jobs, Timesheets, Expenses, Tickets, Approvals, Notifications, Messages, Channels.

### 4.3 System Tables
AuditLogs, SLALogs, RolloverLogs, GamificationLogs.

### 4.4 Schema Baseline
- Implemented MSSQL baseline DDL is available at:
  - `backend/app/db/mssql_schema.sql`

## 5. Event-Driven Operating Model
All business actions should publish events. Baseline flow:

`User Action → Domain Event → Engine Processing → Notifications → Audit`

Example event sequence for task completion:
- TASK_COMPLETED
- STATUS_ENGINE_EVALUATED
- SLA_ENGINE_EVALUATED
- GAMIFICATION_UPDATED
- NOTIFICATION_SENT
- AUDIT_LOGGED

## 6. API Contract Alignment
Auth contract aligned with:
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/refresh`

Existing module APIs continue under `/api/v1/{module}` with action aliases where needed.

## 7. Real-Time & Worker Requirements
- WebSockets for collaboration and notification scenarios.
- Background worker scheduler loop for SLA/escalation/automation ticks.
- Redis-compatible event bus abstraction with fallback mode.

## 8. Security Requirements
- RBAC enforced at API/service boundaries.
- API key strategy reserved for integration layer.
- Audit entries are append-only.
- No direct DB manipulations from client layer.

## 9. Mobile Layer (API-first)
- Login/session model compatible with bearer token.
- Approval and execution quick actions exposed through backend APIs.
- Notification center and chat sync supported by backend events + WebSocket.
- Offline bootstrap endpoint for first-level cache hydration.

## 10. Non-Negotiable Rules
- No action without RBAC.
- No approval without audit.
- No notification without log.
- No chat without persistence strategy.
