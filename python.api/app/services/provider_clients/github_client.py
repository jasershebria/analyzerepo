from __future__ import annotations

import httpx

from app.services.provider_clients.base import IRepoProviderClient, ProviderAuth, RepoMeta

DEFAULT_BASE_URL = "https://api.github.com"


class GitHubRepoProviderClient(IRepoProviderClient):
    def __init__(self, api_base_url: str | None = None) -> None:
        base = (api_base_url or DEFAULT_BASE_URL).rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=base,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "AnalyzeRepo/1.0",
            },
            timeout=30.0,
        )

    def _auth_headers(self, auth: ProviderAuth) -> dict[str, str]:
        token = auth.secret_ref_or_token
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def _parse_url(web_url: str) -> tuple[str, str]:
        normalized = (
            web_url.strip()
            .removeprefix("https://")
            .removeprefix("http://")
            .removeprefix("github.com/")
            .rstrip("/")
        )
        if normalized.endswith(".git"):
            normalized = normalized[:-4]
        parts = [p for p in normalized.split("/") if p]
        if len(parts) < 2:
            raise ValueError(f"Invalid GitHub URL: {web_url}")
        return parts[0], parts[1]

    async def get_repo_meta(self, web_url: str, auth: ProviderAuth) -> RepoMeta:
        owner, repo = self._parse_url(web_url)
        resp = await self._client.get(f"/repos/{owner}/{repo}", headers=self._auth_headers(auth))
        resp.raise_for_status()
        data = resp.json()
        return RepoMeta(
            name=f"{owner}/{repo}",
            web_url_normalized=f"https://github.com/{owner}/{repo}",
            clone_url=data["clone_url"],
            default_branch=data["default_branch"],
            provider_repo_id=str(data["id"]),
            provider_workspace_id=str(data["owner"]["id"]),
            provider_code="github",
        )

    async def get_branches(self, meta: RepoMeta, auth: ProviderAuth) -> list[str]:
        owner, repo = meta.name.split("/", 1)
        branches: list[str] = []
        page = 1
        while True:
            resp = await self._client.get(
                f"/repos/{owner}/{repo}/branches",
                params={"per_page": 100, "page": page},
                headers=self._auth_headers(auth),
            )
            resp.raise_for_status()
            data = resp.json()
            if not data:
                break
            branches.extend(b["name"] for b in data)
            if len(data) < 100:
                break
            page += 1
        return branches

    async def aclose(self) -> None:
        await self._client.aclose()
