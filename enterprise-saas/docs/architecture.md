# Enterprise SaaS Architecture (Zoho + ServiceNow Class)

## Step 1: High-level architecture

```text
                           +-----------------------------+
                           |         Next.js Web         |
                           |  Admin + Agent + Customer   |
                           +--------------+--------------+
                                          |
                                          v
+----------------+              +---------+---------+               +----------------+
| OAuth / SSO    |<-----------> | API Gateway / BFF | <-----------> | Public API     |
| Google/AzureAD |              | (NestJS)           |               | (Rate limited) |
+----------------+              +---------+---------+               +----------------+
                                          |
                           +--------------+--------------+
                           | Tenant Context Middleware   |
                           | RBAC + ABAC + Audit Guard   |
                           +--------------+--------------+
                                          |
      +---------------------+-------------+------------------+----------------------+
      |                     |                                |                      |
      v                     v                                v                      v
+-----+------+     +--------+-------+               +--------+-------+      +-------+------+
| CRM / Core |     | Workflow & SLA |               | Billing Engine |      | Ticketing     |
| Entities   |     | Versioned      |               | Usage Metering |      | + Portal      |
+-----+------+     +--------+-------+               +--------+-------+      +-------+------+
      |                     |                                |                      |
      +----------+----------+----------------------+---------+----------------------+
                 |                                 |
                 v                                 v
       +---------+---------+            +----------+----------+
       | PostgreSQL        |            | Redis + BullMQ      |
       | Row + Schema MT   |            | Cache + Async Jobs  |
       +---------+---------+            +----------+----------+
                 |                                 |
                 v                                 v
       +---------+---------+            +----------+----------+
       | ETL / CDC Jobs    |----------> | Analytics Warehouse |
       | (batch + stream)  |            | + AI feedback loop  |
       +---------+---------+            +---------------------+
                 |
                 v
       +---------+---------+      +--------------------+
       | Notification Hub  |----> | Email/WhatsApp/Push|
       | templates + retry |      +--------------------+
       +-------------------+
```

### Core principles
- API-first contract layer (`/v1/{tenant}/{module}/...`), backward-compatible versioning.
- Multi-tenant data isolation: schema-per-tenant for regulated tenants, row-level isolation for pooled tenants.
- Event-driven side effects (notifications, ledger posting, ETL, AI training updates).
- Auditability by default for all state-changing operations.
- Horizontal scalability: stateless API pods, externalized cache/queue/storage.

## Step 2: Database schema
See `enterprise-saas/db/schema.sql` for full DDL including:
- tenant hierarchy (`tenants`, `branches`, `departments`),
- security (`users`, `roles`, `permissions`, `user_roles`),
- platform modules (tickets, workflows, approvals, CRM, billing),
- metering + ledger + invoices,
- version tables (`workflow_versions`, `approval_rule_versions`),
- audit trail and ETL staging/warehouse tables.

## Step 3: Backend core modules
- `TenancyModule`: resolves tenant/branch/company context from JWT + headers.
- `AuthModule`: JWT + OAuth + SSO entry points.
- `BillingModule`: subscription, usage meter, invoice generation.
- `WorkflowModule`: immutable version graph + sandbox simulation.
- `NotificationsModule`: template render, channel routing, retries.
- `SearchModule`: global federated search adapter (Postgres FTS + optional ES).
- `PublicApiModule`: partner tokens, webhook registration, API usage metering.

## Step 4: API conventions
- URL: `/api/v1/{resource}` for platform and `/api/v1/tenants/{tenantId}/{resource}` for tenant-scoped writes.
- Idempotency required on financial and workflow execution endpoints.
- Correlation IDs mandatory (`x-correlation-id`).
- RFC7807 error objects.

## Step 5: Scaling + deployment
- Kubernetes-ready manifests in `infra/k8s`.
- Dockerized local stack in `infra/docker/docker-compose.yml`.
- Redis/BullMQ workers scaled independently from API pods.
- Read replicas for analytical reads.
- Partitioned usage events table for 1M+ users.
