from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.modules.documents.schemas import (
    DocumentAccessRequest,
    DocumentCarryForwardRequest,
    DocumentLinkRequest,
    DocumentUploadRequest,
    DocumentVersionRequest,
)
from app.modules.documents.service import DocumentService
from app.modules.rbac.schemas import PermissionAssignRequest, RoleCreateRequest
from app.modules.rbac.service import RbacService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def grant_doc_view_permission(db, user_id: int):
    rbac = RbacService(db)
    role = rbac.create_role(RoleCreateRequest(name=f"DocViewer-{user_id}", is_system_role=False))
    rbac.assign_permission(
        role["role_id"],
        PermissionAssignRequest(module_name="DOCUMENT", feature_name="DOCUMENT", action_name="VIEW", is_allowed=True),
    )
    rbac.assign_user_role(user_id, role["role_id"])


def test_upload_link_get_and_versioning():
    db = setup_db()
    svc = DocumentService(db)
    grant_doc_view_permission(db, 501)

    uploaded = svc.upload_document(
        DocumentUploadRequest(
            file_name="proposal.pdf",
            file_url="https://files.local/proposal.pdf",
            file_type="application/pdf",
            file_tag="proposal",
            uploaded_by=501,
            file_hash="abc123",
        )
    )
    link = svc.link_document(DocumentLinkRequest(document_id=uploaded["document_id"], entity_type="LEAD", entity_id=10, user_id=501))
    assert link["status"] == "LINKED"

    docs = svc.get_documents("LEAD", 10, DocumentAccessRequest(user_id=501))
    assert len(docs) == 1
    assert docs[0]["file_name"] == "proposal.pdf"

    v2 = svc.create_version(
        DocumentVersionRequest(
            parent_document_id=uploaded["document_id"],
            file_name="proposal_v2.pdf",
            file_url="https://files.local/proposal_v2.pdf",
            file_type="application/pdf",
            uploaded_by=501,
            file_hash="abc124",
        )
    )
    assert v2["version"] == 2


def test_carry_forward_avoids_duplicates():
    db = setup_db()
    svc = DocumentService(db)

    doc = svc.upload_document(
        DocumentUploadRequest(
            file_name="agreement.pdf",
            file_url="https://files.local/agreement.pdf",
            file_type="application/pdf",
            uploaded_by=600,
        )
    )
    svc.link_document(DocumentLinkRequest(document_id=doc["document_id"], entity_type="DEAL", entity_id=100, user_id=600))

    out1 = svc.carry_forward(
        DocumentCarryForwardRequest(
            source_entity_type="DEAL",
            source_entity_id=100,
            target_entity_type="INVOICE",
            target_entity_id=101,
            user_id=600,
        )
    )
    out2 = svc.carry_forward(
        DocumentCarryForwardRequest(
            source_entity_type="DEAL",
            source_entity_id=100,
            target_entity_type="INVOICE",
            target_entity_id=101,
            user_id=600,
        )
    )
    assert out1["carried_forward"] == 1
    assert out2["carried_forward"] == 0


def test_get_documents_requires_rbac_access():
    db = setup_db()
    svc = DocumentService(db)

    doc = svc.upload_document(
        DocumentUploadRequest(
            file_name="kyc.pdf",
            file_url="https://files.local/kyc.pdf",
            file_type="application/pdf",
            uploaded_by=700,
        )
    )
    svc.link_document(DocumentLinkRequest(document_id=doc["document_id"], entity_type="CUSTOMER", entity_id=55, user_id=700))

    try:
        svc.get_documents("CUSTOMER", 55, DocumentAccessRequest(user_id=701))
        assert False
    except Exception:
        assert True
