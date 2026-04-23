from __future__ import annotations

from typing import Any

from ._base import BaseTool, ToolDef
from . import _state


class TaskListTool(BaseTool):
    name = "task_list"
    description = "List all tasks in the current session."

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={},
        )

    async def _run(self, args: dict[str, Any]) -> list[dict]:
        tasks = list(_state.TASKS.values())
        # Remove completed task IDs from blocked_by lists
        completed = {t["id"] for t in tasks if t.get("status") == "completed"}
        for t in tasks:
            t["blocked_by"] = [b for b in t.get("blocked_by", []) if b not in completed]
        return tasks
