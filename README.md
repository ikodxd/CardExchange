# Collectible Card Exchange Service

FastAPI service for listing collectible cards and exchanging them atomically through a dedicated service layer.

## Features

- JWT authentication with `user`, `moderator`, and `admin` roles
- Card catalog with rarity and price filters plus pagination
- Transactional card exchange in `TradeService`
- Celery task for email notifications after a successful trade
- Moderator endpoint for deleting fake cards
- Admin endpoint `POST /api/admin/assign-role` for granting moderator access
- Pytest coverage focused on the trade business flow

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Docker Compose

```bash
docker compose up --build
```

The stack starts:

- `api` on `http://localhost:8000`
- `redis` for Celery broker/result backend
- `worker` for background email notification jobs

## Queue

```bash
celery -A app.tasks worker --loglevel=info
```

## Environment

Main runtime variables live in `.env`.

```env
APP_NAME=Collectible Card Exchange Service
DATABASE_URL=sqlite:///./data/trading_app.db
SECRET_KEY=change-me-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=60
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
ADMIN_EMAIL=admin@example.com
ADMIN_USERNAME=root_admin
ADMIN_PASSWORD=change-admin-password
```

## Roles

- Registration always creates accounts with role `user`
- Only the configured admin account can call `POST /api/admin/assign-role`
- The admin endpoint upgrades a user to `moderator`
