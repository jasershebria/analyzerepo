from __future__ import annotations

import logging
from pathlib import Path

from app.core.config import settings

log = logging.getLogger(__name__)


class MemoryService:
    """Reads project memory (CLAUDE.md) from a cloned repository workspace."""

    def read_claude_md(self, repo_id: str) -> str | None:
        """Return the contents of CLAUDE.md from the repo workspace, or None if not found."""
        workspace = self._find_workspace(repo_id)
        if workspace is None:
            return None

        claude_md = workspace / "CLAUDE.md"
        if not claude_md.exists():
            return None

        try:
            content = claude_md.read_text(encoding="utf-8", errors="replace").strip()
            log.info("Loaded CLAUDE.md for repo %s (%d chars)", repo_id, len(content))
            return content or None
        except Exception:
            log.exception("Failed to read CLAUDE.md for repo %s", repo_id)
            return None

    def _find_workspace(self, repo_id: str) -> Path | None:
        """Find the workspace directory for a repo by scanning the clone base path."""
        base = Path(settings.git_clone_base_path)
        if not base.exists():
            return None

        # Walk up to 3 levels deep to find a .git dir linked to this repo
        for git_dir in base.rglob(".git"):
            workspace = git_dir.parent
            if workspace.exists():
                return workspace

        return None
