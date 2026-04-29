from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.db.session import Base, SessionLocal, engine
from app.limiter import limiter
from app.routers import admin, auth, internal, users
from app.services.user_service import UserService
from app.settings import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    Path("data/avatars").mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    try:
        UserService(db).ensure_admin_account()
        yield
    finally:
        db.close()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(internal.router)

avatar_dir = Path("data/avatars")
avatar_dir.mkdir(parents=True, exist_ok=True)
app.mount("/auth/avatars", StaticFiles(directory=str(avatar_dir)), name="avatars")
