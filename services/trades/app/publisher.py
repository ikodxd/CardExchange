"""Redis pub/sub publisher for notification events."""
from __future__ import annotations

import asyncio
import json

import redis.asyncio as aioredis

from app.settings import settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
    return _redis


async def publish(channel: str, payload: dict) -> None:
    try:
        r = await get_redis()
        await asyncio.wait_for(r.publish(channel, json.dumps(payload)), timeout=3.0)
    except Exception as exc:
        # Redis unavailable — notifications won't fire but core logic continues
        print(f"[REDIS] publish error (non-fatal): {exc}")
