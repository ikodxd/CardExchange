from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db.session import Base, engine
from app.routers import admin, cards, internal
from app.settings import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    Path("data/uploads").mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.include_router(cards.router)
app.include_router(admin.router)
app.include_router(internal.router)

upload_dir = Path("data/uploads")
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/cards/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")
