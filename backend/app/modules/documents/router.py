from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.documents.schemas import (
    DocumentAccessRequest,
    DocumentCarryForwardRequest,
    DocumentLinkRequest,
    DocumentUploadRequest,
    DocumentVersionRequest,
)
from app.modules.documents.service import DocumentService

router = APIRouter(prefix="/documents", tags=["Work Management - Documents"])


@router.post("/upload")
def upload_document(payload: DocumentUploadRequest, db: Session = Depends(get_db)):
    return DocumentService(db).upload_document(payload)


@router.post("/link")
def link_document(payload: DocumentLinkRequest, db: Session = Depends(get_db)):
    return DocumentService(db).link_document(payload)


@router.get("/{entity_type}/{entity_id}")
def get_documents(
    entity_type: str,
    entity_id: int,
    user_id: int = Query(...),
    module_name: str = Query("DOCUMENT"),
    feature_name: str = Query("DOCUMENT"),
    action_name: str = Query("VIEW"),
    company_id: int | None = Query(None),
    branch_id: int | None = Query(None),
    department_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    return DocumentService(db).get_documents(
        entity_type,
        entity_id,
        DocumentAccessRequest(
            user_id=user_id,
            module_name=module_name,
            feature_name=feature_name,
            action_name=action_name,
            company_id=company_id,
            branch_id=branch_id,
            department_id=department_id,
            entity_id=entity_id,
        ),
    )


@router.post("/version")
def create_version(payload: DocumentVersionRequest, db: Session = Depends(get_db)):
    return DocumentService(db).create_version(payload)


@router.post("/carry-forward")
def carry_forward(payload: DocumentCarryForwardRequest, db: Session = Depends(get_db)):
    return DocumentService(db).carry_forward(payload)


@router.delete("/{document_id}/{entity_type}/{entity_id}")
def unlink_document(document_id: int, entity_type: str, entity_id: int, user_id: int = Query(...), db: Session = Depends(get_db)):
    return DocumentService(db).delete_document_link(document_id, entity_type, entity_id, user_id)
