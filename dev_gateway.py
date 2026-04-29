"""
Dev gateway — заменяет nginx при локальном запуске.
Проксирует запросы к сервисам и раздаёт SPA-фронтенд.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

import httpx
import websockets as ws_lib
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response

app = FastAPI(title="Dev Gateway")

FRONTEND_DIR = Path(__file__).parent / "frontend"

# Порядок важен: более длинные префиксы — первыми
_ROUTES: list[tuple[str, str]] = [
    ("/api/admin/cards/", "http://localhost:8002"),
    ("/api/admin/",       "http://localhost:8001"),
    ("/auth/",            "http://localhost:8001"),
    ("/users/",           "http://localhost:8001"),
    ("/cards/",           "http://localhost:8002"),
    ("/trades/",          "http://localhost:8003"),
]

_STRIP_REQ  = {"host", "content-length", "transfer-encoding", "connection"}
_STRIP_RESP = {"content-encoding", "transfer-encoding", "connection"}


# ── WebSocket прокси → notifications service ──────────────────────
@app.websocket("/ws")
async def ws_proxy(ws: WebSocket, token: str = ""):
    await ws.accept()
    backend_url = f"ws://localhost:8004/ws?token={token}"
    try:
        async with ws_lib.connect(backend_url) as backend:
            async def to_client():
                async for msg in backend:
                    try:
                        await ws.send_text(msg if isinstance(msg, str) else msg.decode())
                    except Exception:
                        break

            async def to_backend():
                try:
                    async for msg in ws.iter_text():
                        await backend.send(msg)
                except WebSocketDisconnect:
                    pass

            done, pending = await asyncio.wait(
                [asyncio.create_task(to_client()), asyncio.create_task(to_backend())],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for t in pending:
                t.cancel()
    except Exception as exc:
        print(f"[WS] {exc}")


# ── HTTP прокси + раздача фронтенда ──────────────────────────────
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def proxy(request: Request, path: str):
    full = "/" + path

    # Попытка прокси к сервису
    for prefix, target in _ROUTES:
        # Match both "/cards/something" and "/cards" (exact without trailing slash)
        if full.startswith(prefix) or full == prefix.rstrip("/"):
            url = target + full
            headers = {k: v for k, v in request.headers.items() if k.lower() not in _STRIP_REQ}
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.request(
                        method=request.method,
                        url=url,
                        headers=headers,
                        content=await request.body(),
                        params=dict(request.query_params),
                        follow_redirects=True,
                    )
                resp_headers = {k: v for k, v in resp.headers.items() if k.lower() not in _STRIP_RESP}
                return Response(content=resp.content, status_code=resp.status_code, headers=resp_headers)
            except httpx.ConnectError:
                return Response(
                    content=f'{{"detail":"Service unavailable ({target})"}}',
                    status_code=503,
                    media_type="application/json",
                )

    # Статические файлы фронтенда
    file_path = FRONTEND_DIR / path
    if file_path.is_file():
        return FileResponse(str(file_path))

    # SPA fallback
    return FileResponse(str(FRONTEND_DIR / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("dev_gateway:app", host="0.0.0.0", port=8000, reload=False)
