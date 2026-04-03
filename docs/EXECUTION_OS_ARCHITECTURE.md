# Execution OS – Architecture Specification (Implemented Reference)

## 1) Final Module Tree
- Dashboard
- Masters
  - Authentication
  - System Settings
  - Company
  - Branch
  - Department
  - Role
  - User
  - Profile
- Man Management
  - Project
  - Task
  - Job
  - Ticket
  - Billing & Costing
  - Settings (SLA)
- Bridge
  - Productivity Tracking
  - Chat
- Intelligence
  - Bruno
  - Help
  - Contextual Help
  - Release Notes
- Product Intelligence
  - UX Analytics
  - Screen Analytics
  - Logs
  - Audit
  - Automation
  - Notifications

## 2) Screen Inventory
| Module | Screens |
|---|---|
| Project | List, Entry, Edit, Detail |
| Task | List, Entry, Edit, Detail |
| Job | List, Entry, Detail + Timesheet |
| Ticket | List, Entry, Detail + Timesheet |

## 3) API Inventory
| Module | APIs |
|---|---|
| Project | CRUD + Close |
| Task | CRUD + Assign |
| Job | Start / Pause / Complete |
| Ticket | Assign / Resolve |
| Automation | Rule + Execute |

## 4) DB Groups
- Security Tables
- Execution Tables
- Workflow Tables
- Finance Tables
- Analytics Tables
- System Tables

## 5) Workers
- SLA Worker
- Notification Worker
- Automation Worker
- Analytics Worker
- Bruno Worker

## 6) Pre-PR Checklist
- No empty UI
- All APIs wired
- RBAC applied
- Audit enabled
- Analytics active
- DB migrations present

## 7) Codex Guardrails
- No placeholder code
- No UI-only screens
- All modules end-to-end
- Reject incomplete PR
