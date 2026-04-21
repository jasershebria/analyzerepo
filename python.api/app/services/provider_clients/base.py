from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RepoMeta:
    name: str
    web_url_normalized: str
    clone_url: str
    default_branch: str
    provider_repo_id: str
    provider_workspace_id: str | None
    provider_code: str


@dataclass
class ProviderAuth:
    auth_type: str
    secret_ref_or_token: str


class IRepoProviderClient(ABC):
    @abstractmethod
    async def get_repo_meta(self, web_url: str, auth: ProviderAuth) -> RepoMeta: ...

    @abstractmethod
    async def get_branches(self, meta: RepoMeta, auth: ProviderAuth) -> list[str]: ...
