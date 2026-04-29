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
    app_name: str = os.getenv("APP_NAME", "Card Exchange — Trades Service")
    database_url: str = os.getenv("TRADES_DATABASE_URL", "sqlite:///./data/trades.db")
    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-production")
    internal_secret: str = os.getenv("INTERNAL_SECRET", "internal-secret-key")
    auth_service_url: str = os.getenv("AUTH_SERVICE_URL", "http://auth:8001")
    cards_service_url: str = os.getenv("CARDS_SERVICE_URL", "http://cards:8002")
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")


settings = Settings()
