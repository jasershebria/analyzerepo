from __future__ import annotations

from urllib.parse import quote

import httpx

from app.services.provider_clients.base import IRepoProviderClient, ProviderAuth, RepoMeta

DEFAULT_BASE_URL = "https://gitlab.com/api/v4"


class GitLabRepoProviderClient(IRepoProviderClient):
    def __init__(self, api_base_url: str | None = None) -> None:
        base = (api_base_url or DEFAULT_BASE_URL).rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=base,
            headers={"Accept": "application/json", "User-Agent": "AnalyzeRepo/1.0"},
            timeout=30.0,
        )

    def _auth_headers(self, auth: ProviderAuth) -> dict[str, str]:
        if auth.auth_type.lower() == "token":
            return {"PRIVATE-TOKEN": auth.secret_ref_or_token}
        return {"Authorization": f"Bearer {auth.secret_ref_or_token}"}

    @staticmethod
    def _parse_url(web_url: str) -> tuple[str, str]:
        normalized = (
            web_url.strip()
            .removeprefix("https://")
            .removeprefix("http://")
            .rstrip("/")
        )
        if normalized.endswith(".git"):
            normalized = normalized[:-4]
        if normalized.lower().startswith("gitlab.com/"):
            normalized = normalized[len("gitlab.com/"):]
        parts = [p for p in normalized.split("/") if p]
        if len(parts) < 2:
            raise ValueError(f"Invalid GitLab URL: {web_url}")
        project = parts[-1]
        namespace = "/".join(parts[:-1])
        return namespace, project

    async def get_repo_meta(self, web_url: str, auth: ProviderAuth) -> RepoMeta:
        namespace, project = self._parse_url(web_url)
        path = quote(f"{namespace}/{project}", safe="")
        resp = await self._client.get(f"/projects/{path}", headers=self._auth_headers(auth))
        resp.raise_for_status()
        data = resp.json()
        ns_id = str(data.get("namespace", {}).get("id", ""))
        return RepoMeta(
            name=f"{namespace}/{project}",
            web_url_normalized=f"https://gitlab.com/{namespace}/{project}",
            clone_url=data["http_url_to_repo"],
            default_branch=data.get("default_branch") or "main",
            provider_repo_id=str(data["id"]),
            provider_workspace_id=ns_id or None,
            provider_code="gitlab",
        )

    async def get_branches(self, meta: RepoMeta, auth: ProviderAuth) -> list[str]:
        encoded = quote(meta.name, safe="")
        branches: list[str] = []
        page = 1
        while True:
            resp = await self._client.get(
                f"/projects/{encoded}/repository/branches",
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
