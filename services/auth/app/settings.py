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
    app_name: str = os.getenv("APP_NAME", "Card Exchange — Auth Service")
    database_url: str = os.getenv("AUTH_DATABASE_URL", "sqlite:///./data/auth.db")
    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-production")
    internal_secret: str = os.getenv("INTERNAL_SECRET", "internal-secret-key")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    admin_email: str = os.getenv("ADMIN_EMAIL", "")
    admin_username: str = os.getenv("ADMIN_USERNAME", "")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "")
    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from: str = os.getenv("SMTP_FROM", "noreply@cardexchange.com")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:8000")
    starting_balance: float = float(os.getenv("STARTING_BALANCE", "1000.0"))


settings = Settings()
