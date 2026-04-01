from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import get_settings
from backend.routers import api_router

_DEFAULT_DEV_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="RAG Project API")
    allow_origins = [*_DEFAULT_DEV_ORIGINS, *settings.cors_extra_allow_origins_list()]
    cors_kwargs = {
        "allow_origins": allow_origins,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }
    if settings.environment == "development":
        cors_kwargs["allow_origin_regex"] = r"http://(localhost|127\.0\.0\.1)(:\d+)?"
    app.add_middleware(CORSMiddleware, **cors_kwargs)
    app.include_router(api_router)
    return app


app = create_app()
