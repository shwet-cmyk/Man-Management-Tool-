# Worker Coverage Matrix

| Worker | Trigger | Input Source | Output Action | Retry Rule | Failure Logging | Health Check |
|---|---|---|---|---|---|---|
| Scheduler (`run_periodic_jobs`) | app startup | app config | periodic tasks | ⚠️ basic loop | ⚠️ print/log only | ⚠️ implicit |
| SLA recalculation | scheduled | task/ticket/job state | SLA updates/escalations | ⚠️ pending hardening | ⚠️ partial | ⚠️ pending |
| Notification dispatcher | event bus | domain events | in-app notifications | ⚠️ pending backoff policy | ⚠️ partial | ⚠️ pending |
| Automation execution | rule trigger/test | automation rule store | action execution | ⚠️ partial | ⚠️ partial | ⚠️ pending |
| Automation retry/failure | run failure | execution history | retry queue | ✅ duplicate-retry guard | ⚠️ partial | ⚠️ pending |
| UX aggregation | event ingest | ux event store | screen summary metrics | ⚠️ pending batch worker | ⚠️ partial | ⚠️ pending |
| Log aggregation | app/api/job logs | logs sources | devlogs dashboard | ⚠️ pending | ⚠️ partial | ⚠️ pending |
| Help-release sync | release events | release notes/help | help updates | ⚠️ pending | ⚠️ partial | ⚠️ pending |
