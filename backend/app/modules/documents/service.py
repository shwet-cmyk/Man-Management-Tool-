from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.wm_approval_transaction import WmApprovalTransaction
from app.models.wm_document import WmDocument
from app.models.wm_document_audit import WmDocumentAudit
from app.models.wm_document_link import WmDocumentLink
from app.modules.documents.schemas import (
    DocumentAccessRequest,
    DocumentCarryForwardRequest,
    DocumentLinkRequest,
    DocumentUploadRequest,
    DocumentVersionRequest,
)
from app.modules.rbac.schemas import AccessCheckRequest
from app.modules.rbac.service import RbacService


class DocumentService:
    def __init__(self, db: Session):
        self.db = db

    def upload_document(self, payload: DocumentUploadRequest):
        if payload.file_hash:
            dup = self.db.query(WmDocument).filter(WmDocument.file_hash == payload.file_hash, WmDocument.is_active.is_(True)).first()
            if dup:
                return {"document_id": dup.document_id, "duplicate": True}

        row = WmDocument(
            file_name=payload.file_name,
            file_url=payload.file_url,
            file_type=payload.file_type,
            file_tag=payload.file_tag,
            uploaded_by=payload.uploaded_by,
            file_hash=payload.file_hash,
            version=1,
        )
        self.db.add(row)
        self.db.flush()
        self._audit(row.document_id, "UPLOAD", payload.uploaded_by, payload.file_name)
        self.db.commit()
        return {"document_id": row.document_id, "version": row.version}

    def link_document(self, payload: DocumentLinkRequest):
        doc = self.db.query(WmDocument).filter(WmDocument.document_id == payload.document_id, WmDocument.is_active.is_(True)).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        exists = (
            self.db.query(WmDocumentLink)
            .filter(
                WmDocumentLink.document_id == payload.document_id,
                WmDocumentLink.entity_type == payload.entity_type,
                WmDocumentLink.entity_id == payload.entity_id,
            )
            .first()
        )
        if exists:
            return {"document_link_id": exists.document_link_id, "status": "EXISTS"}

        row = WmDocumentLink(
            document_id=payload.document_id,
            entity_type=payload.entity_type,
            entity_id=payload.entity_id,
            is_primary=payload.is_primary,
        )
        self.db.add(row)
        self.db.flush()
        self._audit(payload.document_id, "LINK", payload.user_id, f"{payload.entity_type}:{payload.entity_id}")
        self.db.commit()
        return {"document_link_id": row.document_link_id, "status": "LINKED"}

    def get_documents(self, entity_type: str, entity_id: int, access: DocumentAccessRequest):
        access_result = RbacService(self.db).check_access(
            AccessCheckRequest(
                user_id=access.user_id,
                module_name=access.module_name,
                feature_name=access.feature_name,
                action_name=access.action_name,
                company_id=access.company_id,
                branch_id=access.branch_id,
                department_id=access.department_id,
                entity_id=entity_id,
            )
        )
        if not access_result.get("allowed"):
            raise HTTPException(status_code=403, detail="Access denied")

        links = self.db.query(WmDocumentLink).filter(WmDocumentLink.entity_type == entity_type, WmDocumentLink.entity_id == entity_id).all()
        docs = []
        for link in links:
            doc = self.db.query(WmDocument).filter(WmDocument.document_id == link.document_id, WmDocument.is_active.is_(True)).first()
            if doc:
                docs.append(
                    {
                        "document_id": doc.document_id,
                        "file_name": doc.file_name,
                        "file_url": doc.file_url,
                        "file_type": doc.file_type,
                        "file_tag": doc.file_tag,
                        "version": doc.version,
                        "is_primary": link.is_primary,
                    }
                )
        return docs

    def create_version(self, payload: DocumentVersionRequest):
        parent = self.db.query(WmDocument).filter(WmDocument.document_id == payload.parent_document_id, WmDocument.is_active.is_(True)).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent document not found")

        row = WmDocument(
            file_name=payload.file_name,
            file_url=payload.file_url,
            file_type=payload.file_type,
            file_tag=payload.file_tag,
            uploaded_by=payload.uploaded_by,
            file_hash=payload.file_hash,
            version=int(parent.version) + 1,
            parent_document_id=parent.document_id,
        )
        self.db.add(row)
        self.db.flush()
        self._audit(row.document_id, "VERSION_CREATE", payload.uploaded_by, f"parent={parent.document_id}")
        self.db.commit()
        return {"document_id": row.document_id, "parent_document_id": parent.document_id, "version": row.version}

    def carry_forward(self, payload: DocumentCarryForwardRequest):
        source_links = (
            self.db.query(WmDocumentLink)
            .filter(WmDocumentLink.entity_type == payload.source_entity_type, WmDocumentLink.entity_id == payload.source_entity_id)
            .all()
        )
        created = 0
        for link in source_links:
            exists = (
                self.db.query(WmDocumentLink)
                .filter(
                    WmDocumentLink.entity_type == payload.target_entity_type,
                    WmDocumentLink.entity_id == payload.target_entity_id,
                    WmDocumentLink.document_id == link.document_id,
                )
                .first()
            )
            if exists:
                continue
            self.db.add(
                WmDocumentLink(
                    document_id=link.document_id,
                    entity_type=payload.target_entity_type,
                    entity_id=payload.target_entity_id,
                    is_primary=False,
                )
            )
            self._audit(link.document_id, "CARRY_FORWARD", payload.user_id, f"to={payload.target_entity_type}:{payload.target_entity_id}")
            created += 1
        self.db.commit()
        return {"carried_forward": created}

    def delete_document_link(self, document_id: int, entity_type: str, entity_id: int, user_id: int):
        approved_txn = (
            self.db.query(WmApprovalTransaction)
            .filter(
                WmApprovalTransaction.entity_type == entity_type,
                WmApprovalTransaction.entity_id == entity_id,
                WmApprovalTransaction.status == "APPROVED",
            )
            .first()
        )
        if approved_txn and entity_type.upper() in {"VOUCHER", "INVOICE"}:
            raise HTTPException(status_code=422, detail="Documents cannot be deleted from approved financial entities")

        row = (
            self.db.query(WmDocumentLink)
            .filter(WmDocumentLink.document_id == document_id, WmDocumentLink.entity_type == entity_type, WmDocumentLink.entity_id == entity_id)
            .first()
        )
        if not row:
            raise HTTPException(status_code=404, detail="Document link not found")
        self.db.delete(row)
        self._audit(document_id, "UNLINK", user_id, f"{entity_type}:{entity_id}")
        self.db.commit()
        return {"status": "UNLINKED"}

    def _audit(self, document_id: int, action: str, user_id: int, remarks: str | None):
        self.db.add(WmDocumentAudit(document_id=document_id, action=action, user_id=user_id, remarks=remarks))
