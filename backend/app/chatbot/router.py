from __future__ import annotations

from fastapi import APIRouter

from app.chatbot.bal import ChatbotBAL
from app.chatbot.schemas import ChatHistoryResponse, ChatQueryRequest, ChatQueryResponse

router = APIRouter(prefix='/chatbot', tags=['Contextual Chatbot'])
_bal = ChatbotBAL()


@router.post('/query', response_model=ChatQueryResponse)
def query_chatbot(payload: ChatQueryRequest) -> ChatQueryResponse:
    return _bal.query(payload)


@router.get('/sessions/{session_id}/messages', response_model=ChatHistoryResponse)
def get_session_messages(session_id: str) -> ChatHistoryResponse:
    return _bal.get_history(session_id)
