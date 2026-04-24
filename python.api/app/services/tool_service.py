from __future__ import annotations

import json
import logging
import shutil
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.repository import Repository
from app.services.repo_sync_service import RepoSyncService

log = logging.getLogger(__name__)

class ToolService:
    def __init__(self, db: AsyncSession, repo_id: uuid.UUID) -> None:
        self._db = db
        self._repo_id = repo_id
        self._sync_svc = RepoSyncService(db)
        self._workspace = Path(settings.git_clone_base_path)

    def _resolve(self, p: str) -> Path:
        path = Path(p)
        if not path.is_absolute():
            path = self._workspace / p
        return path

    async def execute_tool(self, name: str, args: dict) -> str:
        log.info("Executing tool: %s with args: %s", name, args)
        try:
            if name == "sync_repository":
                result = await self._sync_svc.sync(self._repo_id)
                return json.dumps(result)
            
            if name == "analyze_repository":
                result = await self._sync_svc.analyze(self._repo_id)
                summary = {k: v for k, v in result.items() if k != "fileTree"}
                summary["fileTree"] = result.get("fileTree", [])
                return json.dumps(summary)
            
            if name == "read_file":
                path = self._resolve(args.get("path", ""))
                if not path.exists():
                    return f"File not found: {path}"
                return path.read_text(encoding="utf-8", errors="replace")
            
            if name == "write_file":
                path = self._resolve(args.get("path", ""))
                content = args.get("content", "")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                return f"Written {len(content)} chars to {path}"
            
            if name == "edit_file":
                path = self._resolve(args.get("path", ""))
                if not path.exists():
                    return f"File not found: {path}"
                old = args.get("old", "")
                new = args.get("new", "")
                original = path.read_text(encoding="utf-8")
                if old not in original:
                    return f"Match not found in {path}. Ensure 'old' text is exact."
                path.write_text(original.replace(old, new, 1), encoding="utf-8")
                return f"Edited {path} successfully"
            
            if name == "rename_file":
                path = self._resolve(args.get("path", ""))
                new_name = args.get("new_name", "")
                if not path.exists():
                    return f"File not found: {path}"
                new_path = path.parent / new_name
                shutil.move(str(path), str(new_path))
                return f"Renamed {path.name} → {new_name}"

            return f"Unknown tool: {name}"
        except Exception as e:
            log.exception("Tool execution failed")
            return f"Error executing {name}: {str(e)}"
