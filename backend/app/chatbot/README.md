# Chatbot module scaffold

Layered structure:
- `bal.py`: API-facing orchestration for query/history.
- `bll.py`: business logic to generate route-aware responses.
- `dal.py`: persistence abstraction (in-memory scaffold currently).
- `router.py`: FastAPI routes mounted at `/api/v1/chatbot`.

This scaffold is intentionally lightweight and can be replaced with DB-backed DAL + LLM provider integrations.
