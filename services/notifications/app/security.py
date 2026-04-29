from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime

from app.settings import settings


def _b64d(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def decode_access_token(token: str) -> dict | None:
    try:
        h, p, s = token.split(".")
        expected = hmac.new(settings.secret_key.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _b64d(s)):
            return None
        payload = json.loads(_b64d(p))
        if payload.get("exp", 0) < int(datetime.now(UTC).timestamp()):
            return None
        return payload
    except Exception:
        return None
