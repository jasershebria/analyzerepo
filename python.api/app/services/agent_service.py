from __future__ import annotations

import json
import logging
import time

from openai import AsyncOpenAI

from app.core.config import settings
from app.schemas.agent import AgentRunRequest, AgentRunResult
from app.services.tools_service import ToolsService

log = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are an autonomous software engineering agent. You have access to tools for \
reading/writing files, running shell commands, searching code, and browsing the web. \
Use tools to accomplish tasks — never give manual instructions to the user. \
Always act; never ask the user to do something you can do yourself.\
"""


class AgentService:
    def __init__(self, tools_service: ToolsService) -> None:
        self._client = AsyncOpenAI(
            base_url=f"{settings.ollama_base_url.rstrip('/')}/v1",
            api_key="ollama",
        )
        self._model = settings.ollama_model
        self._tools_svc = tools_service

    async def run(self, req: AgentRunRequest) -> AgentRunResult:
        start = time.monotonic()
        tool_defs = [t.model_dump(by_alias=True) for t in self._tools_svc.get_definitions()]

        # Build initial message list from optional history
        messages: list[dict] = []
        for m in req.history:
            entry: dict = {"role": m.role}
            if m.content is not None:
                entry["content"] = m.content
            if m.tool_call_id is not None:
                entry["tool_call_id"] = m.tool_call_id
            messages.append(entry)

        # Prepend system prompt (user-supplied overrides default)
        system = req.system_prompt or _SYSTEM_PROMPT
        messages.insert(0, {"role": "system", "content": system})
        messages.append({"role": "user", "content": req.prompt})

        tool_calls_made = 0

        for _ in range(req.max_rounds):
            resp = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=tool_defs,
                tool_choice="auto",
            )
            msg = resp.choices[0].message

            # Serialize assistant turn into a plain dict for storage
            assistant_entry: dict = {"role": "assistant"}
            if msg.content:
                assistant_entry["content"] = msg.content
            if msg.tool_calls:
                assistant_entry["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ]
            messages.append(assistant_entry)

            if not msg.tool_calls:
                return AgentRunResult(
                    final_response=msg.content or "",
                    tool_calls_made=tool_calls_made,
                    elapsed_ms=int((time.monotonic() - start) * 1000),
                    messages=messages,
                )

            # Execute each tool call and append results
            for tc in msg.tool_calls:
                tool_calls_made += 1
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                log.info("Agent tool call: %s(%s)", tc.function.name, args)
                result = await self._tools_svc.execute(tc.function.name, args)
                content = result.result if result.result is not None else (result.error or "")
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": content,
                    }
                )

        return AgentRunResult(
            final_response="Reached maximum tool call rounds without a final answer.",
            tool_calls_made=tool_calls_made,
            elapsed_ms=int((time.monotonic() - start) * 1000),
            messages=messages,
        )
