from __future__ import annotations

from fastapi import FastAPI

from backend.routers import api_router


def create_app() -> FastAPI:
    app = FastAPI(title="RAG Project API")
    app.include_router(api_router)
    return app


app = create_app()
