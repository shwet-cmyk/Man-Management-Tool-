from __future__ import annotations
from app.productivity.repositories.screenshot_repository import ScreenshotRepository

class ScreenshotService:
    def __init__(self, repo: ScreenshotRepository) -> None:
        self.repo = repo

    async def list_all(self) -> list[dict]:
        return await self.repo.list_all()

    async def create(self, payload: dict) -> dict:
        return await self.repo.insert(payload)

    async def update(self, row_id: int, payload: dict) -> dict | None:
        return await self.repo.update(row_id, payload)
