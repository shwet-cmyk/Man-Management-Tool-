# SRS — Desktop Activity Agent (Phase 1)

## 1) Module Name
Desktop Activity Agent

## 2) Objective
Lightweight secure telemetry agent on company-managed desktops to capture operating-system level activity and sync to TEZ backend for productivity classification, policy enforcement, dashboards, reports, and alerts.

## 3) Non-Surveillance Boundaries
The agent collects telemetry (events + context) and **does not** collect:
- keystroke content
- clipboard content (phase 1)
- microphone/webcam data
- full continuous video recording by default

## 4) Supported Platforms
- Phase 1: Windows
- Phase 2: macOS (optional)
- Linux: optional by internal demand

## 5) Agent Components
- Bootstrap Service
- Device Registration Service
- Activity Collector
- Active Window Tracker
- Browser URL Tracker
- System State Tracker
- Idle Detection Service
- Policy Sync Service
- Local Queue + Retry
- Screenshot Capture (policy-driven, optional)
- Secure Sync Uploader
- Self Health Monitor

## 6) Captured Event Types
- USER_INPUT
- ACTIVE_WINDOW_CHANGED
- URL_CHANGED
- SESSION_LOCKED
- SESSION_UNLOCKED
- SYSTEM_SLEEP
- SYSTEM_WAKE
- SYSTEM_SHUTDOWN
- SYSTEM_RESTART
- AGENT_HEARTBEAT

## 7) Core Data Fields
- device_id
- user_id
- event_timestamp
- event_type
- active_app_name
- active_executable
- active_window_title
- active_domain / active_url
- metadata_json

## 8) Idle Detection Rule
Idle is computed from missing keyboard/mouse inputs beyond policy threshold.
- lock -> locked time (not idle)
- sleep -> hibernate time (not idle)
- shutdown/reboot -> system state, not idle

## 9) Policy Sync Contract
Agent should regularly fetch policy snapshot with:
- idle threshold
- screenshot policy
- block/warn behavior
- productive thresholds
- sync intervals/version metadata

## 10) Offline + Retry
- local queued events preserved with timestamps
- retry with backoff
- delete only after ACK
- idempotent sync envelope recommended

## 11) Security + Transparency
- token auth
- HTTPS only
- encrypted token/queue where possible
- signed binaries recommended
- employee-visible policy disclosures required

## 12) Backend Integration (Implemented API Surface)
Current backend productivity routes include agent and admin/reporting APIs under `/api/v1/productivity/*`:
- `/agent/register`, `/agent/heartbeat`, `/agent/sync`
- `/agent/health`, `/agent/version-report`
- policy, summaries, breaches, screenshots, widgets, masters

## 13) Data Retention
- raw activity log: 90 days
- screenshot evidence: policy-driven (default 90)
- summaries: perpetual

## 14) Alternate Flows
- No internet -> local queue + retry
- Invalid token -> reject + auth failure state
- Backend unavailable -> queue + health anomaly
- Outdated agent -> version report + admin flag
- Unregistered device -> sync blocked

## 15) Traceability Matrix (SRS to Backend)
- Device registration -> `POST /productivity/agent/register`
- Heartbeat/health -> `POST /productivity/agent/heartbeat`, `GET /productivity/agent/health`
- Activity ingestion -> `POST /productivity/agent/sync`
- Policy distribution -> `GET /productivity/policy/current`
- Breaches -> `GET /productivity/policy-breaches`
- Screenshots metadata -> `GET /productivity/screenshots`
- Dashboards -> `GET /productivity/dashboard/widgets`

## 16) Phase 1 Admin Web Screens (Required)
- Device Master
- Agent Health Dashboard
- Agent Version Report
- Sync Failure/Offline Report
- Policy Assignment
- Screenshot Evidence View
- Policy Breach View

## 17) Non-Negotiable Rules
- no manual idle/productive entry
- no keystroke/mic/camera capture
- no stealth design intent
- no silent data loss
- all policy/health failures auditable
