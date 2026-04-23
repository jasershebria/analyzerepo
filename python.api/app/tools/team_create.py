from __future__ import annotations

import uuid
from typing import Any

from ._base import BaseTool, ToolDef
from . import _state


class TeamCreateTool(BaseTool):
    name = "team_create"
    description = "Create a new agent team context for multi-agent coordination."

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "name": {"type": "string", "description": "Team name"},
                "description": {"type": "string", "description": "Team purpose"},
                "members": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Agent names or IDs",
                },
            },
            required=["name"],
        )

    async def _run(self, args: dict[str, Any]) -> dict:
        team_id = str(uuid.uuid4())[:8]
        team = {
            "id": team_id,
            "name": args["name"],
            "description": args.get("description", ""),
            "members": args.get("members") or [],
        }
        if "teams" not in _state.CONFIG:
            _state.CONFIG["teams"] = {}
        _state.CONFIG["teams"][team_id] = team
        return {"teamId": team_id, "team": team}


class TeamDeleteTool(BaseTool):
    name = "team_delete"
    description = "Delete an agent team by ID."

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "team_id": {"type": "string", "description": "Team ID to delete"},
            },
            required=["team_id"],
        )

    async def _run(self, args: dict[str, Any]) -> str:
        teams: dict = _state.CONFIG.get("teams", {})
        team_id: str = args["team_id"]
        if team_id not in teams:
            raise KeyError(f"Team '{team_id}' not found")
        del teams[team_id]
        return f"Team '{team_id}' deleted"
