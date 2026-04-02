import asyncio
import json
import sys

import websockets


async def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/ws_test_client.py ws://localhost:8080/ws/test-user")
        return
    url = sys.argv[1]
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({"type": "CHAT", "to": None, "payload": {"message": "hello from ws client"}}))
        msg = await ws.recv()
        print("Received:", msg)


if __name__ == "__main__":
    asyncio.run(main())
