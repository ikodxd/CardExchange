from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.db.session import Base, SessionLocal, engine
from app.routers import admin, auth, cards, trades
from app.services.user_service import UserService
from app.settings import settings


static_dir = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        UserService(db).ensure_admin_account()
        yield
    finally:
        db.close()


app = FastAPI(title=settings.app_name, lifespan=lifespan)


app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
def read_index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/admin", include_in_schema=False)
def read_admin_index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


app.include_router(auth.router)
app.include_router(cards.router)
app.include_router(trades.router)
app.include_router(admin.router)
