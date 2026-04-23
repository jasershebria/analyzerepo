from __future__ import annotations

from typing import Any

from ._base import BaseTool, ToolDef
from . import _state


class ExitPlanModeTool(BaseTool):
    name = "exit_plan_mode"
    description = "Exit plan mode and return to normal implementation mode."

    def definition(self) -> ToolDef:
        return ToolDef(name=self.name, description=self.description, properties={})

    async def _run(self, args: dict[str, Any]) -> str:
        _state.PLAN_MODE = False
        return "Exited plan mode. Implementation is now allowed."
