from __future__ import annotations

from typing import Any

from ._base import BaseTool, ToolDef
from . import _state


class EnterPlanModeTool(BaseTool):
    name = "enter_plan_mode"
    description = (
        "Switch to plan mode for exploration and design. "
        "In plan mode you can read files and research without making changes."
    )

    def definition(self) -> ToolDef:
        return ToolDef(name=self.name, description=self.description, properties={})

    async def _run(self, args: dict[str, Any]) -> str:
        _state.PLAN_MODE = True
        return "Entered plan mode. Use ExitPlanMode when ready to implement."
