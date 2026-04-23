from __future__ import annotations

import json
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/analyzerepo"

    ai_base_url: str = "http://localhost:11434/v1"
    ai_api_key: str = "ollama"
    ai_model: str = "qwen2.5-coder:3b"

    git_clone_base_path: str = "repos"

    cors_origins: list[str] = ["http://localhost:4200"]

    # MongoDB — used by the RAG pipeline
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db: str = "analyzerepo_rag"

    # Embeddings — must be a model pulled via 'ollama pull nomic-embed-text'
    embedding_model: str = "nomic-embed-text"

    # RAG chunking & retrieval
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 200
    rag_top_k: int = 5
    rag_embedding_batch_size: int = 32


settings = Settings()
