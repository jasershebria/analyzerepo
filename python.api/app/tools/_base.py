from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any


class ToolDef:
    """OpenAI function-calling tool definition."""

    def __init__(
        self,
        name: str,
        description: str,
        properties: dict[str, Any],
        required: list[str] | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self.properties = properties
        self.required = required or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.properties,
                    "required": self.required,
                },
            },
        }


class BaseTool(ABC):
    name: str = ""
    description: str = ""

    @abstractmethod
    def definition(self) -> ToolDef: ...

    @abstractmethod
    async def _run(self, args: dict[str, Any]) -> Any: ...

    async def call(self, args: dict[str, Any]) -> str:
        result = await self._run(args)
        if result is None:
            return ""
        if isinstance(result, str):
            return result
        return json.dumps(result, default=str, ensure_ascii=False)
