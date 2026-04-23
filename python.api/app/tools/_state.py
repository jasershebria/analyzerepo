"""Shared in-memory state for all tools (reset on server restart)."""
from __future__ import annotations

from typing import Any

TODO_LIST: list[dict] = []
TASKS: dict[str, dict] = {}
CRONS: dict[str, dict] = {}
CONFIG: dict[str, Any] = {}
MESSAGES: list[dict] = []
PLAN_MODE: bool = False
WORKTREE: dict | None = None   # {"path": str, "branch": str, "original_cwd": str}
