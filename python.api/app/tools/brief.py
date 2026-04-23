from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ._base import BaseTool, ToolDef
from . import _state

log = logging.getLogger(__name__)


class BriefTool(BaseTool):
    name = "send_user_message"
    description = (
        "Send a formatted message to the user with optional file attachments. "
        "Use status='proactive' for background updates."
    )

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "message": {"type": "string", "description": "Markdown-formatted message"},
                "attachments": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Absolute file paths to attach",
                },
                "status": {
                    "type": "string",
                    "enum": ["normal", "proactive"],
                    "description": "Message type (default: normal)",
                },
            },
            required=["message"],
        )

    async def _run(self, args: dict[str, Any]) -> str:
        message: str = args["message"]
        attachments: list[str] = args.get("attachments") or []
        status: str = args.get("status", "normal")

        valid_attachments = [a for a in attachments if Path(a).exists()]
        missing = [a for a in attachments if not Path(a).exists()]

        entry = {"message": message, "status": status, "attachments": valid_attachments}
        _state.MESSAGES.append(entry)
        log.info("BriefTool [%s]: %s", status, message[:120])

        parts = [f"Message delivered ({status})"]
        if valid_attachments:
            parts.append(f"Attachments: {', '.join(valid_attachments)}")
        if missing:
            parts.append(f"Missing files (skipped): {', '.join(missing)}")
        return " | ".join(parts)
