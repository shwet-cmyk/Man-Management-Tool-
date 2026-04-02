from __future__ import annotations

import json

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.task_audit_log import TaskAuditLog
from app.models.wm_audit_field_change import WmAuditFieldChange
from app.models.wm_entity_version import WmEntityVersion
from app.modules.audit.schemas import AuditLogCreateRequest


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log_event(self, payload: AuditLogCreateRequest):
        log_row = TaskAuditLog(
            entity_name=payload.entity_type,
            entity_id=payload.entity_id,
            action=payload.action,
            details=json.dumps(payload.new_data, default=str),
            created_by=payload.performed_by,
            ip_address=payload.ip_address,
            device_info=payload.device_info,
            source=payload.source,
        )
        self.db.add(log_row)
        self.db.flush()

        changes = self._diff(payload.old_data, payload.new_data)
        for change in changes:
            self.db.add(
                WmAuditFieldChange(
                    audit_log_id=log_row.id,
                    field_name=change["field_name"],
                    old_value=change["old_value"],
                    new_value=change["new_value"],
                )
            )

        next_version = self._next_version(payload.entity_type, payload.entity_id)
        self.db.add(
            WmEntityVersion(
                entity_type=payload.entity_type,
                entity_id=payload.entity_id,
                version_no=next_version,
                snapshot_json=json.dumps(payload.new_data, default=str),
            )
        )
        self.db.commit()
        return {"audit_log_id": log_row.id, "field_change_count": len(changes), "version_no": next_version}

    def get_audit_logs(self, entity_type: str, entity_id: int):
        rows = (
            self.db.query(TaskAuditLog)
            .filter(TaskAuditLog.entity_name == entity_type, TaskAuditLog.entity_id == entity_id)
            .order_by(TaskAuditLog.created_on.desc())
            .all()
        )
        return [
            {
                "audit_log_id": x.id,
                "entity_type": x.entity_name,
                "entity_id": x.entity_id,
                "action": x.action,
                "performed_by": x.created_by,
                "performed_at": x.created_on,
                "ip_address": x.ip_address,
                "device_info": x.device_info,
                "source": x.source,
            }
            for x in rows
        ]

    def get_field_changes(self, audit_log_id: int):
        rows = self.db.query(WmAuditFieldChange).filter(WmAuditFieldChange.audit_log_id == audit_log_id).all()
        return [
            {
                "audit_field_change_id": x.audit_field_change_id,
                "field_name": x.field_name,
                "old_value": x.old_value,
                "new_value": x.new_value,
            }
            for x in rows
        ]

    def get_version_snapshot(self, entity_type: str, entity_id: int, version_no: int):
        row = (
            self.db.query(WmEntityVersion)
            .filter(WmEntityVersion.entity_type == entity_type, WmEntityVersion.entity_id == entity_id, WmEntityVersion.version_no == version_no)
            .first()
        )
        if not row:
            raise HTTPException(status_code=404, detail="Entity version not found")
        return {
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "version_no": row.version_no,
            "snapshot": json.loads(row.snapshot_json),
            "created_on": row.created_on,
        }

    @staticmethod
    def _diff(old_data: dict, new_data: dict):
        all_keys = set(old_data.keys()) | set(new_data.keys())
        changes = []
        for key in sorted(all_keys):
            old_val = old_data.get(key)
            new_val = new_data.get(key)
            if old_val != new_val:
                changes.append(
                    {
                        "field_name": key,
                        "old_value": None if old_val is None else str(old_val),
                        "new_value": None if new_val is None else str(new_val),
                    }
                )
        return changes

    def _next_version(self, entity_type: str, entity_id: int):
        row = (
            self.db.query(WmEntityVersion)
            .filter(WmEntityVersion.entity_type == entity_type, WmEntityVersion.entity_id == entity_id)
            .order_by(WmEntityVersion.version_no.desc())
            .first()
        )
        return int(row.version_no) + 1 if row else 1
