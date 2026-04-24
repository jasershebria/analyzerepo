from __future__ import annotations

import uuid
from datetime import datetime
from enum import IntEnum

from pydantic import Field, field_validator

from app.schemas.common import CamelModel


class AuthType(IntEnum):
    PersonalAccessToken = 1
    OAuth = 2
    AppInstallation = 3


class BranchRuleRequest(CamelModel):
    pattern: str = Field(..., max_length=200, min_length=1)
    scan_on_push: bool = True


class BranchRuleDto(CamelModel):
    id: uuid.UUID
    pattern: str
    scan_on_push: bool
    is_enabled: bool


class RepositoryDto(CamelModel):
    id: uuid.UUID
    name: str
    web_url: str
    created_at: datetime


class CreateRepositoryRequest(CamelModel):
    provider_id: uuid.UUID
    provider_repo_id: str = Field(..., max_length=200, min_length=1)
    name: str = Field(..., max_length=200, min_length=1)
    web_url: str = Field(..., max_length=500, min_length=1)
    clone_url: str = Field(..., max_length=500, min_length=1)
    default_branch: str = Field(..., max_length=100, min_length=1)
    authentication_type: AuthType
    secret_ref: str = Field(..., max_length=500, min_length=1)
    run_initial_scan: bool = False
    branch_rules: list[BranchRuleRequest] = Field(..., min_length=1)

    @field_validator("web_url")
    @classmethod
    def web_url_must_be_valid(cls, v: str) -> str:
        from urllib.parse import urlparse
        r = urlparse(v)
        if not all([r.scheme, r.netloc]):
            raise ValueError("Web URL must be a valid URL")
        return v


class CreateRepositoryResponse(CamelModel):
    id: uuid.UUID
    name: str
    provider_id: uuid.UUID
    web_url: str
    created_at: datetime


class GetAllRepositoriesQuery(CamelModel):
    page_index: int = Field(default=1, ge=1)
    skip_count: int = Field(default=0, ge=0)
    max_result_count: int = Field(default=10, ge=1, le=500)
    include_deleted: bool = False
    search_term: str | None = None
    provider_id: uuid.UUID | None = None
    is_active: bool | None = None


class GetRepositoryResponse(CamelModel):
    id: uuid.UUID
    name: str
    provider_id: uuid.UUID
    web_url: str
    clone_url: str | None
    default_branch: str
    provider_repo_id: str | None
    provider_workspace_id: str | None
    is_active: bool
    cloned_directory: str | None
    last_seen_at_utc: datetime | None
    created_at: datetime
    updated_at: datetime | None
    is_deleted: bool
    authentication_type: AuthType | None
    secret_ref: str | None
    branch_rules: list[BranchRuleDto]


class UpdateRepositoryRequest(CamelModel):
    name: str = Field(..., max_length=200, min_length=1)
    provider_id: uuid.UUID
    web_url: str = Field(..., max_length=500, min_length=1)
    clone_url: str = Field(..., max_length=500)
    default_branch: str = Field(..., max_length=100)
    provider_repo_id: str | None = None
    authentication_type: AuthType
    secret_ref: str = Field(..., max_length=500, min_length=1)
    branch_rules: list[BranchRuleRequest] = Field(default_factory=list)

    @field_validator("web_url")
    @classmethod
    def web_url_must_be_valid(cls, v: str) -> str:
        from urllib.parse import urlparse
        r = urlparse(v)
        if not all([r.scheme, r.netloc]):
            raise ValueError("Web URL must be a valid URL")
        return v


class UpdateRepositoryResponse(CamelModel):
    id: uuid.UUID
    name: str
    provider_id: uuid.UUID
    web_url: str
    updated_at: datetime


class TestConnectionRequest(CamelModel):
    provider_id: uuid.UUID
    web_url: str = Field(..., min_length=1)
    auth_type: str = Field(..., min_length=1)
    secret_ref_or_token: str = Field(..., min_length=1)
    optional_clone_preference: str | None = None

    @field_validator("web_url")
    @classmethod
    def web_url_must_be_valid(cls, v: str) -> str:
        from urllib.parse import urlparse
        r = urlparse(v)
        if not all([r.scheme, r.netloc]):
            raise ValueError("Web URL must be a valid URL")
        return v

    @field_validator("auth_type")
    @classmethod
    def auth_type_must_be_valid(cls, v: str) -> str:
        if v.lower() not in ("token", "oauth", "app"):
            raise ValueError("Auth type must be 'token', 'oauth', or 'app'")
        return v


class GitBranchDto(CamelModel):
    name: str


class TestConnectionResponse(CamelModel):
    success: bool
    repo_name: str | None
    provider_repo_id: str | None
    provider_workspace_id: str | None
    default_branch: str | None
    clone_url: str | None
    web_url_normalized: str | None
    error_message: str | None
    branches: list[GitBranchDto]
