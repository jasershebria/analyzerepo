from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.routers import providers, repositories, ai, webhooks
from app.mcp.tools_server import mcp_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    import logging
    from app.rag import vector_store as vs
    from app.services.ai_service import AIChatService

    log = logging.getLogger("uvicorn.error")
    yield

    # Shutdown — close the shared MongoDB client
    await vs.close()


app = FastAPI(
    title="AnalyzeRepo API",
    version="1.0.0",
    description=(
        "AI-powered repository analysis backend. "
        "AI chat, repository management, RAG pipeline, and an MCP server for OpenHands integration."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "AI",           "description": "Direct LLM chat endpoints (single-turn and multi-turn with history)."},
        {"name": "Repositories", "description": "Repository registration, sync, and metadata."},
        {"name": "Providers",    "description": "Git provider credentials (GitHub, GitLab, Bitbucket, …)."},
        {"name": "Webhooks",     "description": "Incoming webhook handlers for provider push events."},
        {"name": "Health",       "description": "Liveness probe."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(KeyError)
async def key_error_handler(request: Request, exc: KeyError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


API_PREFIX = "/api"

app.include_router(providers.router,    prefix=API_PREFIX)
app.include_router(repositories.router, prefix=API_PREFIX)
app.include_router(ai.router,           prefix=API_PREFIX)
app.include_router(webhooks.router,     prefix=API_PREFIX)
app.mount("/mcp", mcp_app)


@app.get("/health", tags=["Health"])
async def health() -> dict:
    return {"status": "ok"}
