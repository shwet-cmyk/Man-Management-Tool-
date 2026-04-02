from __future__ import annotations

from fastapi import APIRouter, Query, Response, status
from pydantic import BaseModel

from app.chatbot.bal import ChatbotBAL
from app.chatbot.schemas import ChatHistoryResponse, ChatQueryRequest, ChatQueryResponse, QuickPromptsResponse

router = APIRouter(prefix='/chatbot', tags=['Contextual Chatbot'])
_bal = ChatbotBAL()


class QuickPromptUsageRequest(BaseModel):
    user_id: int
    prompt_id: int


@router.post('/query', response_model=ChatQueryResponse)
def query_chatbot(payload: ChatQueryRequest) -> ChatQueryResponse:
    return _bal.query(payload)


@router.get('/sessions/{session_id}/messages', response_model=ChatHistoryResponse)
def get_session_messages(session_id: str) -> ChatHistoryResponse:
    return _bal.get_history(session_id)


@router.get('/quick-prompts', response_model=QuickPromptsResponse)
def get_quick_prompts(
    module_name: str = Query(..., description='Current module name'),
    user_id: int = Query(..., description='Current user id'),
    screen_key: str | None = Query(default=None, description='Current screen key'),
    language: str = Query(default='en', description='en | hi | gu | mr'),
    limit: int = Query(default=7, ge=3, le=7),
) -> QuickPromptsResponse:
    return _bal.quick_prompts(module_name=module_name, screen_key=screen_key, user_id=user_id, language=language, limit=limit)


@router.post('/quick-prompts/usage', status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def track_quick_prompt_usage(payload: QuickPromptUsageRequest) -> Response:
    _bal.track_prompt_usage(user_id=payload.user_id, prompt_id=payload.prompt_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
