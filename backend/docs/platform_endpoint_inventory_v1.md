# Platform Endpoint Inventory (v1)

Base path: `/api/v1`

Common query params for list endpoints:
`page`, `page_size`, `search`, `sort_by`, `sort_order`, `filters`, `last_updated_since`

---

## API Admin Module
- `GET /api-apps`
- `POST /api-apps`
- `GET /api-apps/{id}`
- `PUT /api-apps/{id}`
- `PATCH /api-apps/{id}/status`
- `GET /api-apps/{id}/scopes`
- `POST /api-apps/{id}/scopes`
- `GET /api-apps/{id}/keys`
- `POST /api-apps/{id}/keys`
- `POST /api-apps/{id}/keys/{keyId}/revoke`
- `POST /api-apps/{id}/keys/{keyId}/regenerate`
- `GET /api-apps/{id}/usage`
- `GET /api-apps/{id}/logs`
- `GET /scopes`
- `GET /endpoint-registry`
- `GET /endpoint-registry/{id}`
- `GET /webhooks`
- `POST /webhooks`
- `GET /webhooks/{id}`
- `PUT /webhooks/{id}`
- `POST /webhooks/{id}/test`
- `POST /webhooks/{id}/pause`
- `POST /webhooks/{id}/resume`
- `GET /webhooks/{id}/deliveries`
- `GET /api-logs`
- `GET /api-settings`
- `PUT /api-settings`
- `GET /api-docs`

## Users & Roles (RBAC)
- `GET /users`
- `POST /users`
- `GET /users/{id}`
- `PUT /users/{id}`
- `PATCH /users/{id}/status`
- `GET /users/{id}/permissions`
- `PUT /users/{id}/permissions`
- `GET /users/{id}/effective-access`
- `GET /roles`
- `POST /roles`
- `GET /roles/{id}`
- `PUT /roles/{id}`
- `GET /roles/{id}/permissions`
- `PUT /roles/{id}/permissions`
- `GET /permission-tree`
- `GET /permission-tree/modules`
- `GET /access-matrix`
- `GET /hierarchy`
- `GET /hierarchy/{userId}/downline`

## Masters
### Companies / Branches / Departments / Employees
- `GET /companies`, `POST /companies`, `GET /companies/{id}`, `PUT /companies/{id}`, `PATCH /companies/{id}/archive`
- `GET /branches`, `POST /branches`, `GET /branches/{id}`, `PUT /branches/{id}`, `PATCH /branches/{id}/archive`
- `GET /departments`, `POST /departments`, `GET /departments/{id}`, `PUT /departments/{id}`, `PATCH /departments/{id}/archive`
- `GET /employees`, `POST /employees`, `GET /employees/{id}`, `PUT /employees/{id}`, `PATCH /employees/{id}/archive`
- `GET /employees/{id}/cost-profile`, `GET /employees/{id}/shift`, `GET /employees/{id}/manager`, `GET /employees/{id}/capacity`

### Employee Groups / Holidays / Shifts
- `GET /employee-groups`, `POST /employee-groups`, `GET /employee-groups/{id}`, `PUT /employee-groups/{id}`
- `GET /holidays`, `POST /holidays`, `GET /holidays/{id}`, `PUT /holidays/{id}`, `PATCH /holidays/{id}/archive`
- `GET /shifts`, `POST /shifts`, `GET /shifts/{id}`, `PUT /shifts/{id}`

### Customers / Products / Classifications
- `GET /customers`, `POST /customers`, `GET /customers/{id}`, `PUT /customers/{id}`, `PATCH /customers/{id}/archive`
- `GET /customers/{id}/addresses`, `POST /customers/{id}/addresses`, `PUT /customers/{id}/addresses/{addressId}`, `DELETE /customers/{id}/addresses/{addressId}`
- `GET /customers/{id}/services`, `GET /customers/{id}/ledger`, `GET /customers/{id}/price-list`, `POST /customers/{id}/price-list`
- `GET /customers/{id}/discount-list`, `POST /customers/{id}/discount-list`, `GET /customers/{id}/remarks`
- `GET /products`, `POST /products`, `GET /products/{id}`, `PUT /products/{id}`
- `GET /categories`, `GET /priorities`, `GET /statuses`

