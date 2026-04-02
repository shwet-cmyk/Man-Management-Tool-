from __future__ import annotations

class InMemoryRepo:
    def __init__(self) -> None:
        self.rows: dict[int, dict] = {}
        self.seq = 1

    async def insert(self, row: dict) -> dict:
        row = dict(row)
        row_id = self.seq
        self.seq += 1
        row['id'] = row_id
        self.rows[row_id] = row
        return row

    async def get(self, row_id: int) -> dict | None:
        return self.rows.get(row_id)

    async def list_all(self) -> list[dict]:
        return list(self.rows.values())

    async def update(self, row_id: int, patch: dict) -> dict | None:
        row = self.rows.get(row_id)
        if not row:
            return None
        row.update(patch)
        return row
