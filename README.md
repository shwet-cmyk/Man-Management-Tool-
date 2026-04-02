# TEZ Execution System — Local Development Stack

This repository now includes a **one-command local environment** for:
- FastAPI backend API
- WebSocket gateway service
- Celery worker service
- Redis event bus
- MSSQL database (schema + seed)
- React frontend
- Nginx reverse proxy

## Setup (5 steps max)
1. Copy env file: `cp .env.example .env`
2. Start everything: `make dev` (or `docker compose up --build`)
3. Open frontend: `http://localhost:3000`
4. Open API docs (via nginx): `http://localhost:8080/api/api-docs`
5. Validate health: `http://localhost:8080/api/health` and `http://localhost:8080/api/ready`

## Folder structure
- `backend/` FastAPI app, workers, schema, seed SQL, Postman collection.
- `websocket-service/` dedicated WS gateway (transport-only + Redis pub/sub).
- `frontend/` React app.
- `devops/` Dockerfiles + nginx config.
- `docker-compose.yml` full local orchestration.
- `Makefile` lifecycle commands (`dev`, `reset`, `seed`).

## How to run
```bash
make dev
```

### Useful lifecycle commands
```bash
make reset   # stop stack and remove volumes
make seed    # rerun DB schema + seed
```

## How to debug
- Backend logs: `docker compose logs -f backend-api`
- Worker logs: `docker compose logs -f worker-service`
- WebSocket logs: `docker compose logs -f websocket-service`
- DB health: `docker compose ps` (check `mssql` healthy)

## Common issues
- **MSSQL password policy failure**: ensure `MSSQL_SA_PASSWORD` is complex (uppercase/lowercase/number/symbol).
- **Port conflict**: if 3000/8000/8080/1433 already used, stop conflicting processes or remap ports.
- **Frontend blank on boot**: wait until `npm ci` finishes inside `frontend` container.
- **Seed rerun needed**: run `make seed` after `make reset`.

## Test assets
- Postman collection: `backend/tests/postman/tez-local.postman_collection.json`
- WebSocket test client: `tools/ws_test_client.py`

## Contextual assistant UX
- Chatbot is now exposed as a **global floating assistant** in the frontend (not as a sidebar module entry).
- Assistant sends route/screen context (`route_path`, `screen_key`, `module_name`) to backend `/api/v1/chatbot/query`.
- Backend includes BAL/BLL/DAL scaffold under `backend/app/chatbot/` with session history endpoint.
- Global assistant includes dynamic **Quick Questions (Smart Prompts)** chips with context/RBAC/data-driven filtering and click-to-query behavior.

- Added Productivity & Activity Intelligence backend module (`/api/v1/productivity/*`) for device registration, activity ingestion, policy controls, summaries, breach tracking, and dashboard/report feeds.

- Added Product Intelligence & UX Optimization APIs (`/api/v1/product-intelligence/*`) for telemetry ingestion, friction analytics, AI UX suggestions, release notes, and help-refresh orchestration.
