from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field, field_validator

from app.schemas.common import CamelModel


class ProviderDto(CamelModel):
    id: uuid.UUID
    name: str
    code: str
    api_base_url: str
    is_active: bool
    created_at: datetime


class CreateProviderRequest(CamelModel):
    name: str = Field(..., max_length=200, min_length=1)
    code: str = Field(..., max_length=50, min_length=1)
    api_base_url: str = Field(..., max_length=500, min_length=1)

    @field_validator("code")
    @classmethod
    def code_must_be_lowercase_alphanumeric(cls, v: str) -> str:
        import re
        if not re.match(r"^[a-z0-9_-]+$", v):
            raise ValueError("Code must be lowercase alphanumeric with hyphens or underscores.")
        return v

    @field_validator("api_base_url")
    @classmethod
    def api_base_url_must_be_valid(cls, v: str) -> str:
        from urllib.parse import urlparse
        result = urlparse(v)
        if not all([result.scheme, result.netloc]):
            raise ValueError("ApiBaseUrl must be a valid URL.")
        return v


class GetAllProvidersQuery(CamelModel):
    page_index: int = Field(default=1, ge=1)
    max_result_count: int = Field(default=50, ge=1, le=500)
    search_term: str | None = None
    is_active: bool | None = None
