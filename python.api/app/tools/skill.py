from __future__ import annotations

from typing import Any

from ._base import BaseTool, ToolDef


class SkillTool(BaseTool):
    name = "skill"
    description = (
        "Invoke a named skill or slash command (e.g. /review, /init). "
        "Skills are pre-defined prompts that run in isolated agent contexts."
    )

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "command": {
                    "type": "string",
                    "description": "Skill name (without leading slash), e.g. 'review'",
                },
                "args": {"type": "string", "description": "Optional arguments for the skill"},
                "model": {
                    "type": "string",
                    "description": "Model override for skill execution",
                },
            },
            required=["command"],
        )

    async def _run(self, args: dict[str, Any]) -> str:
        return (
            f"Skill '{args['command']}' invocation is not yet implemented in the Python agent. "
            "Use the AgentTool with a specific prompt instead."
        )
