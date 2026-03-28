# API Module Guide (UI/UX, Endpoint Inventory, RBAC Tree, OpenAPI)

## 1) API Module UI/UX command
Use this when you want to open the frontend and validate API-module related screens/workflows.

```bash
cd frontend && npm install && npm run dev
```

Then open the local URL shown by Vite (typically `http://localhost:5173`).

For backend API during UI testing:

```bash
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 2) Actual endpoint inventory by module
Generate inventory directly from source registrations in `backend/app/main.py` and each module router:

```bash
python backend/scripts/api_module_inventory.py --format markdown > backend/docs/api_module_inventory.md
python backend/scripts/api_module_inventory.py --format json > backend/docs/api_module_inventory.json
```

## 3) RBAC tree for API module
Seed and fetch the RBAC permission tree through APIs:

```bash
curl -X POST http://localhost:8000/api/permissions/tree/seed
curl http://localhost:8000/api/permissions/tree
```

Tree shape (root modules and key action families):

- `JOBS`
  - CRUD + workflow actions (entry, timesheet, voucher/date)
  - communication (email/document)
  - print/reports
  - financial-sensitive actions (invoice/proforma/view amount)
  - import/export + bulk assignment
- `TIMESHEET`
  - CRUD + voucher/date + communication + reports + export
- `MASTER_CUSTOMER`
  - CRUD + extra addresses + services + communication
  - financial-sensitive actions (service rate, ledger, price/discount uploads, confirmation)
  - report/export/bulk upload actions
- `MASTER_COMPANY`
- `MASTER_BRANCH`
- `MASTER_DEPARTMENT`
- `MASTER_EMPLOYEE`

> Source of truth for the RBAC tree is `RbacService._tree_seed_rows()` plus `GET /api/permissions/tree`.

## 4) Swagger / OpenAPI generation command
### Interactive docs
```bash
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Then open:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

### Export OpenAPI JSON to file
```bash
curl http://localhost:8000/openapi.json -o backend/docs/openapi.json
```
