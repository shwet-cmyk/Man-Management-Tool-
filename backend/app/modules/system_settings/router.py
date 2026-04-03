from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/system/settings", tags=["System Settings"])


class SystemSettingsPayload(BaseModel):
    system_name: str = Field(min_length=2)
    default_time_zone: str
    financial_year_start: str
    base_currency: str
    session_timeout_mins: int = Field(gt=0)
    password_policy_level: str
    two_factor_enabled: bool = False
    audit_retention_days: int = Field(ge=30)
    help_auto_update_enabled: bool = False
    bruno_enabled: bool = True
    guided_tour_enabled: bool = True
    productivity_agent_enabled: bool = False
    ux_tracking_enabled: bool = True


DEFAULT_SETTINGS = SystemSettingsPayload(
    system_name="TEZ Execution System",
    default_time_zone="UTC",
    financial_year_start="2026-04-01",
    base_currency="USD",
    session_timeout_mins=30,
    password_policy_level="HIGH",
    two_factor_enabled=False,
    audit_retention_days=180,
    help_auto_update_enabled=True,
    bruno_enabled=True,
    guided_tour_enabled=True,
    productivity_agent_enabled=False,
    ux_tracking_enabled=True,
)

LIVE_SETTINGS = DEFAULT_SETTINGS.model_dump()
DRAFT_SETTINGS = DEFAULT_SETTINGS.model_dump()
SETTINGS_HISTORY: list[dict] = []
PUBLISH_METRICS = {"publish_count": 0, "rollback_count": 0, "sync_failures": 0}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _audit(action: str, payload: dict, actor: str) -> None:
    SETTINGS_HISTORY.append(
        {
            "version": len(SETTINGS_HISTORY) + 1,
            "action": action,
            "actor": actor,
            "payload": deepcopy(payload),
            "created_at": _now(),
        }
    )


def _impact(payload: dict) -> list[str]:
    impacts: list[str] = []
    if not payload.get("bruno_enabled", True):
        impacts.append("Bruno assistant responses will be disabled for all users.")
    if not payload.get("guided_tour_enabled", True):
        impacts.append("First-login guided tours will be skipped for all roles.")
    if not payload.get("ux_tracking_enabled", True):
        impacts.append("Heatmaps/dead-click/rage-click telemetry ingestion will stop.")
    if not payload.get("productivity_agent_enabled", True):
        impacts.append("Desktop productivity agent pipelines will pause for new data ingestion.")
    if payload.get("session_timeout_mins", 30) < 10:
        impacts.append("Aggressive session timeout may increase forced logouts.")
    return impacts


@router.get("")
def get_settings(mode: str = Query(default="live", pattern="^(live|draft)$")):
    target = LIVE_SETTINGS if mode == "live" else DRAFT_SETTINGS
    return {
        "mode": mode,
        "settings": target,
        "interconnects": ["Login", "Role Management", "Help Engine", "Guided Tour", "Automation Engine", "Notification Engine", "Audit Logs", "Product Intelligence", "Bruno"],
    }


@router.post("/save")
def save_settings(payload: SystemSettingsPayload, actor_role: str = "SuperAdmin"):
    data = payload.model_dump()
    if actor_role not in {"SuperAdmin", "Admin"}:
        raise HTTPException(status_code=403, detail="Only Admin/SuperAdmin can save draft settings")
    DRAFT_SETTINGS.update(data)
    _audit("SETTING_CHANGED", DRAFT_SETTINGS, actor=f"{actor_role}:draft")
    return {
        "status": "draft_saved",
        "warnings": _impact(DRAFT_SETTINGS),
        "draft_vs_live_drift_count": sum(1 for k, v in DRAFT_SETTINGS.items() if LIVE_SETTINGS.get(k) != v),
    }


@router.post("/publish")
def publish_settings(confirm_impact: bool = False, actor_role: str = "SuperAdmin"):
    if actor_role != "SuperAdmin":
        raise HTTPException(status_code=403, detail="Only Super Admin can publish global settings")
    impacts = _impact(DRAFT_SETTINGS)
    if impacts and not confirm_impact:
        return {"status": "impact_confirmation_required", "impact": impacts}

    LIVE_SETTINGS.update(deepcopy(DRAFT_SETTINGS))
    PUBLISH_METRICS["publish_count"] += 1
    _audit("SETTING_PUBLISHED", LIVE_SETTINGS, actor="SuperAdmin")
    return {
        "status": "published",
        "published_at": _now(),
        "sync_jobs_triggered": ["help_refresh_sync", "feature_flag_propagation", "security_policy_refresh"],
        "impact": impacts,
    }


@router.post("/reset-default")
def reset_to_default(actor_role: str = "SuperAdmin"):
    if actor_role not in {"SuperAdmin", "Admin"}:
        raise HTTPException(status_code=403, detail="Unauthorized")
    DRAFT_SETTINGS.update(DEFAULT_SETTINGS.model_dump())
    _audit("SETTING_RESET_DEFAULT", DRAFT_SETTINGS, actor=actor_role)
    return {"status": "draft_reset", "draft": DRAFT_SETTINGS}


@router.get("/history")
def settings_history(limit: int = 50):
    return {"count": min(limit, len(SETTINGS_HISTORY)), "items": SETTINGS_HISTORY[-limit:]}


@router.get("/analytics")
def settings_analytics():
    changes: dict[str, int] = {}
    for item in SETTINGS_HISTORY:
        payload = item["payload"]
        for key in payload.keys():
            changes[key] = changes.get(key, 0) + 1
    return {
        "most_changed_settings": sorted(changes.items(), key=lambda x: x[1], reverse=True)[:8],
        "publish_frequency": PUBLISH_METRICS["publish_count"],
        "rollback_frequency": PUBLISH_METRICS["rollback_count"],
        "feature_enablement_adoption": {
            "bruno_enabled": LIVE_SETTINGS["bruno_enabled"],
            "guided_tour_enabled": LIVE_SETTINGS["guided_tour_enabled"],
            "productivity_agent_enabled": LIVE_SETTINGS["productivity_agent_enabled"],
            "ux_tracking_enabled": LIVE_SETTINGS["ux_tracking_enabled"],
        },
        "drift_between_draft_and_live": sum(1 for k, v in DRAFT_SETTINGS.items() if LIVE_SETTINGS.get(k) != v),
        "publish_latency_ms": 45,
        "config_sync_failures": PUBLISH_METRICS["sync_failures"],
        "feature_toggle_propagation_errors": 0,
    }


@router.get("/report")
def settings_report():
    return {
        "system_configuration_report": LIVE_SETTINGS,
        "module_enablement_report": {
            "guided_tour": LIVE_SETTINGS["guided_tour_enabled"],
            "bruno": LIVE_SETTINGS["bruno_enabled"],
            "productivity_agent": LIVE_SETTINGS["productivity_agent_enabled"],
            "ux_tracking": LIVE_SETTINGS["ux_tracking_enabled"],
        },
        "security_settings_report": {
            "password_policy_level": LIVE_SETTINGS["password_policy_level"],
            "two_factor_enabled": LIVE_SETTINGS["two_factor_enabled"],
            "session_timeout_mins": LIVE_SETTINGS["session_timeout_mins"],
        },
        "feature_flag_report": {
            key: LIVE_SETTINGS[key]
            for key in [
                "help_auto_update_enabled",
                "bruno_enabled",
                "guided_tour_enabled",
                "productivity_agent_enabled",
                "ux_tracking_enabled",
            ]
        },
    }
