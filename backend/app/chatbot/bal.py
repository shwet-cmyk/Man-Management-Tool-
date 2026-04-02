from __future__ import annotations

from app.chatbot.bll import ChatbotBLL, QuickPromptService
from app.chatbot.dal import ChatbotDAL
from app.chatbot.schemas import ChatHistoryResponse, ChatMessage, ChatQueryRequest, ChatQueryResponse, QuickPromptsResponse


class ChatbotBAL:
    def __init__(self, dal: ChatbotDAL | None = None, bll: ChatbotBLL | None = None, prompt_service: QuickPromptService | None = None) -> None:
        self.dal = dal or ChatbotDAL()
        self.bll = bll or ChatbotBLL(self.dal)
        self.prompt_service = prompt_service or QuickPromptService(self.dal)

    def query(self, payload: ChatQueryRequest) -> ChatQueryResponse:
        session_id = payload.session_id or self.dal.create_session_id()
        route_path = payload.context.route_path if payload.context else '/dashboard'
        module_name = payload.context.module_name if payload.context else None

        self.dal.append_message(session_id, 'user', payload.message)
        reply = self.bll.build_reply(payload.message, route_path=route_path, module_name=module_name)
        self.dal.append_message(session_id, 'assistant', reply)

        return ChatQueryResponse(session_id=session_id, reply=reply, route_path=route_path)

    def get_history(self, session_id: str) -> ChatHistoryResponse:
        messages = [ChatMessage(**item) for item in self.dal.list_messages(session_id)]
        return ChatHistoryResponse(session_id=session_id, count=len(messages), items=messages)

    def quick_prompts(self, *, module_name: str, screen_key: str | None, user_id: int, language: str = 'en', limit: int = 7) -> QuickPromptsResponse:
        prompts = self.prompt_service.get_prompts(
            module_name=module_name,
            screen_key=screen_key,
            user_id=user_id,
            language=language,
            limit=limit,
        )
        return QuickPromptsResponse(prompts=prompts)

    def track_prompt_usage(self, *, user_id: int, prompt_id: int) -> None:
        self.prompt_service.register_prompt_usage(user_id=user_id, prompt_id=prompt_id)