## Tickets
- `GET /tickets`, `POST /tickets`, `GET /tickets/{id}`, `PUT /tickets/{id}`
- `PATCH /tickets/{id}/status`, `PATCH /tickets/{id}/assign`
- `POST /tickets/{id}/followups`, `GET /tickets/{id}/followups`
- `POST /tickets/{id}/close`, `POST /tickets/{id}/reopen`
- `POST /tickets/{id}/convert-to-task`, `GET /tickets/{id}/linked-tasks`, `GET /tickets/{id}/sla`, `GET /tickets/{id}/activity`

## Tasks
- `GET /tasks`, `POST /tasks`, `GET /tasks/{id}`, `PUT /tasks/{id}`
- `PATCH /tasks/{id}/status`, `PATCH /tasks/{id}/assign`, `PATCH /tasks/{id}/manager`
- `POST /tasks/{id}/complete`, `POST /tasks/{id}/reopen`
- `GET /tasks/{id}/jobs`, `POST /tasks/{id}/jobs`
- `GET /tasks/{id}/timesheets-summary`, `GET /tasks/{id}/costing`, `GET /tasks/{id}/profitability`
- `GET /tasks/{id}/activity`, `GET /tasks/{id}/comments`, `POST /tasks/{id}/comments`
- `GET /tasks/{id}/approvals`, `POST /tasks/{id}/approvals`
- `GET /tasks/{id}/team`, `POST /tasks/{id}/team`

## Jobs / Job Tasks
- `GET /jobs`, `POST /jobs`, `GET /jobs/{id}`, `PUT /jobs/{id}`
- `PATCH /jobs/{id}/status`, `PATCH /jobs/{id}/assign`, `PATCH /jobs/{id}/due-date`
- `POST /jobs/{id}/complete`, `POST /jobs/{id}/reopen`
- `GET /jobs/{id}/dependencies`, `POST /jobs/{id}/dependencies`
- `GET /jobs/{id}/transfer`, `POST /jobs/{id}/transfer`, `POST /jobs/{id}/accept-transfer`, `POST /jobs/{id}/reject-transfer`
- `GET /jobs/{id}/timesheets`, `POST /jobs/{id}/comments`, `GET /jobs/{id}/comments`
- `GET /jobs/{id}/billing-readiness`, `POST /jobs/{id}/mark-billed`
- `GET /jobs/{id}/costing`, `GET /jobs/{id}/profitability`
- `GET /jobs/{id}/rollovers`, `POST /jobs/{id}/rollovers`
- `GET /job-tasks`, `POST /job-tasks`, `GET /job-tasks/{id}`, `PUT /job-tasks/{id}`
- `PATCH /job-tasks/{id}/status`, `POST /job-tasks/{id}/complete`, `POST /job-tasks/{id}/reopen`

## Timesheets
- `GET /timesheets`, `POST /timesheets`, `GET /timesheets/{id}`, `PUT /timesheets/{id}`, `DELETE /timesheets/{id}`
- `POST /timesheets/{id}/submit`, `POST /timesheets/{id}/approve`, `POST /timesheets/{id}/reject`
- `GET /timesheets/{id}/expenses`, `POST /timesheets/{id}/expenses`
- `GET /timesheets/{id}/reimbursements`, `POST /timesheets/{id}/reimbursements`
- `GET /timesheets/{id}/attachments`, `POST /timesheets/{id}/attachments`

## Projects / Team / Chat
- `GET /projects`, `POST /projects`, `GET /projects/{id}`, `PUT /projects/{id}`
- `PATCH /projects/{id}/status`, `POST /projects/{id}/archive`
- `GET /projects/{id}/tasks`, `GET /projects/{id}/jobs`
- `GET /projects/{id}/team`, `POST /projects/{id}/team`, `PUT /projects/{id}/team/{memberId}`, `DELETE /projects/{id}/team/{memberId}`
- `GET /projects/{id}/timeline`, `GET /projects/{id}/calendar`, `GET /projects/{id}/dashboard`
- `GET /projects/{id}/files`, `POST /projects/{id}/files`
- `GET /projects/{id}/activity`, `GET /projects/{id}/chat`, `POST /projects/{id}/chat`
- `GET /project-team-members`, `GET /comments`, `GET /mentions`
- `POST /messages`, `PUT /messages/{id}`, `DELETE /messages/{id}`, `POST /messages/{id}/pin`, `POST /messages/{id}/unpin`

