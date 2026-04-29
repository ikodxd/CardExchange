from __future__ import annotations

import asyncio
import smtplib
from email.mime.text import MIMEText

from app.settings import settings


async def send_reset_email(to_email: str, reset_token: str) -> None:
    reset_url = f"{settings.frontend_url}/#reset-password?token={reset_token}"
    body = (
        f"Password Reset — Card Exchange\n\n"
        f"Click the link to reset your password:\n{reset_url}\n\n"
        f"This link expires in 1 hour. If you didn't request this, ignore this email."
    )

    if not settings.smtp_user:
        print(f"[EMAIL] Reset link for {to_email}: {reset_url}")
        return

    msg = MIMEText(body)
    msg["Subject"] = "Password Reset — Card Exchange"
    msg["From"] = settings.smtp_from
    msg["To"] = to_email

    def _send() -> None:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as s:
            s.starttls()
            s.login(settings.smtp_user, settings.smtp_password)
            s.send_message(msg)

    await asyncio.to_thread(_send)
