# API Coverage Matrix (Screens 32-40)

| Module | Endpoint | Method | Auth | Validation | BLL | DAL | Audit | Test |
|---|---|---|---|---|---|---|---|---|
| UX | `/api/ux/summary` | GET | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| UX | `/api/ux/filter` | POST | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| UX | `/api/ux/screen-detail/{id}` | GET | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| UX | `/api/ux/heatmap/{id}` | GET | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| UX | `/api/ux/compare` | POST | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| UX | `/api/ux/create-ticket` | POST | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| Devlogs | `/api/devlogs/dashboard` | GET | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| Devlogs | `/api/devlogs/search` | POST | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| Devlogs | `/api/devlogs/detail/{id}` | GET | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| Devlogs | `/api/devlogs/notes/{id}` | POST | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| Audit | `/api/audit/list` | GET | ⚠️ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Audit | `/api/audit/search` | POST | ⚠️ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Audit | `/api/audit/detail/{id}` | GET | ⚠️ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Audit | `/api/audit/export` | POST | ⚠️ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Automation | `/api/automation/list` | GET | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| Automation | `/api/automation/create` | POST | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| Automation | `/api/automation/update/{id}` | PUT | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| Automation | `/api/automation/test/{id}` | POST | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| Automation | `/api/automation/history/{id}` | GET | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| Automation | `/api/automation/retry/{runId}` | POST | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
