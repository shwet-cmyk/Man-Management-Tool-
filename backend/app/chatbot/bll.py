from __future__ import annotations

from app.chatbot.dal import ChatbotDAL


class ChatbotBLL:
    def __init__(self, dal: ChatbotDAL) -> None:
        self.dal = dal

    def build_reply(self, message: str, route_path: str, module_name: str | None = None) -> str:
        module = module_name or route_path.strip('/').split('/')[0] or 'dashboard'
        return (
            f"You are in '{module}'. "
            f"I captured route context '{route_path}'. "
            f"Request noted: {message}"
        )
