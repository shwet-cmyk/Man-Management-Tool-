# Edge Cases and Validations

- Tenant mismatch between JWT and `x-tenant-id` header must fail with 403.
- Workflow publish race condition: use optimistic lock (`workflow.version`) and unique constraints.
- Invoice double-post prevention: idempotency key + unique `(tenant_id, period_start, period_end)`.
- SLA escalations across holidays/timezones: calculate using tenant business calendar.
- Notification retries: dead-letter queue after max attempts.
- Search permissions: result filtering by RBAC scope before returning records.
- Webhook replay attacks: timestamp + HMAC validation and nonce cache.
- Sandbox leakage: sandbox workflow versions never selectable in production path.
