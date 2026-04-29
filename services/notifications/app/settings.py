from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv() -> None:
    for p in [Path(".env"), Path("../../.env"), Path("../../../.env")]:
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                s = line.strip()
                if not s or s.startswith("#") or "=" not in s:
                    continue
                k, v = s.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
            break


_load_dotenv()


@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "Card Exchange — Notifications Service")
    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-production")
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")


settings = Settings()
