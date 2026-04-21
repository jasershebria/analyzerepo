from __future__ import annotations

import base64

import httpx

from app.services.provider_clients.base import IRepoProviderClient, ProviderAuth, RepoMeta

DEFAULT_BASE_URL = "https://api.bitbucket.org/2.0"


class BitbucketRepoProviderClient(IRepoProviderClient):
    def __init__(self, api_base_url: str | None = None) -> None:
        base = (api_base_url or DEFAULT_BASE_URL).rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=base,
            headers={"Accept": "application/json", "User-Agent": "AnalyzeRepo/1.0"},
            timeout=30.0,
        )

    def _auth_headers(self, auth: ProviderAuth) -> dict[str, str]:
        if auth.auth_type.lower() == "basic":
            encoded = base64.b64encode(auth.secret_ref_or_token.encode()).decode()
            return {"Authorization": f"Basic {encoded}"}
        return {"Authorization": f"Bearer {auth.secret_ref_or_token}"}

    @staticmethod
    def _parse_url(web_url: str) -> tuple[str, str]:
        normalized = (
            web_url.strip()
            .removeprefix("https://")
            .removeprefix("http://")
            .removeprefix("bitbucket.org/")
            .rstrip("/")
        )
        if normalized.endswith(".git"):
            normalized = normalized[:-4]
        parts = [p for p in normalized.split("/") if p]
        if len(parts) < 2:
            raise ValueError(f"Invalid Bitbucket URL: {web_url}")
        return parts[0], parts[1]

    async def get_repo_meta(self, web_url: str, auth: ProviderAuth) -> RepoMeta:
        workspace, slug = self._parse_url(web_url)
        resp = await self._client.get(
            f"/repositories/{workspace}/{slug}", headers=self._auth_headers(auth)
        )
        resp.raise_for_status()
        data = resp.json()
        clone_links = data.get("links", {}).get("clone", [])
        clone_url = next((l["href"] for l in clone_links if l.get("name") == "https"), "")
        return RepoMeta(
            name=f"{workspace}/{slug}",
            web_url_normalized=f"https://bitbucket.org/{workspace}/{slug}",
            clone_url=clone_url,
            default_branch=data.get("mainbranch", {}).get("name", "main"),
            provider_repo_id=data.get("uuid") or data.get("full_name", ""),
            provider_workspace_id=(data.get("workspace") or {}).get("uuid"),
            provider_code="bitbucket",
        )

    async def get_branches(self, meta: RepoMeta, auth: ProviderAuth) -> list[str]:
        workspace, slug = meta.name.split("/", 1)
        branches: list[str] = []
        url: str | None = f"/repositories/{workspace}/{slug}/refs/branches?pagelen=100"
        while url:
            if url.startswith("http"):
                resp = await self._client.get(url, headers=self._auth_headers(auth))
            else:
                resp = await self._client.get(url, headers=self._auth_headers(auth))
            resp.raise_for_status()
            data = resp.json()
            values = data.get("values", [])
            branches.extend(b["name"] for b in values)
            url = data.get("next")
        return branches

    async def aclose(self) -> None:
        await self._client.aclose()
