from __future__ import annotations

from typing import Any

from ._base import BaseTool, ToolDef
from . import _state


class TaskStopTool(BaseTool):
    name = "task_stop"
    description = "Stop or cancel a running task by ID."

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "task_id": {"type": "string", "description": "Task ID to stop"},
                "shell_id": {"type": "string", "description": "Deprecated alias for task_id"},
            },
        )

    async def _run(self, args: dict[str, Any]) -> str:
        task_id = args.get("task_id") or args.get("shell_id")
        if not task_id:
            return "No task_id provided"
        if task_id not in _state.TASKS:
            raise KeyError(f"Task '{task_id}' not found")
        _state.TASKS[task_id]["status"] = "deleted"
        return f"Task '{task_id}' stopped"
