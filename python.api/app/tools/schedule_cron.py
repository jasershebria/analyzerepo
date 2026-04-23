from __future__ import annotations

import uuid
from typing import Any

from ._base import BaseTool, ToolDef
from . import _state

_MAX_JOBS = 50


class ScheduleCronTool(BaseTool):
    name = "cron_create"
    description = (
        "Schedule a recurring or one-shot prompt on a cron schedule. "
        "Returns a job ID that can be used to delete the job."
    )

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "cron": {
                    "type": "string",
                    "description": '5-field cron expression, e.g. "*/5 * * * *" (minute hour dom month dow)',
                },
                "prompt": {"type": "string", "description": "Prompt to enqueue at each fire time"},
                "recurring": {
                    "type": "boolean",
                    "description": "Repeat on schedule (default: true)",
                },
                "durable": {
                    "type": "boolean",
                    "description": "Persist to disk across restarts (default: false)",
                },
            },
            required=["cron", "prompt"],
        )

    async def _run(self, args: dict[str, Any]) -> dict:
        if len(_state.CRONS) >= _MAX_JOBS:
            raise ValueError(f"Maximum {_MAX_JOBS} cron jobs reached")

        job_id = str(uuid.uuid4())[:8]
        job = {
            "id": job_id,
            "cron": args["cron"],
            "prompt": args["prompt"],
            "recurring": args.get("recurring", True),
            "durable": args.get("durable", False),
            "status": "active",
        }
        _state.CRONS[job_id] = job
        return {"jobId": job_id, "job": job}


class CronDeleteTool(BaseTool):
    name = "cron_delete"
    description = "Delete a scheduled cron job by its ID."

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "id": {"type": "string", "description": "Job ID returned by cron_create"},
            },
            required=["id"],
        )

    async def _run(self, args: dict[str, Any]) -> str:
        job_id: str = args["id"]
        if job_id not in _state.CRONS:
            raise KeyError(f"Cron job '{job_id}' not found")
        del _state.CRONS[job_id]
        return f"Cron job '{job_id}' deleted"


class CronListTool(BaseTool):
    name = "cron_list"
    description = "List all active cron jobs."

    def definition(self) -> ToolDef:
        return ToolDef(name=self.name, description=self.description, properties={})

    async def _run(self, args: dict[str, Any]) -> list[dict]:
        return list(_state.CRONS.values())
