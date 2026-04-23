from __future__ import annotations

import uuid
from typing import Any

from ._base import BaseTool, ToolDef
from . import _state


class TaskCreateTool(BaseTool):
    name = "task_create"
    description = "Create a new task and add it to the task list."

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "subject": {"type": "string", "description": "Short task title"},
                "description": {"type": "string", "description": "What needs to be done"},
                "active_form": {
                    "type": "string",
                    "description": "Present-continuous form shown in spinner, e.g. 'Running tests'",
                },
                "metadata": {
                    "type": "object",
                    "description": "Arbitrary metadata key-value pairs",
                },
            },
            required=["subject", "description"],
        )

    async def _run(self, args: dict[str, Any]) -> dict:
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "subject": args["subject"],
            "description": args["description"],
            "active_form": args.get("active_form"),
            "status": "pending",
            "metadata": args.get("metadata") or {},
            "blocks": [],
            "blocked_by": [],
            "owner": None,
        }
        _state.TASKS[task_id] = task
        return {"taskId": task_id, "task": task}
