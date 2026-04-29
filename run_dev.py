"""
Запуск всех микросервисов локально (без Docker).
Использование: python run_dev.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
PYTHON = sys.executable

# Создаём папки data/ для каждого сервиса
for svc in ("auth", "cards", "trades"):
    (ROOT / "services" / svc / "data").mkdir(parents=True, exist_ok=True)

# Общие переменные окружения для локального запуска
BASE_ENV = {
    **os.environ,
    # Переопределяем URL-ы сервисов на localhost
    "AUTH_SERVICE_URL":   "http://localhost:8001",
    "CARDS_SERVICE_URL":  "http://localhost:8002",
    # Redis — опционально. Без него уведомления не работают, но ядро работает
    "REDIS_URL": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
}

services: list[tuple[str, str, int]] = [
    ("auth",          "services/auth",          8001),
    ("cards",         "services/cards",         8002),
    ("trades",        "services/trades",        8003),
    ("notifications", "services/notifications", 8004),
]

procs: list[subprocess.Popen] = []


def start_service(name: str, rel_dir: str, port: int) -> subprocess.Popen:
    cwd = ROOT / rel_dir
    print(f"[run_dev] >> {name:16s} -> http://localhost:{port}")
    return subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "app.main:app",
         "--host", "0.0.0.0", "--port", str(port), "--log-level", "warning"],
        cwd=str(cwd),
        env=BASE_ENV,
    )


try:
    for svc_name, svc_dir, svc_port in services:
        procs.append(start_service(svc_name, svc_dir, svc_port))

    time.sleep(2)  # ждём запуска сервисов

    # Gateway на 8000
    print("[run_dev] >> gateway           -> http://localhost:8000")
    gw = subprocess.Popen(
        [PYTHON, "dev_gateway.py"],
        cwd=str(ROOT),
        env=BASE_ENV,
    )
    procs.append(gw)

    print("\n[run_dev] All services started!")
    print("[run_dev] Open -> http://localhost:8000")
    print("[run_dev] Press Ctrl+C to stop\n")

    # Ждём завершения любого процесса
    for p in procs:
        p.wait()

except KeyboardInterrupt:
    print("\n[run_dev] Stopping...")
finally:
    for p in procs:
        try:
            p.terminate()
        except Exception:
            pass
    print("[run_dev] Done.")
