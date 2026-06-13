"""
Enterprise AI Workbench — FastAPI application entry point.

Run from the project root:
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import get_settings
from backend.app.api.routes_health import router as health_router
from backend.app.api.routes_session import router as session_router
from backend.app.api.routes_claims import router as claims_router
from backend.app.api.routes_conversation import router as conversation_router


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Enterprise AI Workbench API",
        description="Governed, explainable AI for claims processing.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # In local mode, allow all localhost origins (any port) so the
    # frontend dev server, preview tools, and docs UIs all work without config.
    # In sandbox/production, only the explicitly configured origins are allowed.
    if settings.environment == "local":
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=r"http://localhost(:\d+)?",
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(health_router)
    app.include_router(session_router)
    app.include_router(claims_router)
    app.include_router(conversation_router)

    return app


app = create_app()
