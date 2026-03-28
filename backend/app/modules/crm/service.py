from __future__ import annotations

import json
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.wm_crm_deal import WmCrmDeal
from app.models.wm_crm_followup import WmCrmFollowup
from app.models.wm_crm_lead import WmCrmLead
from app.models.wm_crm_opportunity import WmCrmOpportunity
from app.models.wm_customer_lifecycle import WmCustomerLifecycle
from app.models.wm_rbac_approval_limit import WmRbacApprovalLimit
from app.modules.audit.schemas import AuditLogCreateRequest
from app.modules.audit.service import AuditService
from app.modules.crm.schemas import DealCreateRequest, DealInvoiceRequest, FollowupCreateRequest, LeadCreateRequest, LifecycleUpdateRequest


class CrmService:
    def __init__(self, db: Session):
        self.db = db

    def create_lead(self, payload: LeadCreateRequest, performed_by: int = 0):
        row = WmCrmLead(
            name=payload.name,
            source=payload.source,
            status="LEAD",
            assigned_users_json=json.dumps(payload.assigned_users),
            estimated_value=payload.estimated_value,
        )
        self.db.add(row)
        self.db.flush()
        self._audit("LEAD", row.lead_id, "CREATE", performed_by, {}, {"name": row.name, "source": row.source, "status": row.status})
        self.db.commit()
        return {"lead_id": row.lead_id, "status": row.status}

    def convert_lead_to_opportunity(self, lead_id: int, performed_by: int = 0):
        lead = self.db.query(WmCrmLead).filter(WmCrmLead.lead_id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        if lead.status != "LEAD":
            raise HTTPException(status_code=422, detail="Lead already converted")

        followup = (
            self.db.query(WmCrmFollowup)
            .filter(WmCrmFollowup.entity_type == "LEAD", WmCrmFollowup.entity_id == lead_id)
            .order_by(WmCrmFollowup.followup_id.desc())
            .first()
        )
        if not followup:
            raise HTTPException(status_code=422, detail="At least one follow-up is required before conversion")

        opp = WmCrmOpportunity(
            lead_id=lead.lead_id,
            value=int(lead.estimated_value or 0),
            probability=self._predict_conversion_probability(lead),
            status="OPEN",
        )
        self.db.add(opp)
        old_status = lead.status
        lead.status = "OPPORTUNITY"
        self.db.flush()
        self._audit("LEAD", lead.lead_id, "CONVERT", performed_by, {"status": old_status}, {"status": lead.status})
        self._audit("OPPORTUNITY", opp.opportunity_id, "CREATE", performed_by, {}, {"lead_id": lead.lead_id, "value": opp.value})
        self.db.commit()
        return {"opportunity_id": opp.opportunity_id, "probability": opp.probability}

    def create_deal(self, payload: DealCreateRequest, performed_by: int = 0):
        opp = self.db.query(WmCrmOpportunity).filter(WmCrmOpportunity.opportunity_id == payload.opportunity_id).first()
        if not opp:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        row = WmCrmDeal(
            opportunity_id=payload.opportunity_id,
            negotiated_value=payload.negotiated_value,
            customer_name=payload.customer_name,
            status="NEGOTIATION",
        )
        self.db.add(row)
        self.db.flush()
        self._audit("DEAL", row.deal_id, "CREATE", performed_by, {}, {"opportunity_id": row.opportunity_id, "negotiated_value": row.negotiated_value})
        self.db.commit()
        return {"deal_id": row.deal_id, "status": row.status}

    def convert_deal_to_invoice(self, deal_id: int, payload: DealInvoiceRequest):
        deal = self.db.query(WmCrmDeal).filter(WmCrmDeal.deal_id == deal_id).first()
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")
        if deal.status not in {"NEGOTIATION", "WON"}:
            raise HTTPException(status_code=422, detail="Deal cannot be invoiced")

        limit = self._approval_limit(payload.approved_by, "SALES")
        if limit is not None and int(deal.negotiated_value) > int(limit):
            raise HTTPException(status_code=422, detail="Approval limit exceeded")

        old = {"status": deal.status, "invoice_voucher_no": deal.invoice_voucher_no}
        deal.status = "INVOICED"
        deal.invoice_voucher_no = f"INV-{deal.deal_id}-{int(datetime.utcnow().timestamp())}"
        self._audit("DEAL", deal.deal_id, "INVOICE", payload.approved_by, old, {"status": deal.status, "invoice_voucher_no": deal.invoice_voucher_no})
        self.db.commit()
        return {"deal_id": deal.deal_id, "invoice_voucher_no": deal.invoice_voucher_no, "status": deal.status, "pushed_to_tez": payload.push_to_tez}

    def create_followup(self, payload: FollowupCreateRequest):
        row = WmCrmFollowup(
            entity_type=payload.entity_type.upper(),
            entity_id=payload.entity_id,
            next_followup_date=payload.next_followup_date,
            remarks=payload.remarks,
            assigned_to=payload.assigned_to,
            status="PENDING",
        )
        self.db.add(row)
        self.db.commit()
        return {"followup_id": row.followup_id, "status": row.status}

    def due_followups(self):
        now = datetime.utcnow()
        rows = self.db.query(WmCrmFollowup).filter(WmCrmFollowup.status == "PENDING", WmCrmFollowup.next_followup_date <= now).all()
        return [{"followup_id": x.followup_id, "entity_type": x.entity_type, "entity_id": x.entity_id, "assigned_to": x.assigned_to} for x in rows]

    def upsert_customer_lifecycle(self, payload: LifecycleUpdateRequest):
        row = self.db.query(WmCustomerLifecycle).filter(WmCustomerLifecycle.customer_id == payload.customer_id).first()
        if not row:
            row = WmCustomerLifecycle(customer_id=payload.customer_id, stage=payload.stage, churn_risk_score=payload.churn_risk_score)
        else:
            row.stage = payload.stage
            row.churn_risk_score = payload.churn_risk_score
            row.last_activity_date = datetime.utcnow()
        self.db.add(row)
        self.db.commit()
        return {"customer_id": row.customer_id, "stage": row.stage, "churn_risk_score": row.churn_risk_score}

    @staticmethod
    def _predict_conversion_probability(lead: WmCrmLead):
        base = 30
        if lead.source.upper() in {"REFERRAL", "EXISTING_CUSTOMER"}:
            base += 25
        if int(lead.estimated_value or 0) > 100000:
            base += 15
        return min(base, 95)

    def _approval_limit(self, user_id: int, module_name: str):
        row = self.db.query(WmRbacApprovalLimit).filter(WmRbacApprovalLimit.user_id == user_id, WmRbacApprovalLimit.module_name == module_name).first()
        return row.max_amount if row else None

    def _audit(self, entity_type: str, entity_id: int, action: str, user_id: int, old_data: dict, new_data: dict):
        AuditService(self.db).log_event(
            AuditLogCreateRequest(
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                performed_by=user_id,
                old_data=old_data,
                new_data=new_data,
                source="CRM",
            )
        )
