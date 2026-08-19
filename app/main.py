from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database.connection import engine
from app.routes import auth, health, tasks


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        yield
    finally:
        await engine.dispose()


app = FastAPI(
    title="Taskflow API",
    description="API de tarefas com PostgreSQL e autenticação JWT.",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(tasks.router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", include_in_schema=False)
async def interface() -> FileResponse:
    return FileResponse("app/static/index.html")