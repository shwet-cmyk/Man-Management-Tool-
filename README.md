# TEZ Execution System

Fresh implementation baseline for an audit-first execution control engine.

## Stack
- Frontend: React + Vite
- Backend: FastAPI (Python)
- Database target: MSSQL (to be wired in next increment)

## Run backend
```bash
pip install fastapi pydantic pydantic-settings uvicorn email-validator
PYTHONPATH=backend uvicorn app.main:app --reload --port 8000
```

Docs:
- Swagger UI: `http://localhost:8000/api-docs`
- OpenAPI JSON: `http://localhost:8000/api/v1/openapi.json`

## Run frontend
```bash
cd frontend
npm install
npm run dev
```

## Baseline docs
- `docs/SRS_TEZ_EXECUTION_SYSTEM_v3.md`
- `docs/ENDPOINT_INVENTORY_API_V1.md`


## Implemented modules
- Login
- RBAC Master
- User Master
- Company Master
- Governance
- Interconnect Master
- Dashboard Engine
- Global Analytics Engine
- Global Reporting Engine
- Project Module
- Status Engine
- Ticket Module
- Task Management Module
- Approval Engine
- Automation Engine
- Algorithm + Calendar Intelligence
- Task Master + Task Group
- Governance Dashboard
- Gamification + Appraisal Engine
- Collaboration Engine
- Unified Notification Engine
- System Audit Module
