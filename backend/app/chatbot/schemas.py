from __future__ import annotations

from pydantic import BaseModel, Field


class ChatActor(BaseModel):
    user_id: int | None = None
    role: str | None = None


class ChatContext(BaseModel):
    route_path: str = Field(default='/dashboard')
    screen_key: str | None = None
    module_name: str | None = None


class ChatQueryRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str | None = None
    actor: ChatActor | None = None
    context: ChatContext | None = None


class ChatQueryResponse(BaseModel):
    session_id: str
    reply: str
    route_path: str


class ChatMessage(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class ChatHistoryResponse(BaseModel):
    session_id: str
    count: int
    items: list[ChatMessage]


class QuickPromptItem(BaseModel):
    prompt_id: int
    text: str
    intent_code: str
    action_type: str
    route_path: str | None = None


class QuickPromptsResponse(BaseModel):
    prompts: list[QuickPromptItem]
