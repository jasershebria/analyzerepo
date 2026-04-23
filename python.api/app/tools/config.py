from __future__ import annotations

from typing import Any

from ._base import BaseTool, ToolDef
from . import _state


class ConfigTool(BaseTool):
    name = "config"
    description = "Get or set session configuration settings. Omit value to read current setting."

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "setting": {
                    "type": "string",
                    "description": 'Setting key, e.g. "theme" or "model"',
                },
                "value": {
                    "description": "New value (omit to get current value)",
                },
            },
            required=["setting"],
        )

    async def _run(self, args: dict[str, Any]) -> Any:
        key: str = args["setting"]
        if "value" not in args or args["value"] is None:
            return {key: _state.CONFIG.get(key)}
        _state.CONFIG[key] = args["value"]
        return f"Set {key} = {args['value']}"
