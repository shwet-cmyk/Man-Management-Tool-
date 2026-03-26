from pydantic import BaseModel, Field


class RuleCreateRequest(BaseModel):
    module: str
    condition: dict
    action: dict
    priority: int = 100


class RuleEvaluateRequest(BaseModel):
    module: str
    context: dict = Field(default_factory=dict)
