# API → BLL → DAL Map (Current additions)

- UX APIs (`modules/ux_analytics/router.py`) → `UxAnalyticsBLL` → `UxAnalyticsDAL`
- Devlogs APIs (`modules/devlogs/router.py`) → `DevlogsBLL` → `DevlogsDAL`
- Audit APIs (`modules/system_audit/router.py`) → `AuditService` → in-memory `entries`
- Automation APIs (`modules/automation/router.py`) → router-level orchestration (pending dedicated BLL/DAL split)
