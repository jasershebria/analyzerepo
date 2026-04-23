from __future__ import annotations

from typing import Any

from ._base import BaseTool, ToolDef


class RemoteTriggerTool(BaseTool):
    name = "remote_trigger"
    description = (
        "Manage scheduled remote agent triggers via the Anthropic API. "
        "Actions: list, get, create, update, run."
    )

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "action": {
                    "type": "string",
                    "enum": ["list", "get", "create", "update", "run"],
                    "description": "Operation to perform",
                },
                "trigger_id": {
                    "type": "string",
                    "description": "Trigger ID (required for get, update, run)",
                },
                "body": {
                    "type": "object",
                    "description": "JSON body for create/update",
                },
            },
            required=["action"],
        )

    async def _run(self, args: dict[str, Any]) -> Any:
        import httpx
        import os

        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            return {"error": "ANTHROPIC_API_KEY not set"}

        action: str = args["action"]
        trigger_id: str | None = args.get("trigger_id")
        body: dict | None = args.get("body")
        base = "https://api.anthropic.com/v1/code/triggers"

        url = f"{base}/{trigger_id}" if trigger_id and action in ("get", "update", "run") else base
        if action == "run":
            url = f"{base}/{trigger_id}/run"

        method = {
            "list": "GET",
            "get": "GET",
            "create": "POST",
            "update": "PUT",
            "run": "POST",
        }[action]

        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.request(method, url, json=body, headers=headers)
        return {"status": resp.status_code, "body": resp.json()}
