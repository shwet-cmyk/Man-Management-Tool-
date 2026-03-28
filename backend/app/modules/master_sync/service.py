from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ref_employee import RefEmployee
from app.models.sync_log import SyncLog


@dataclass
class SyncCounters:
    total_fetched: int = 0
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0


class EmployeeSyncService:
    def __init__(self, db: Session, erp_client) -> None:
        self.db = db
        self.erp_client = erp_client

    def sync_employees(self, sync_mode: str = "FULL") -> dict:
        started_at = datetime.utcnow()
        counters = SyncCounters()
        errors: list[str] = []

        try:
            employees = self.erp_client.get_employees()
            counters.total_fetched = len(employees)

            seen_emp_ids: set[int] = set()

            for idx, raw_emp in enumerate(employees):
                try:
                    normalized = self._normalize(raw_emp)
                    if not normalized:
                        counters.skipped += 1
                        continue

                    emp_id = normalized["emp_id"]
                    if emp_id in seen_emp_ids:
                        counters.skipped += 1
                        continue
                    seen_emp_ids.add(emp_id)

                    existing = self.db.get(RefEmployee, emp_id)
                    if existing is None:
                        self.db.add(RefEmployee(**normalized))
                        counters.inserted += 1
                    else:
                        for key, value in normalized.items():
                            setattr(existing, key, value)
                        counters.updated += 1
                except Exception as exc:  # noqa: BLE001
                    counters.failed += 1
                    errors.append(f"row={idx}, error={exc}")

            if sync_mode == "FULL":
                active_ids = list(seen_emp_ids)
                if active_ids:
                    self.db.query(RefEmployee).filter(~RefEmployee.emp_id.in_(active_ids)).update(
                        {RefEmployee.is_active: False, RefEmployee.last_synced_at: datetime.utcnow()},
                        synchronize_session=False,
                    )

            self.db.commit()
            status = "SUCCESS" if counters.failed == 0 else "PARTIAL_SUCCESS"
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            status = "FAILED"
            counters.failed += 1
            errors.append(str(exc))

        self._write_sync_log(sync_mode, status, counters, started_at, errors)

        return {
            "status": status,
            "total_fetched": counters.total_fetched,
            "inserted": counters.inserted,
            "updated": counters.updated,
            "skipped": counters.skipped,
            "failed": counters.failed,
        }

    def _normalize(self, payload: dict) -> dict | None:
        emp_id = payload.get("empId")
        employee_name = payload.get("employeeName")

        if emp_id is None or not employee_name:
            raise ValueError("Missing empId or employeeName")

        company_id = payload.get("companyId")
        if company_id is None:
            raise ValueError("Missing companyId")

        is_active = bool(payload.get("active", 0) == 1)
        monthly_ctc_raw = payload.get("monthlyCTC", 0) or 0
        monthly_ctc = Decimal(str(monthly_ctc_raw))

        hourly_cost = Decimal("0")
        if monthly_ctc > 0:
            hourly_cost = monthly_ctc / Decimal(str(settings.working_hours_per_month))

        return {
            "emp_id": int(emp_id),
            "employee_name": str(employee_name).strip(),
            "company_id": int(company_id),
            "branch_id": int(payload["branchId"]) if payload.get("branchId") is not None else None,
            "department_id": int(payload["departmentId"]) if payload.get("departmentId") is not None else None,
            "monthly_ctc": monthly_ctc,
            "hourly_cost": hourly_cost,
            "is_active": is_active,
            "last_synced_at": datetime.utcnow(),
        }

    def _write_sync_log(
        self,
        sync_mode: str,
        status: str,
        counters: SyncCounters,
        started_at: datetime,
        errors: list[str],
    ) -> None:
        log = SyncLog(
            entity="employee",
            sync_mode=sync_mode,
            status=status,
            total_fetched=counters.total_fetched,
            inserted=counters.inserted,
            updated=counters.updated,
            skipped=counters.skipped,
            failed=counters.failed,
            error_details="\n".join(errors) if errors else None,
            started_at=started_at,
            completed_at=datetime.utcnow(),
        )
        self.db.add(log)
        self.db.commit()


def get_employee_summary(db: Session) -> dict:
    total = db.query(func.count(RefEmployee.emp_id)).scalar() or 0
    active = db.query(func.count(RefEmployee.emp_id)).filter(RefEmployee.is_active.is_(True)).scalar() or 0
    latest = db.query(SyncLog).filter(SyncLog.entity == "employee").order_by(desc(SyncLog.completed_at)).first()
    return {
        "total_employees": total,
        "active_employees": active,
        "last_sync_time": latest.completed_at if latest else None,
    }


def list_ref_employees(db: Session) -> list[RefEmployee]:
    return db.query(RefEmployee).order_by(RefEmployee.employee_name.asc()).all()


def list_sync_logs(db: Session, limit: int = 20) -> list[SyncLog]:
    return (
        db.query(SyncLog)
        .filter(SyncLog.entity == "employee")
        .order_by(desc(SyncLog.completed_at))
        .limit(limit)
        .all()
    )
