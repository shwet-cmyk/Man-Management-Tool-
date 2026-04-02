from __future__ import annotations

class InMemoryRepo:
    def __init__(self) -> None:
        self.rows: dict[int, dict] = {}
        self.seq = 1

    async def insert(self, row: dict) -> dict:
        obj = dict(row)
        obj['id'] = self.seq
        self.rows[self.seq] = obj
        self.seq += 1
        return obj

    async def list_all(self) -> list[dict]:
        return list(self.rows.values())

    async def update(self, row_id: int, patch: dict) -> dict | None:
        if row_id not in self.rows:
            return None
        self.rows[row_id].update(patch)
        return self.rows[row_id]
