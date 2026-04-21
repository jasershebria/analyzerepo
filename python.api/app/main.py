from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.routers import providers, repositories, ai, webhooks, files


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="AnalyzeRepo API",
    version="1.0.0",
    description="FastAPI backend equivalent of the AnalyzeRepo ASP.NET Core service.",
    lifespan=lifespan,
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

app.include_router(providers.router, prefix=API_PREFIX)
app.include_router(repositories.router, prefix=API_PREFIX)
app.include_router(ai.router, prefix=API_PREFIX)
app.include_router(webhooks.router, prefix=API_PREFIX)
app.include_router(files.router, prefix=API_PREFIX)


@app.get("/health", tags=["Health"])
async def health() -> dict:
    return {"status": "ok"}
