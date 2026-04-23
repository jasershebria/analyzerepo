from __future__ import annotations

from typing import Any

from ._base import BaseTool, ToolDef


class AgentTool(BaseTool):
    name = "agent"
    description = (
        "Spawn a sub-agent to handle a complex, multi-step task. "
        "The sub-agent runs with its own tool access and returns a result."
    )

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "description": {
                    "type": "string",
                    "description": "3-5 word description of the sub-agent's task",
                },
                "prompt": {"type": "string", "description": "Full task instructions for the sub-agent"},
                "subagent_type": {
                    "type": "string",
                    "description": "Agent specialization (e.g. 'Explore', 'Plan')",
                },
                "model": {
                    "type": "string",
                    "enum": ["sonnet", "opus", "haiku"],
                    "description": "Model override for the sub-agent",
                },
                "run_in_background": {
                    "type": "boolean",
                    "description": "Run the agent as a background task",
                },
            },
            required=["description", "prompt"],
        )

    async def _run(self, args: dict[str, Any]) -> str:
        from app.agent.service import AgentService
        from app.schemas.agent import AgentRunRequest

        svc = AgentService()
        req = AgentRunRequest(
            prompt=args["prompt"],
            system_prompt=f"You are a specialized sub-agent. Task: {args.get('description', '')}",
        )
        result = await svc.run(req)
        return result.final_response
