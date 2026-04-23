from __future__ import annotations

from typing import Any

from ._base import BaseTool, ToolDef
from . import _state


class TaskGetTool(BaseTool):
    name = "task_get"
    description = "Get a specific task by its ID."

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "task_id": {"type": "string", "description": "Task ID to retrieve"},
            },
            required=["task_id"],
        )

    async def _run(self, args: dict[str, Any]) -> dict:
        task_id: str = args["task_id"]
        if task_id not in _state.TASKS:
            raise KeyError(f"Task '{task_id}' not found")
        return _state.TASKS[task_id]
