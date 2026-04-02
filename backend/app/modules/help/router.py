from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, HTTPException, Query

from app.modules.help.seed import HELP_CONTENT_SEED

router = APIRouter(prefix="/help", tags=["Contextual Help"])


@lru_cache(maxsize=1)
def _active_help_map() -> dict[str, dict]:
    return {row["screen_key"]: row for row in HELP_CONTENT_SEED if row.get("is_active")}


@router.get("/{screen_key}")
def get_help_content(screen_key: str):
    row = _active_help_map().get(screen_key)
    if not row:
        return {
            "screen_key": screen_key,
            "title": "Help content not configured",
            "description": "Help content not yet configured for this screen",
            "when_to_use": "Use this screen according to module workflow.",
            "steps_json": [],
            "rules_json": [],
            "errors_json": [],
            "tips_json": [],
            "is_active": False,
        }
    return row


@router.get("")
def list_help_content(module_name: str | None = None, q: str | None = Query(default=None, description="Search in title/description/screen_key")):
    rows = list(_active_help_map().values())
    if module_name:
        rows = [r for r in rows if r["module_name"].lower() == module_name.lower()]
    if q:
        q_low = q.lower()
        rows = [r for r in rows if q_low in r["screen_key"].lower() or q_low in r["title"].lower() or q_low in r["description"].lower()]
    return {"count": len(rows), "items": rows}


@router.get("/route/map")
def route_map():
    return {"mappings": [{"route_path": r["route_path"], "screen_key": r["screen_key"], "module_name": r["module_name"]} for r in _active_help_map().values()]}


@router.get("/route/resolve")
def resolve_by_route(path: str):
    for row in _active_help_map().values():
        if row["route_path"] == path:
            return row
    raise HTTPException(status_code=404, detail="No help mapping found for route")
