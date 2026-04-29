from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.session import Base, engine
from app.routers import offers, transactions
from app.settings import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.include_router(offers.router)
app.include_router(transactions.router)
