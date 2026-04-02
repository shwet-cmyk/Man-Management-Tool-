from __future__ import annotations

import asyncio
import json
import os
from collections import defaultdict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from redis.asyncio import Redis

app = FastAPI(title="TEZ WebSocket Gateway")
redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
CHANNEL = "tez:realtime"

connections: dict[str, WebSocket] = {}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws/{user_id}")
async def ws_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    # single connection per user
    old = connections.get(user_id)
    if old and old is not websocket:
        await old.close(code=1000)
    connections[user_id] = websocket

    redis = Redis.from_url(redis_url, decode_responses=True)
    pubsub = redis.pubsub()
    await pubsub.subscribe(CHANNEL)

    async def consumer():
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message.get("data"):
                payload = json.loads(message["data"])
                if payload.get("to") in {None, user_id}:
                    await websocket.send_json(payload)
            await asyncio.sleep(0.05)

    task = asyncio.create_task(consumer())
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            # Transport layer only: just route/publish event envelope
            event = {
                "type": data.get("type", "CHAT"),
                "from": user_id,
                "to": data.get("to"),
                "payload": data.get("payload", {}),
            }
            await redis.publish(CHANNEL, json.dumps(event))
    except WebSocketDisconnect:
        pass
    finally:
        task.cancel()
        await pubsub.unsubscribe(CHANNEL)
        await pubsub.close()
        await redis.close()
        if connections.get(user_id) is websocket:
            connections.pop(user_id, None)
