# Tez Mobile (Design-First Package)

This folder contains the production-ready UI/UX architecture deliverables for the Tez mobile app focused on:
- Approvals
- Chat
- Notifications

## Deliverables
- `docs/UI_UX_SYSTEM_SPEC.md` — complete design system, IA, screen behavior, components, states, security UX.
- `docs/NAVIGATION_MAP.md` — navigation hierarchy, deep links, badge model.

## Proposed source architecture (for implementation phase)
```
mobile/
  src/
    app/
    components/
    screens/
    navigation/
    services/
    store/
    hooks/
    utils/
    types/
    theme/
    modules/
      approvals/
      chat/
      notifications/
    security/
```

## Scope note
This commit intentionally focuses on **design and UX architecture only** (no backend changes and no mobile runtime code).
