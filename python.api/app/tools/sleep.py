from __future__ import annotations

import asyncio
from typing import Any

from ._base import BaseTool, ToolDef


class SleepTool(BaseTool):
    name = "sleep"
    description = "Wait for a specified duration without holding a shell process."

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "duration_ms": {
                    "type": "integer",
                    "description": "Duration to sleep in milliseconds",
                }
            },
            required=["duration_ms"],
        )

    async def _run(self, args: dict[str, Any]) -> str:
        ms: int = args["duration_ms"]
        await asyncio.sleep(ms / 1000)
        return f"Slept for {ms}ms"
