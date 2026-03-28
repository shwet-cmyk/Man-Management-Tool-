from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from app.integrations.tez_erp_client import TezERPClient
from app.models.task_audit_log import TaskAuditLog
from app.models.wm_billing_configuration import WmBillingConfiguration
from app.models.wm_billing_document_link import WmBillingDocumentLink
from app.models.wm_billing_readiness import WmBillingReadiness
from app.models.wm_billing_status_history import WmBillingStatusHistory
from app.models.wm_expense_claim import WmExpenseClaim
from app.models.wm_job import WmJob
from app.models.wm_task import WmTask
from app.models.wm_timesheet import WmTimesheet
from app.modules.billing.schemas import (
    BillingConfigureRequest,
    InvoiceRequest,
    MarkReadyForBillingRequest,
    ProformaRequest,
    RemoveReadinessRequest,
)


class BillingService:
    def __init__(self, db: Session):
        self.db = db
        self.tez_client = TezERPClient()

    def configure_billing(self, payload: BillingConfigureRequest, user_id: int = 1) -> dict:
        job, task = self._validate_entity(payload.entity_type, payload.job_id, payload.task_id)

        if not self.tez_client.master_exists("customer", payload.customer_id):
            raise HTTPException(status_code=422, detail="Customer missing or inactive")

        if not payload.billable_flag and payload.billing_model != "NON_BILLABLE":
            raise HTTPException(status_code=422, detail="Non-billable entity must use NON_BILLABLE model")

        if payload.billing_model == "FIXED_FEE" and (payload.fixed_billing_amount is None or payload.fixed_billing_amount < 0):
            raise HTTPException(status_code=422, detail="Fixed billing amount is required for FIXED_FEE")

        if payload.entity_type == "TASK" and task and payload.job_id and task.job_id != payload.job_id:
            raise HTTPException(status_code=422, detail="Task does not belong to selected job")

        config = self._get_configuration(payload.entity_type, payload.job_id, payload.task_id)
        now = datetime.utcnow()
        status = "Billable" if payload.billable_flag else "Not Billable"

        try:
            if config:
                config.customer_id = payload.customer_id
                config.billable_flag = payload.billable_flag
                config.billing_model = payload.billing_model
                config.fixed_billing_amount = payload.fixed_billing_amount
                config.billing_status = status
                config.billing_remarks = payload.billing_remarks
                config.updated_by = user_id
                config.updated_on = now
            else:
                self.db.add(
                    WmBillingConfiguration(
                        entity_type=payload.entity_type,
                        job_id=payload.job_id,
                        task_id=payload.task_id,
                        customer_id=payload.customer_id,
                        billable_flag=payload.billable_flag,
                        billing_model=payload.billing_model,
                        fixed_billing_amount=payload.fixed_billing_amount,
                        billing_status=status,
                        billing_remarks=payload.billing_remarks,
                        created_by=user_id,
                    )
                )

            self.db.add(
                TaskAuditLog(
                    entity_name="wm_billing_configuration",
                    entity_id=payload.task_id or payload.job_id or 0,
                    action="CONFIGURE_BILLING",
                    details=f"entity={payload.entity_type};billable_flag={payload.billable_flag};billing_model={payload.billing_model};status={status}",
                    created_by=user_id,
                )
            )
            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Billing configuration update failed: {exc}") from exc

        return {
            "status": "SUCCESS",
            "entity_type": payload.entity_type,
            "billing_status": status,
            "message": "Billing configuration updated successfully",
        }

    def mark_ready_for_billing(self, payload: MarkReadyForBillingRequest, user_id: int = 1) -> dict:
        self._validate_entity(payload.entity_type, payload.job_id, payload.task_id)
        config = self._get_configuration(payload.entity_type, payload.job_id, payload.task_id)
        if not config or not config.billable_flag:
            raise HTTPException(status_code=422, detail="Entity is not billable")
        if config.billing_model == "NON_BILLABLE":
            raise HTTPException(status_code=422, detail="NON_BILLABLE entity cannot be marked ready")

        if config.billing_model in {"TIME_MATERIAL", "RETAINER"}:
            included_hours, included_expense = self._calculate_pools(payload.entity_type, payload.job_id, payload.task_id)
            if included_hours <= 0 and included_expense <= 0:
                raise HTTPException(status_code=422, detail="No approved billable time or recoverable expense available")
        else:
            included_hours, included_expense = Decimal("0"), Decimal("0")

        readiness = self._get_readiness(payload.entity_type, payload.job_id, payload.task_id)
        now = datetime.utcnow()
        try:
            if readiness:
                readiness.ready_for_billing_flag = True
                readiness.ready_for_billing_date = now
                readiness.included_billable_hours = included_hours
                readiness.included_recoverable_expense = included_expense
                readiness.billing_status = "Ready for Billing"
                readiness.billing_remarks = payload.billing_remarks
                readiness.marked_by = user_id
                readiness.marked_on = now
                readiness.updated_by = user_id
                readiness.updated_on = now
            else:
                self.db.add(
                    WmBillingReadiness(
                        entity_type=payload.entity_type,
                        job_id=payload.job_id,
                        task_id=payload.task_id,
                        ready_for_billing_flag=True,
                        ready_for_billing_date=now,
                        included_billable_hours=included_hours,
                        included_recoverable_expense=included_expense,
                        billing_status="Ready for Billing",
                        billing_remarks=payload.billing_remarks,
                        marked_by=user_id,
                    )
                )

            config.billing_status = "Ready for Billing"
            config.updated_by = user_id
            config.updated_on = now

            self.db.add(
                TaskAuditLog(
                    entity_name="wm_billing_readiness",
                    entity_id=payload.task_id or payload.job_id or 0,
                    action="MARK_READY_FOR_BILLING",
                    details=f"entity={payload.entity_type};hours={included_hours};expense={included_expense}",
                    created_by=user_id,
                )
            )
            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Mark ready for billing failed: {exc}") from exc

        return {
            "status": "SUCCESS",
            "entity_type": payload.entity_type,
            "billing_status": "Ready for Billing",
            "included_billable_hours": included_hours,
            "included_recoverable_expense": included_expense,
            "message": "Marked ready for billing successfully",
        }

    def remove_readiness(self, payload: RemoveReadinessRequest, user_id: int = 1) -> dict:
        self._validate_entity(payload.entity_type, payload.job_id, payload.task_id)
        config = self._get_configuration(payload.entity_type, payload.job_id, payload.task_id)
        if not config:
            raise HTTPException(status_code=404, detail="Billing configuration not found")

        readiness = self._get_readiness(payload.entity_type, payload.job_id, payload.task_id)
        if not readiness:
            raise HTTPException(status_code=404, detail="Billing readiness not found")

        try:
            readiness.ready_for_billing_flag = False
            readiness.billing_status = "Billable" if config.billable_flag else "Not Billable"
            readiness.billing_remarks = payload.billing_remarks
            readiness.updated_by = user_id
            readiness.updated_on = datetime.utcnow()

            config.billing_status = "Billable" if config.billable_flag else "Not Billable"
            config.updated_by = user_id
            config.updated_on = datetime.utcnow()

            self.db.add(
                TaskAuditLog(
                    entity_name="wm_billing_readiness",
                    entity_id=payload.task_id or payload.job_id or 0,
                    action="REMOVE_BILLING_READINESS",
                    details=f"entity={payload.entity_type};status={config.billing_status}",
                    created_by=user_id,
                )
            )
            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Remove billing readiness failed: {exc}") from exc

        return {
            "status": "SUCCESS",
            "entity_type": payload.entity_type,
            "billing_status": config.billing_status,
            "message": "Billing readiness removed successfully",
        }

    def process_proforma(self, payload: ProformaRequest, user_id: int = 1) -> dict:
        config, readiness = self._validate_billable_ready(payload.entity_type, payload.job_id, payload.task_id)
        reference_no = (payload.proforma_no or "").strip()
        reference_id = payload.proforma_id

        if payload.action_type == "LINK_EXISTING" and not reference_no:
            raise HTTPException(status_code=422, detail="proforma_no is required when linking existing document")
        if payload.action_type == "CREATE":
            reference_no = self._generate_reference_no("PRO")

        self._ensure_unique_reference(reference_no)
        old_status = config.billing_status
        new_status = "Proforma Created"

        try:
            self.db.add(
                WmBillingDocumentLink(
                    entity_type=payload.entity_type,
                    job_id=payload.job_id,
                    task_id=payload.task_id,
                    billing_reference_type=f"{'INTERNAL' if payload.action_type == 'CREATE' else 'EXTERNAL'}_PROFORMA",
                    billing_reference_id=reference_id,
                    billing_reference_no=reference_no,
                    billed_amount=Decimal("0"),
                    billing_status=new_status,
                    included_billable_hours=readiness.included_billable_hours,
                    included_recoverable_expense=readiness.included_recoverable_expense,
                    billing_remarks=payload.billing_remarks,
                    created_by=user_id,
                )
            )
            self._record_status_change(
                payload.entity_type,
                payload.job_id,
                payload.task_id,
                old_status,
                new_status,
                f"{payload.action_type}_PROFORMA",
                reference_no,
                None,
                payload.billing_remarks,
                user_id,
            )
            config.billing_status = new_status
            config.updated_by = user_id
            config.updated_on = datetime.utcnow()
            self.db.add(
                TaskAuditLog(
                    entity_name="wm_billing_document_link",
                    entity_id=payload.task_id or payload.job_id or 0,
                    action=f"{payload.action_type}_PROFORMA",
                    details=f"entity={payload.entity_type};reference_no={reference_no}",
                    created_by=user_id,
                )
            )
            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Proforma processing failed: {exc}") from exc

        return {
            "status": "SUCCESS",
            "entity_type": payload.entity_type,
            "proforma_no": reference_no,
            "billing_status": new_status,
            "message": "Proforma created successfully" if payload.action_type == "CREATE" else "Proforma linked successfully",
        }

    def process_invoice(self, payload: InvoiceRequest, user_id: int = 1) -> dict:
        config, readiness = self._validate_billable_ready(payload.entity_type, payload.job_id, payload.task_id)
        reference_no = (payload.invoice_no or "").strip()
        reference_id = payload.invoice_id

        if payload.action_type == "LINK_EXISTING" and not reference_no:
            raise HTTPException(status_code=422, detail="invoice_no is required when linking existing document")
        if payload.action_type == "CREATE":
            reference_no = self._generate_reference_no("INV")

        self._ensure_unique_reference(reference_no)

        recommended = self._recommended_amount(config, readiness)
        billed_total = self._total_billed(payload.entity_type, payload.job_id, payload.task_id)
        billed_amount = payload.billed_amount if payload.billed_amount is not None else (recommended - billed_total)
        billed_amount = Decimal(str(billed_amount or 0))
        if billed_amount <= 0:
            raise HTTPException(status_code=422, detail="billed_amount must be greater than zero")

        new_total = billed_total + billed_amount
        if new_total > recommended:
            raise HTTPException(status_code=422, detail="billed_amount exceeds remaining unbilled amount")

        remaining = recommended - new_total
        new_status = "Fully Billed" if remaining == 0 else "Partially Billed"
        old_status = config.billing_status

        try:
            self.db.add(
                WmBillingDocumentLink(
                    entity_type=payload.entity_type,
                    job_id=payload.job_id,
                    task_id=payload.task_id,
                    billing_reference_type=f"{'INTERNAL' if payload.action_type == 'CREATE' else 'EXTERNAL'}_INVOICE",
                    billing_reference_id=reference_id,
                    billing_reference_no=reference_no,
                    billed_amount=billed_amount,
                    billed_date=payload.billed_date or date.today(),
                    billing_status=new_status,
                    included_billable_hours=readiness.included_billable_hours,
                    included_recoverable_expense=readiness.included_recoverable_expense,
                    billing_remarks=payload.billing_remarks,
                    created_by=user_id,
                )
            )
            self._record_status_change(
                payload.entity_type,
                payload.job_id,
                payload.task_id,
                old_status,
                new_status,
                f"{payload.action_type}_INVOICE",
                reference_no,
                billed_amount,
                payload.billing_remarks,
                user_id,
            )
            config.billing_status = new_status
            config.updated_by = user_id
            config.updated_on = datetime.utcnow()
            self.db.add(
                TaskAuditLog(
                    entity_name="wm_billing_document_link",
                    entity_id=payload.task_id or payload.job_id or 0,
                    action=f"{payload.action_type}_INVOICE",
                    details=f"entity={payload.entity_type};reference_no={reference_no};billed_amount={billed_amount}",
                    created_by=user_id,
                )
            )
            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Invoice processing failed: {exc}") from exc

        return {
            "status": "SUCCESS",
            "entity_type": payload.entity_type,
            "invoice_no": reference_no,
            "billing_status": new_status,
            "remaining_unbilled_amount": remaining,
            "message": "Invoice created successfully" if payload.action_type == "CREATE" else "Invoice linked and billing updated successfully",
        }

    def _validate_entity(self, entity_type: str, job_id: int | None, task_id: int | None) -> tuple[WmJob | None, WmTask | None]:
        if entity_type == "JOB":
            if not job_id:
                raise HTTPException(status_code=422, detail="job_id is required for JOB entity")
            job = self.db.query(WmJob).filter(WmJob.job_id == job_id, WmJob.is_active.is_(True)).first()
            if not job:
                raise HTTPException(status_code=422, detail="Invalid job")
            return job, None

        if not task_id:
            raise HTTPException(status_code=422, detail="task_id is required for TASK entity")
        task = self.db.query(WmTask).filter(WmTask.task_id == task_id, WmTask.is_active.is_(True)).first()
        if not task:
            raise HTTPException(status_code=422, detail="Invalid task")
        if job_id and task.job_id != job_id:
            raise HTTPException(status_code=422, detail="Task does not belong to selected job")
        return None, task

    def _validate_billable_ready(self, entity_type: str, job_id: int | None, task_id: int | None) -> tuple[WmBillingConfiguration, WmBillingReadiness]:
        self._validate_entity(entity_type, job_id, task_id)
        config = self._get_configuration(entity_type, job_id, task_id)
        if not config or not config.billable_flag:
            raise HTTPException(status_code=422, detail="Entity is not billable")
        readiness = self._get_readiness(entity_type, job_id, task_id)
        if not readiness or not readiness.ready_for_billing_flag:
            raise HTTPException(status_code=422, detail="Entity is not ready for billing")
        return config, readiness

    def _get_configuration(self, entity_type: str, job_id: int | None, task_id: int | None) -> WmBillingConfiguration | None:
        return self.db.query(WmBillingConfiguration).filter(
            WmBillingConfiguration.entity_type == entity_type,
            WmBillingConfiguration.job_id == job_id,
            WmBillingConfiguration.task_id == task_id,
            WmBillingConfiguration.is_active.is_(True),
        ).first()

    def _get_readiness(self, entity_type: str, job_id: int | None, task_id: int | None) -> WmBillingReadiness | None:
        return self.db.query(WmBillingReadiness).filter(
            WmBillingReadiness.entity_type == entity_type,
            WmBillingReadiness.job_id == job_id,
            WmBillingReadiness.task_id == task_id,
            WmBillingReadiness.is_active.is_(True),
        ).first()

    def _calculate_pools(self, entity_type: str, job_id: int | None, task_id: int | None) -> tuple[Decimal, Decimal]:
        ts_filters = [WmTimesheet.approval_status == "Approved", WmTimesheet.is_active.is_(True)]
        ec_filters = [
            WmExpenseClaim.approval_status == "Approved",
            WmExpenseClaim.recoverable_flag.is_(True),
            WmExpenseClaim.is_active.is_(True),
        ]

        if entity_type == "JOB":
            ts_filters.append(WmTimesheet.job_id == job_id)
            ec_filters.append(WmExpenseClaim.job_id == job_id)
        else:
            ts_filters.append(WmTimesheet.task_id == task_id)
            ec_filters.append(WmExpenseClaim.task_id == task_id)

        billable_hours = self.db.query(func.coalesce(func.sum(WmTimesheet.billable_hours), 0)).filter(and_(*ts_filters)).scalar()
        recoverable_expense = self.db.query(func.coalesce(func.sum(WmExpenseClaim.total_amount), 0)).filter(and_(*ec_filters)).scalar()
        return Decimal(str(billable_hours or 0)), Decimal(str(recoverable_expense or 0))

    def _recommended_amount(self, config: WmBillingConfiguration, readiness: WmBillingReadiness) -> Decimal:
        if config.billing_model == "FIXED_FEE":
            return Decimal(str(config.fixed_billing_amount or 0))
        if config.billing_model in {"TIME_MATERIAL", "RETAINER"}:
            hourly_rate = Decimal("100")
            return Decimal(str(readiness.included_recoverable_expense or 0)) + (Decimal(str(readiness.included_billable_hours or 0)) * hourly_rate)
        return Decimal(str(readiness.included_recoverable_expense or 0))

    def _total_billed(self, entity_type: str, job_id: int | None, task_id: int | None) -> Decimal:
        total = self.db.query(func.coalesce(func.sum(WmBillingDocumentLink.billed_amount), 0)).filter(
            WmBillingDocumentLink.entity_type == entity_type,
            WmBillingDocumentLink.job_id == job_id,
            WmBillingDocumentLink.task_id == task_id,
            WmBillingDocumentLink.billing_reference_type.like("%_INVOICE"),
            WmBillingDocumentLink.is_active.is_(True),
        ).scalar()
        return Decimal(str(total or 0))

    def _ensure_unique_reference(self, reference_no: str) -> None:
        exists = self.db.query(WmBillingDocumentLink).filter(
            WmBillingDocumentLink.billing_reference_no == reference_no,
            WmBillingDocumentLink.is_active.is_(True),
        ).first()
        if exists:
            raise HTTPException(status_code=409, detail="Billing reference already linked")

    def _generate_reference_no(self, prefix: str) -> str:
        year = datetime.utcnow().year
        ref_prefix = f"{prefix}-{year}-"
        latest = self.db.query(WmBillingDocumentLink).filter(
            WmBillingDocumentLink.billing_reference_no.like(f"{ref_prefix}%"),
        ).order_by(desc(WmBillingDocumentLink.billing_document_link_id)).first()
        next_seq = (int(latest.billing_reference_no.split("-")[-1]) + 1) if latest and latest.billing_reference_no else 1
        return f"{ref_prefix}{next_seq:05d}"

    def _record_status_change(
        self,
        entity_type: str,
        job_id: int | None,
        task_id: int | None,
        old_status: str,
        new_status: str,
        action_code: str,
        reference_no: str,
        billed_amount: Decimal | None,
        remarks: str | None,
        user_id: int,
    ) -> None:
        self.db.add(
            WmBillingStatusHistory(
                entity_type=entity_type,
                job_id=job_id,
                task_id=task_id,
                old_billing_status=old_status,
                new_billing_status=new_status,
                action_code=action_code,
                billing_reference_no=reference_no,
                billed_amount=billed_amount,
                acted_by=user_id,
                remarks=remarks,
            )
        )
