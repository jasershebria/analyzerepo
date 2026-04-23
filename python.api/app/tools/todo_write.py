from __future__ import annotations

from typing import Any

from ._base import BaseTool, ToolDef
from . import _state


class TodoWriteTool(BaseTool):
    name = "todo_write"
    description = (
        "Replace the entire task checklist with a new list. "
        "Each todo has id, content, status (pending/in_progress/completed), "
        "activeForm (present-continuous form), and priority."
    )

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "todos": {
                    "type": "array",
                    "description": "Full todo list (replaces existing)",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "content": {"type": "string"},
                            "status": {
                                "type": "string",
                                "enum": ["pending", "in_progress", "completed"],
                            },
                            "activeForm": {"type": "string"},
                            "priority": {
                                "type": "string",
                                "enum": ["high", "medium", "low"],
                            },
                        },
                        "required": ["id", "content", "status"],
                    },
                }
            },
            required=["todos"],
        )

    async def _run(self, args: dict[str, Any]) -> str:
        todos: list[dict] = args["todos"]
        _state.TODO_LIST.clear()
        _state.TODO_LIST.extend(todos)
        return f"Todo list updated ({len(todos)} item{'s' if len(todos) != 1 else ''})"
