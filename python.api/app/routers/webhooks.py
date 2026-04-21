from __future__ import annotations

from fastapi import APIRouter, HTTPException, Path, Request, status

from app.services.provider_clients.base import ProviderAuth
from app.services.provider_clients.factory import RepoProviderClientFactory

router = APIRouter(prefix="/webhook", tags=["Webhook"])

_factory = RepoProviderClientFactory()

_SUPPORTED_PROVIDERS = {"github", "gitlab", "bitbucket"}


@router.post(
    "/trigger/{name}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Receive a Git provider push webhook",
)
async def webhook_trigger(
    name: str = Path(..., description="Provider name: github, gitlab, bitbucket"),
    request: Request = ...,
) -> dict:
    provider = name.lower()
    if provider not in _SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown provider '{name}'. Supported: {', '.join(_SUPPORTED_PROVIDERS)}",
        )

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request body is not valid JSON.",
        )

    scan_job = _parse_scan_job(provider, payload)

    return {"accepted": True, "provider": provider, "branch": scan_job.get("branch"), "commit": scan_job.get("commit_hash")}


def _parse_scan_job(provider: str, payload: dict) -> dict:
    if provider == "github":
        repo = payload.get("repository", {})
        external_id = str(repo.get("id", ""))
        raw_ref = payload.get("ref", "")
        branch = raw_ref.removeprefix("refs/heads/")
        commit_hash = payload.get("after", "")
        return {"provider": provider, "external_id": external_id, "branch": branch, "commit_hash": commit_hash}

    if provider == "gitlab":
        repo = payload.get("project", {})
        external_id = str(repo.get("id", ""))
        raw_ref = payload.get("ref", "")
        branch = raw_ref.removeprefix("refs/heads/")
        commit_hash = payload.get("after", "")
        return {"provider": provider, "external_id": external_id, "branch": branch, "commit_hash": commit_hash}

    if provider == "bitbucket":
        push = payload.get("push", {})
        changes = push.get("changes", [{}])
        change = changes[0] if changes else {}
        new_ref = change.get("new", {})
        branch = new_ref.get("name", "")
        commit_hash = new_ref.get("target", {}).get("hash", "")
        repo = payload.get("repository", {})
        external_id = repo.get("uuid", "")
        return {"provider": provider, "external_id": external_id, "branch": branch, "commit_hash": commit_hash}

    raise ValueError(f"Unsupported provider: {provider}")
