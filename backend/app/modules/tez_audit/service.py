from __future__ import annotations

import json

from app.models.audit_logs_v2 import AuditLogV2
from app.modules.tez_audit.schemas import TezAuditLogRequest

SENSITIVE_FIELDS = {"password", "token", "secret", "api_key"}


class TezAuditService:
    def __init__(self, db):
        self.db = db

    def log_event(self, payload: TezAuditLogRequest):
        row = AuditLogV2(
            entity_type=payload.entity_type.upper(),
            entity_id=payload.entity_id,
            action=payload.action.upper(),
            old_data=json.dumps(self._mask(payload.old_data), default=str),
            new_data=json.dumps(self._mask(payload.new_data), default=str),
            user_id=payload.user_id,
            ip_address=payload.ip_address,
            attempt_status="AUTHORIZED" if payload.authorized else "DENIED",
        )
        self.db.add(row)
        self.db.commit()
        return {"status": "logged", "audit_id": row.id}

    def get_entity_logs(self, entity_type: str, entity_id: str):
        rows = (
            self.db.query(AuditLogV2)
            .filter(AuditLogV2.entity_type == entity_type.upper(), AuditLogV2.entity_id == entity_id)
            .order_by(AuditLogV2.created_at.desc())
            .all()
        )
        return [
            {
                "id": row.id,
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "action": row.action,
                "user_id": row.user_id,
                "attempt_status": row.attempt_status,
                "created_at": row.created_at,
            }
            for row in rows
        ]

    def soft_delete_with_audit(self, entity_type: str, entity_id: str, user_id: str):
        return self.log_event(
            TezAuditLogRequest(
                entity_type=entity_type,
                entity_id=entity_id,
                action="DELETE",
                user_id=user_id,
                old_data={"is_deleted": False},
                new_data={"is_deleted": True},
                authorized=True,
            )
        )

    def _mask(self, data: dict):
        masked = {}
        for k, v in data.items():
            masked[k] = "***MASKED***" if k.lower() in SENSITIVE_FIELDS else v
        return masked
