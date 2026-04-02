from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

router = APIRouter(prefix="/collaboration", tags=["Collaboration Engine"])


class ChatType(str, Enum):
    dm = "DM"
    channel = "CHANNEL"
    context = "CONTEXT"


class ContextType(str, Enum):
    project = "PROJECT"
    task = "TASK"
    job = "JOB"
    ticket = "TICKET"


class PresenceStatus(str, Enum):
    online = "ONLINE"
    offline = "OFFLINE"
    away = "AWAY"
    busy = "BUSY"


class StartDmRequest(BaseModel):
    user_a: str
    user_b: str


class CreateChannelRequest(BaseModel):
    name: str
    project_id: int | None = None
    members: list[str] = Field(default_factory=list)


class MessageRequest(BaseModel):
    chat_id: int
    sender: str
    text: str | None = None
    attachments: list[str] = Field(default_factory=list)
    mentions: list[str] = Field(default_factory=list)
    reply_to_message_id: int | None = None


class ThreadReplyRequest(BaseModel):
    sender: str
    text: str
    attachments: list[str] = Field(default_factory=list)


class PresenceUpdateRequest(BaseModel):
    user: str
    status: PresenceStatus


class ConnectionManager:
    def __init__(self):
        self.active: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, user: str, websocket: WebSocket):
        await websocket.accept()
        self.active[user].append(websocket)

    def disconnect(self, user: str, websocket: WebSocket):
        if websocket in self.active.get(user, []):
            self.active[user].remove(websocket)

    async def push(self, user: str, payload: dict):
        for ws in self.active.get(user, []):
            await ws.send_json(payload)


manager = ConnectionManager()

CHATS: dict[int, dict] = {}
MESSAGES: dict[int, dict] = {}
THREADS: dict[int, list[dict]] = defaultdict(list)
PRESENCE: dict[str, dict] = {}
NOTIFICATIONS: list[dict] = []
READ_RECEIPTS: dict[int, list[str]] = defaultdict(list)
TYPING: dict[int, set[str]] = defaultdict(set)


def _presence(user: str) -> dict:
    return PRESENCE.get(user, {"user": user, "status": PresenceStatus.offline, "last_seen": None})


def ensure_project_channel(project_id: int, project_name: str, members: list[str]) -> dict:
    existing = [c for c in CHATS.values() if c["chat_type"] == ChatType.channel and c.get("project_id") == project_id]
    if existing:
        row = existing[0]
        row["members"] = sorted(set(row["members"] + members))
        return row

    next_id = len(CHATS) + 1
    row = {
        "chat_id": next_id,
        "chat_type": ChatType.channel,
        "name": f"#{project_name.lower().replace(' ', '-')}",
        "members": members,
        "project_id": project_id,
        "context": {"type": ContextType.project, "id": project_id},
        "created_at": datetime.utcnow(),
    }
    CHATS[next_id] = row
    return row


@router.get("/shortcuts")
def shortcuts():
    return {
        "search": "Ctrl+K",
        "new_dm": "Ctrl+N",
        "switch_channel": "Arrow+Enter",
        "reply": "R",
        "thread": "T",
    }


@router.get("/sidebar/{user}")
def sidebar(user: str):
    user_chats = [c for c in CHATS.values() if user in c.get("members", [])]
    return {
        "workspace": "TEZ Execution Workspace",
        "dms": [c for c in user_chats if c["chat_type"] == ChatType.dm],
        "channels": [c for c in user_chats if c["chat_type"] == ChatType.channel],
        "starred": [],
        "recent": sorted(user_chats, key=lambda c: c["created_at"], reverse=True)[:15],
    }


@router.post("/dms/start")
def start_dm(payload: StartDmRequest):
    existing = [
        c
        for c in CHATS.values()
        if c["chat_type"] == ChatType.dm and set(c["members"]) == {payload.user_a, payload.user_b}
    ]
    if existing:
        return existing[0]

    next_id = len(CHATS) + 1
    row = {
        "chat_id": next_id,
        "chat_type": ChatType.dm,
        "name": f"{payload.user_a} ↔ {payload.user_b}",
        "members": [payload.user_a, payload.user_b],
        "created_at": datetime.utcnow(),
    }
    CHATS[next_id] = row
    return row


