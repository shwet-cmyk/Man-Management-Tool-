# Chatbot module scaffold

Layered structure:
- `bal.py`: API-facing orchestration for query/history/quick-prompts.
- `bll.py`: business logic including quick-prompt ranking + RBAC/context filtering.
- `dal.py`: persistence abstraction (in-memory scaffold currently) + prompt seed catalog.
- `router.py`: FastAPI routes mounted at `/api/v1/chatbot`.

## Quick Questions (Smart Prompts) engine
- Context-aware: matches by `module_name` + `screen_key` with global fallback.
- RBAC-aware: filters by user role and allowed intent list.
- Data-driven: filters by user data signals (`pending_approvals`, `delayed_tasks`, `sla_breaches`, `timesheet_overlaps`).
- Action-oriented: each prompt returns `intent_code` + `action_type` and is clickable in UI.
- Relevance sorting: priority + context + usage score.

## API sample
`GET /api/v1/chatbot/quick-prompts?module_name=approvals&screen_key=approval_inbox&user_id=1&language=hi`

Example response:
```json
{
  "prompts": [
    {
      "prompt_id": 3,
      "text": "मेरे pending approvals दिखाओ",
      "intent_code": "GET_PENDING_APPROVALS",
      "action_type": "QUERY",
      "route_path": "/approvals"
    }
  ]
}
```
