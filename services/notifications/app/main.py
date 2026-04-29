from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from app.manager import manager
from app.security import decode_access_token
from app.settings import settings


async def _redis_listener() -> None:
    """Subscribe to Redis pub/sub; retries on connection failure (e.g. Redis not running)."""
    while True:
        try:
            r = aioredis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            pubsub = r.pubsub()
            await pubsub.psubscribe("user:*")
            async for msg in pubsub.listen():
                if msg["type"] != "pmessage":
                    continue
                channel: str = msg["channel"]
                try:
                    user_id = int(channel.split(":")[1])
                    payload = json.loads(msg["data"])
                    await manager.send(user_id, payload)
                except Exception as exc:
                    print(f"[NOTIFY] message error: {exc}")
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(f"[NOTIFY] Redis connection error (retrying in 5s): {exc}")
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(_redis_listener())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, token: str = ""):
    payload = decode_access_token(token)
    if not payload:
        await ws.close(code=4001)
        return

    user_id: int = payload["id"]
    await manager.connect(user_id, ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id, ws)
