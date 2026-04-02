from __future__ import annotations

from collections.abc import Callable

from fastapi import Header, HTTPException


class PermissionChecker:
    def __init__(self, required_permission: str) -> None:
        self.required_permission = required_permission

    def __call__(
        self,
        x_role: str | None = Header(default=None),
        x_permissions: str | None = Header(default=None),
    ) -> None:
        if (x_role or "").lower() == "admin":
            return

        permission_set = {
            p.strip().lower()
            for p in (x_permissions or "").split(",")
            if p.strip()
        }
        if self.required_permission.lower() not in permission_set:
            raise HTTPException(status_code=403, detail="Insufficient permissions")


def require_permission(required_permission: str) -> Callable[..., None]:
    return PermissionChecker(required_permission)
