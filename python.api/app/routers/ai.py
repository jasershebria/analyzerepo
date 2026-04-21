from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.routing import CamelCaseRoute
from app.db.session import get_db
from app.schemas.ai import AIChatRequest, AIChatResponse, AIChatWithHistoryRequest
from app.services.ai_service import AIChatService
from app.services.repo_sync_service import RepoSyncService

router = APIRouter(prefix="/ai", tags=["AI"], route_class=CamelCaseRoute)

_ai_service = AIChatService()


@router.post("/chat", response_model=AIChatResponse)
async def chat(request: Request) -> AIChatResponse:
    body = await request.json()
    req = AIChatRequest.model_validate(body)
    reply = await _ai_service.chat(req.prompt, req.system_prompt)
    return AIChatResponse(reply=reply)


@router.post("/chat/history", response_model=AIChatResponse)
async def chat_with_history(request: Request, db: AsyncSession = Depends(get_db)) -> AIChatResponse:
    body = await request.json()
    req = AIChatWithHistoryRequest.model_validate(body)

    messages: list[tuple[str, str]] = []
    if req.system_prompt:
        messages.append(("system", req.system_prompt))
    for msg in req.messages:
        messages.append((msg.role, msg.content))

    tool_executor = None
    if req.repo_id:
        repo_id = uuid.UUID(req.repo_id)
        sync_svc = RepoSyncService(db)

        workspace = Path(settings.git_clone_base_path)

        def resolve(p: str) -> Path:
            path = Path(p)
            if not path.is_absolute():
                path = workspace / p
            return path

        async def tool_executor(name: str, args: dict) -> str:
            if name == "sync_repository":
                result = await sync_svc.sync(repo_id)
                return json.dumps(result)
            if name == "analyze_repository":
                result = await sync_svc.analyze(repo_id)
                return json.dumps({k: v for k, v in result.items() if k != "fileTree"} | {"fileTree": result.get("fileTree", [])[:100]})
            if name == "read_file":
                path = resolve(args.get("path", ""))
                if not path.exists():
                    return f"File not found: {path}"
                return path.read_text(encoding="utf-8", errors="replace")[:8000]
            if name == "write_file":
                path = resolve(args.get("path", ""))
                content = args.get("content", "")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                return f"Written {len(content)} chars to {path}"
            if name == "edit_file":
                path = resolve(args.get("path", ""))
                if not path.exists():
                    return f"File not found: {path}"
                old = args.get("old", "")
                new = args.get("new", "")
                original = path.read_text(encoding="utf-8")
                if old not in original:
                    return f"Text not found in {path}: {old[:80]}"
                path.write_text(original.replace(old, new, 1), encoding="utf-8")
                return f"Edited {path} successfully"
            if name == "rename_file":
                path = resolve(args.get("path", ""))
                new_name = args.get("new_name", "")
                if not path.exists():
                    return f"File not found: {path}"
                new_path = path.parent / new_name
                try:
                    shutil.move(str(path), str(new_path))
                except Exception as exc:
                    return f"Rename failed: {exc}"
                return f"Renamed {path.name} → {new_name}"
            return f"Unknown tool: {name}"

    reply = await _ai_service.chat_with_history(messages, tool_executor=tool_executor)
    return AIChatResponse(reply=reply)
