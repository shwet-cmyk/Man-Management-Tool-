from pydantic import BaseModel, Field


class DependencyCheckRequest(BaseModel):
    task_id: str
    user_id: str
    action: str = Field(pattern="^(START|SUBMIT|APPROVE)$")
    dependency_type: str = Field(default="FS", pattern="^(FS|SS|FF)$")
    depends_on_user_id: str | None = None
    override_flag: bool = False


class DependencyCreateRequest(BaseModel):
    task_id: str
    user_id: str
    depends_on_user_id: str
    depends_on_task_id: str | None = None
    dependency_type: str = Field(default="FS", pattern="^(FS|SS|FF)$")


class DependencyActionRequest(BaseModel):
    dependency_id: str
    action: str = Field(pattern="^(COMPLETE|APPROVE|REJECT)$")


class DependencyCheckResponse(BaseModel):
    allowed: bool
    message: str
