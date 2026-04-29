"""Thin HTTP clients for calling auth and cards services internally."""
from __future__ import annotations

import httpx

from app.settings import settings

_HEADERS = {"X-Internal-Key": settings.internal_secret}


async def get_card(card_id: int) -> dict:
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{settings.cards_service_url}/internal/cards/{card_id}", headers=_HEADERS)
        r.raise_for_status()
        return r.json()


async def transfer_card_owner(card_id: int, new_owner_id: int) -> dict:
    async with httpx.AsyncClient() as c:
        r = await c.patch(
            f"{settings.cards_service_url}/internal/cards/{card_id}/owner",
            json={"new_owner_id": new_owner_id},
            headers=_HEADERS,
        )
        r.raise_for_status()
        return r.json()


async def lock_card(card_id: int, locked: bool) -> dict:
    async with httpx.AsyncClient() as c:
        r = await c.patch(
            f"{settings.cards_service_url}/internal/cards/{card_id}/lock",
            json={"locked": locked},
            headers=_HEADERS,
        )
        r.raise_for_status()
        return r.json()


async def delist_card(card_id: int) -> dict:
    async with httpx.AsyncClient() as c:
        r = await c.patch(
            f"{settings.cards_service_url}/internal/cards/{card_id}/delist",
            headers=_HEADERS,
        )
        r.raise_for_status()
        return r.json()


async def get_user(user_id: int) -> dict:
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{settings.auth_service_url}/internal/users/{user_id}", headers=_HEADERS)
        r.raise_for_status()
        return r.json()


async def update_balance(user_id: int, delta: float) -> dict:
    async with httpx.AsyncClient() as c:
        r = await c.post(
            f"{settings.auth_service_url}/internal/users/{user_id}/balance",
            json={"delta": str(delta)},
            headers=_HEADERS,
        )
        r.raise_for_status()
        return r.json()
