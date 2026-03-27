# API Design (REST)

## Naming conventions
- Resource nouns, lowercase kebab-case.
- Tenant-scoped resources under `/api/v1/tenants/{tenantId}/...`.
- Bulk actions under `/actions/{verb}` only when not representable as resource state.

## Sample endpoints
- `POST /api/v1/tenants/{tenantId}/billing/usage-events`
- `GET /api/v1/tenants/{tenantId}/billing/invoices/{periodStart}/{periodEnd}`
- `POST /api/v1/tenants/{tenantId}/workflows/{workflowKey}/versions`
- `POST /api/v1/tenants/{tenantId}/workflows/{workflowKey}/simulate`
- `GET /api/v1/tenants/{tenantId}/search?q=&module=`
- `POST /api/v1/public/webhooks/{provider}`

## Response envelope
```json
{
  "data": {},
  "meta": { "correlationId": "...", "tenantId": "..." },
  "errors": []
}
```

## Error format
RFC7807 `application/problem+json`.
