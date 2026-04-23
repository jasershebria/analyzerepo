from __future__ import annotations

from typing import Any

from ._base import BaseTool, ToolDef
from . import _state


class TaskUpdateTool(BaseTool):
    name = "task_update"
    description = "Update an existing task's fields, status, or dependency relationships."

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "task_id": {"type": "string", "description": "Task ID to update"},
                "subject": {"type": "string", "description": "New title"},
                "description": {"type": "string", "description": "New description"},
                "active_form": {"type": "string", "description": "New active form"},
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "completed", "deleted"],
                },
                "add_blocks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Task IDs that this task blocks",
                },
                "add_blocked_by": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Task IDs that block this task",
                },
                "owner": {"type": "string", "description": "Owning agent name"},
                "metadata": {"type": "object"},
            },
            required=["task_id"],
        )

    async def _run(self, args: dict[str, Any]) -> dict:
        task_id: str = args["task_id"]
        if task_id not in _state.TASKS:
            raise KeyError(f"Task '{task_id}' not found")
        task = _state.TASKS[task_id]

        for field in ("subject", "description", "active_form", "status", "owner"):
            if args.get(field) is not None:
                task[field] = args[field]
        if args.get("metadata"):
            task["metadata"].update(args["metadata"])
        for tid in args.get("add_blocks") or []:
            if tid not in task["blocks"]:
                task["blocks"].append(tid)
        for tid in args.get("add_blocked_by") or []:
            if tid not in task["blocked_by"]:
                task["blocked_by"].append(tid)

        return task
