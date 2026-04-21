from __future__ import annotations

from app.services.provider_clients.base import IRepoProviderClient
from app.services.provider_clients.github_client import GitHubRepoProviderClient
from app.services.provider_clients.gitlab_client import GitLabRepoProviderClient
from app.services.provider_clients.bitbucket_client import BitbucketRepoProviderClient


class RepoProviderClientFactory:
    def get_client(self, provider_code: str, api_base_url: str | None = None) -> IRepoProviderClient:
        code = provider_code.lower()
        if code == "github":
            return GitHubRepoProviderClient(api_base_url)
        if code == "gitlab":
            return GitLabRepoProviderClient(api_base_url)
        if code == "bitbucket":
            return BitbucketRepoProviderClient(api_base_url)
        raise ValueError(f"Provider '{provider_code}' is not supported. Supported: github, gitlab, bitbucket")