## Approvals
- `GET /approvals`, `POST /approvals`, `GET /approvals/{id}`
- `POST /approvals/{id}/approve`, `POST /approvals/{id}/reject`, `POST /approvals/{id}/return`, `POST /approvals/{id}/escalate`, `POST /approvals/{id}/comment`

## Alerts / Automation
- `GET /alert-settings`, `POST /alert-settings`, `GET /alert-settings/{id}`, `PUT /alert-settings/{id}`, `PATCH /alert-settings/{id}/status`
- `GET /alert-logs`
- `GET /notification-queue`, `GET /notification-failures`, `POST /notification-failures/{id}/retry`
- `GET /message-templates`, `POST /message-templates`, `GET /message-templates/{id}`, `PUT /message-templates/{id}`
- `GET /recipient-matrix`, `POST /recipient-matrix`, `PUT /recipient-matrix/{id}`

## Goals / Intake / Launches / Resource Planning
- Goals: `GET /goals`, `POST /goals`, `GET /goals/{id}`, `PUT /goals/{id}`, `PATCH /goals/{id}/status`, `PATCH /goals/{id}/progress`, `GET /goals/{id}/links`, `POST /goals/{id}/links`, `DELETE /goals/{id}/links/{linkId}`, `GET /goals/{id}/history`
- Intake: `GET /intake-requests`, `POST /intake-requests`, `GET /intake-requests/{id}`, `PUT /intake-requests/{id}`, `POST /intake-requests/{id}/approve`, `POST /intake-requests/{id}/reject`, `POST /intake-requests/{id}/convert-to-ticket`, `POST /intake-requests/{id}/convert-to-project`, `POST /intake-requests/{id}/convert-to-task`, `POST /intake-requests/{id}/convert-to-job`
- Launches: `GET /launches`, `POST /launches`, `GET /launches/{id}`, `PUT /launches/{id}`, `PATCH /launches/{id}/status`, `GET /launches/{id}/milestones`, `POST /launches/{id}/milestones`, `PUT /launches/{id}/milestones/{milestoneId}`, `GET /launches/{id}/readiness`, `PATCH /launches/{id}/readiness`, `GET /launches/{id}/risks`, `POST /launches/{id}/risks`
- Capacity: `GET /capacity/employees/{employeeId}/month`, `GET /capacity/employees/{employeeId}/week`, `GET /capacity/employees/{employeeId}/day`, `GET /capacity/team/{managerId}/summary`, `GET /capacity/free`, `GET /capacity/overloaded`, `GET /capacity/underutilized`
- Allocations: `GET /allocations`, `POST /allocations`, `PUT /allocations/{id}`, `POST /allocations/{id}/reassign`

## Gamification / Performance / Commercial
- `GET /points/ledger`, `GET /points/employees/{employeeId}/summary`, `GET /points/leaderboard`, `GET /increments/eligibility`, `GET /increments/employees/{employeeId}`, `POST /points/manual-adjustments`
- `GET /profitability/tasks/{taskId}`, `GET /profitability/jobs/{jobId}`, `GET /profitability/clients/{clientId}`
- `GET /commercial/billable-summary`, `GET /commercial/non-billable-summary`, `GET /commercial/loss-makers`
- `PATCH /commercial/tasks/{taskId}/billed-amount`, `PATCH /commercial/jobs/{jobId}/billed-amount`

## Dashboards / Reports
- Dashboards: `GET /dashboards/leadership`, `GET /dashboards/operations`, `GET /dashboards/task-governance`, `GET /dashboards/job-operations`, `GET /dashboards/employee-productivity`, `GET /dashboards/client-commercial`, `GET /dashboards/finance`, `GET /dashboards/approvals`, `GET /dashboards/sla`, `GET /dashboards/alerts`, `GET /dashboards/resource-planning`, `GET /dashboards/goals`, `GET /dashboards/launches`
- Reports: `GET /reports`, `GET /reports/{reportCode}/schema`, `POST /reports/{reportCode}/run`, `POST /reports/{reportCode}/export`
