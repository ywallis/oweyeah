from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.middleware import LoggingMiddleware
from src.models import AppVersion
from src.routers import flats, items, login, reset, transactions, users
from src.utils import create_db_and_tables, get_git_version


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup logic
    create_db_and_tables()
    yield
    # Shutdown logic (optional)


origins = ["http://localhost:8081", "https://oy.yannwallis.com"]

app = FastAPI(lifespan=lifespan, title="OweYeah", version=get_git_version())


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)

app.include_router(users.router)
app.include_router(flats.router)
app.include_router(items.router)
app.include_router(transactions.router)
app.include_router(login.router)
app.include_router(reset.router)


@app.get("/version", response_model=AppVersion)
def version():
    return AppVersion(version=app.version)
