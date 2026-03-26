# Monorepo Structure

```text
enterprise-saas/
  apps/
    api/                 # NestJS API (tenant-aware)
      src/
        common/          # middleware, guards, decorators
        modules/         # bounded contexts (billing, workflow, ...)
        queue/           # BullMQ consumers/producers
        etl/             # batch + streaming jobs
    web/                 # Next.js frontend
  db/
    schema.sql           # PostgreSQL DDL
  packages/
    contracts/           # API contracts and conventions
    config/              # shared eslint/tsconfig/env definitions
  infra/
    docker/
    k8s/
  tests/
    *.spec.ts            # unit + integration tests
```