@router.post("/channels")
def create_channel(payload: CreateChannelRequest):
    next_id = len(CHATS) + 1
    row = {
        "chat_id": next_id,
        "chat_type": ChatType.channel,
        "name": payload.name,
        "members": payload.members,
        "project_id": payload.project_id,
        "created_at": datetime.utcnow(),
    }
    CHATS[next_id] = row
    return row


@router.post("/channels/project/{project_id}/sync")
def sync_project_channel(project_id: int, project_name: str, members: list[str]):
    return ensure_project_channel(project_id=project_id, project_name=project_name, members=members)


@router.post("/context/{context_type}/{context_id}")
def open_context_chat(context_type: ContextType, context_id: int, members: list[str]):
    existing = [
        c
        for c in CHATS.values()
        if c.get("context", {}).get("type") == context_type and c.get("context", {}).get("id") == context_id
    ]
    if existing:
        return existing[0]

    next_id = len(CHATS) + 1
    row = {
        "chat_id": next_id,
        "chat_type": ChatType.context,
        "name": f"{context_type}-{context_id}",
        "members": members,
        "context": {"type": context_type, "id": context_id},
        "created_at": datetime.utcnow(),
    }
    CHATS[next_id] = row
    return row


@router.post("/messages")
async def send_message(payload: MessageRequest):
    chat = CHATS.get(payload.chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if payload.sender not in chat["members"]:
        raise HTTPException(status_code=403, detail="Sender is not a member of this chat")

    mid = len(MESSAGES) + 1
    msg = {
        "message_id": mid,
        **payload.model_dump(),
        "created_at": datetime.utcnow(),
        "reactions": [],
    }
    MESSAGES[mid] = msg

    for member in chat["members"]:
        if member == payload.sender:
            continue
        note = {
            "user": member,
            "type": "MENTION" if member in payload.mentions else "NEW_MESSAGE",
            "chat_id": payload.chat_id,
            "message_id": mid,
            "at": datetime.utcnow(),
            "read": False,
        }
        NOTIFICATIONS.append(note)
        await manager.push(member, {"event": "NEW_MESSAGE", "payload": msg})

    return msg


@router.post("/messages/{message_id}/thread")
async def reply_in_thread(message_id: int, payload: ThreadReplyRequest):
    parent = MESSAGES.get(message_id)
    if not parent:
        raise HTTPException(status_code=404, detail="Parent message not found")

    row = {
        "reply_id": len(THREADS[message_id]) + 1,
        "message_id": message_id,
        **payload.model_dump(),
        "created_at": datetime.utcnow(),
    }
    THREADS[message_id].append(row)

    chat = CHATS[parent["chat_id"]]
    for member in chat["members"]:
        if member != payload.sender:
            await manager.push(member, {"event": "THREAD_REPLY", "payload": row})
    return row


@router.get("/messages/{chat_id}")
def list_messages(chat_id: int, limit: int = 100):
    rows = [m for m in MESSAGES.values() if m["chat_id"] == chat_id]
    rows = sorted(rows, key=lambda x: x["created_at"], reverse=True)[:limit]
    for r in rows:
        r["thread_count"] = len(THREADS.get(r["message_id"], []))
    return rows


@router.post("/messages/{message_id}/read")
def mark_read(message_id: int, user: str):
    if message_id not in MESSAGES:
        raise HTTPException(status_code=404, detail="Message not found")
    if user not in READ_RECEIPTS[message_id]:
        READ_RECEIPTS[message_id].append(user)
    return {"message_id": message_id, "read_by": READ_RECEIPTS[message_id]}


@router.post("/typing/{chat_id}")
def typing_indicator(chat_id: int, user: str, typing: bool = True):
    if typing:
        TYPING[chat_id].add(user)
    else:
        TYPING[chat_id].discard(user)
    return {"chat_id": chat_id, "typing_users": sorted(TYPING[chat_id])}


@router.get("/presence/{user}")
def get_presence(user: str):
    return _presence(user)


@router.put("/presence")
def update_presence(payload: PresenceUpdateRequest):
    PRESENCE[payload.user] = {
        "user": payload.user,
        "status": payload.status,
        "last_seen": datetime.utcnow(),
    }
    return PRESENCE[payload.user]


@router.get("/search")
def search(q: str, user: str | None = None, channel: int | None = None):
    messages = list(MESSAGES.values())
    if user:
        messages = [m for m in messages if m["sender"] == user]
    if channel:
        messages = [m for m in messages if m["chat_id"] == channel]

    matched_messages = [m for m in messages if q.lower() in ((m.get("text") or "").lower())]
    matched_files = [m for m in messages if any(q.lower() in a.lower() for a in m.get("attachments", []))]
    matched_users = sorted({u for c in CHATS.values() for u in c.get("members", []) if q.lower() in u.lower()})
    matched_projects = [c for c in CHATS.values() if c.get("project_id") and q.lower() in c["name"].lower()]

    return {
        "messages": matched_messages,
        "files": matched_files,
        "users": matched_users,
        "projects": matched_projects,
    }


@router.get("/notifications/{user}")
def user_notifications(user: str, unread_only: bool = False):
    rows = [n for n in NOTIFICATIONS if n["user"] == user]
    if unread_only:
        rows = [n for n in rows if not n["read"]]
    return rows


@router.post("/notifications/{user}/mark-all-read")
def mark_all_notifications_read(user: str):
    for n in NOTIFICATIONS:
        if n["user"] == user:
            n["read"] = True
    return {"user": user, "status": "updated"}


@router.get("/reports/summary")
def collaboration_reports():
    return {
        "chat_activity_report": {
            "total_chats": len(CHATS),
            "total_messages": len(MESSAGES),
            "thread_replies": sum(len(v) for v in THREADS.values()),
        },
        "message_count_by_user": {
            user: len([m for m in MESSAGES.values() if m["sender"] == user])
            for user in sorted({m["sender"] for m in MESSAGES.values()})
        },
        "file_sharing_report": {
            "messages_with_attachments": len([m for m in MESSAGES.values() if m.get("attachments")]),
            "attachments_total": sum(len(m.get("attachments", [])) for m in MESSAGES.values()),
        },
    }


@router.get("/analytics/summary")
def collaboration_analytics():
    message_rows = list(MESSAGES.values())
    first_response = []
    by_chat: dict[int, list[dict]] = defaultdict(list)
    for row in sorted(message_rows, key=lambda x: x["created_at"]):
        by_chat[row["chat_id"]].append(row)
    for rows in by_chat.values():
        if len(rows) < 2:
            continue
        delta = rows[1]["created_at"] - rows[0]["created_at"]
        first_response.append(delta.total_seconds())

    return {
        "most_active_users": sorted(
            [{"user": u, "count": len([m for m in message_rows if m["sender"] == u])} for u in {m["sender"] for m in message_rows}],
            key=lambda x: x["count"],
            reverse=True,
        ),
        "response_time_seconds_avg": round(sum(first_response) / len(first_response), 2) if first_response else None,
        "collaboration_density": {
            "messages_per_chat": 0 if not CHATS else round(len(MESSAGES) / len(CHATS), 2),
        },
    }


@router.websocket("/ws/{user}")
async def websocket_presence(websocket: WebSocket, user: str):
    await manager.connect(user, websocket)
    PRESENCE[user] = {"user": user, "status": PresenceStatus.online, "last_seen": datetime.utcnow()}
    try:
        while True:
            payload = await websocket.receive_json()
            if payload.get("event") == "PING":
                await websocket.send_json({"event": "PONG", "at": datetime.utcnow().isoformat()})
    except WebSocketDisconnect:
        manager.disconnect(user, websocket)
        PRESENCE[user] = {"user": user, "status": PresenceStatus.offline, "last_seen": datetime.utcnow()}
