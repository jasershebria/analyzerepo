from __future__ import annotations

import uuid
from typing import Any

from ._base import BaseTool, ToolDef
from . import _state


class SendMessageTool(BaseTool):
    name = "send_message"
    description = (
        "Send a message to a teammate agent or broadcast to all ('*'). "
        "Used in multi-agent workflows."
    )

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "to": {
                    "type": "string",
                    "description": 'Recipient: agent name or "*" for broadcast',
                },
                "message": {"type": "string", "description": "Message content"},
                "summary": {
                    "type": "string",
                    "description": "5–10 word summary for display",
                },
            },
            required=["to", "message"],
        )

    async def _run(self, args: dict[str, Any]) -> str:
        entry = {
            "id": str(uuid.uuid4()),
            "to": args["to"],
            "message": args["message"],
            "summary": args.get("summary"),
        }
        _state.MESSAGES.append(entry)
        return f"Message sent to '{args['to']}' (id={entry['id'][:8]})"
