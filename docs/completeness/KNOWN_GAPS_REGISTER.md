# Known Gaps Register

1. Persistent DB-backed repositories are still incomplete for several newly added screen contracts; current implementations are in-memory scaffolds.
2. Full RBAC middleware enforcement per endpoint is not uniformly applied across all new endpoints.
3. Material-action audit emission is partial for new UX/devlogs/automation endpoints.
4. Dedicated integration/unit tests for screens 32-40 contract endpoints are not yet present.
5. Worker-level retry/backoff and health endpoints need formalization.
6. Screen completeness matrices are currently focused on new Product & Developer Intelligence scope, not all modules.
