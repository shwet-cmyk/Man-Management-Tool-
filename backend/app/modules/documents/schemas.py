from pydantic import BaseModel, Field


class DocumentUploadRequest(BaseModel):
    file_name: str
    file_url: str
    file_type: str
    file_tag: str | None = None
    uploaded_by: int
    file_hash: str | None = None


class DocumentLinkRequest(BaseModel):
    document_id: int
    entity_type: str
    entity_id: int
    is_primary: bool = False
    user_id: int


class DocumentVersionRequest(BaseModel):
    parent_document_id: int
    file_name: str
    file_url: str
    file_type: str
    file_tag: str | None = None
    uploaded_by: int
    file_hash: str | None = None


class DocumentCarryForwardRequest(BaseModel):
    source_entity_type: str
    source_entity_id: int
    target_entity_type: str
    target_entity_id: int
    user_id: int


class DocumentAccessRequest(BaseModel):
    user_id: int
    module_name: str = "DOCUMENT"
    feature_name: str = "DOCUMENT"
    action_name: str = "VIEW"
    company_id: int | None = None
    branch_id: int | None = None
    department_id: int | None = None
    entity_id: int | None = None
