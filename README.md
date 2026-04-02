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
