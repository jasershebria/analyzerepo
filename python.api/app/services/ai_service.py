from __future__ import annotations

import json
import logging
from typing import Callable, Awaitable

from openai import AsyncOpenAI

from app.core.config import settings

log = logging.getLogger(__name__)

_TOOL_INSTRUCTIONS = """\
You are an autonomous software engineering agent. Use tools to act — never give manual instructions.

To call a tool output ONLY this JSON (no markdown, no extra text):
{"name": "<tool>", "arguments": {<args>}}

Tools:
- analyze_repository — list all files. args: {}
- read_file — read a file. args: {"path": "<absolute path>"}
- write_file — overwrite a file. args: {"path": "<absolute path>", "content": "<content>"}
- edit_file — replace text in file. args: {"path": "<absolute path>", "old": "<text>", "new": "<text>"}
- rename_file — rename a file. args: {"path": "<absolute path>", "new_name": "<filename only>"}
- sync_repository — clone/pull repo. args: {}

Rules:
1. ALWAYS call analyze_repository first if you don't know the file tree.
2. ALWAYS call read_file before editing or writing a file.
3. Use the full absolute path from the workspace (e.g. D:\\NoxAlarmApp\\package.json).
4. Never say "I don't have that file" — call read_file instead.
5. After every tool result, either call another tool or confirm what you did.\
"""

ToolExecutor = Callable[[str, dict], Awaitable[str]]


class AIChatService:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            base_url=f"{settings.ollama_base_url.rstrip('/')}/v1",
            api_key="ollama",
        )
        self._model = settings.ollama_model

    async def chat(self, prompt: str, system_prompt: str | None = None) -> str:
        messages: list[dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        resp = await self._client.chat.completions.create(model=self._model, messages=messages)
        return resp.choices[0].message.content or ""

    async def chat_with_history(
        self,
        messages: list[tuple[str, str]],
        tool_executor: ToolExecutor | None = None,
    ) -> str:
        formatted: list[dict] = []
        for role, content in messages:
            if role == "system" and tool_executor:
                content = f"{content}\n\n{_TOOL_INSTRUCTIONS}"
            formatted.append({"role": role, "content": content})

        for _ in range(10):  # max tool call rounds
            resp = await self._client.chat.completions.create(
                model=self._model, messages=formatted
            )
            content = resp.choices[0].message.content or ""

            if tool_executor:
                parsed = _try_parse_tool_call(content)
                if parsed:
                    fn_name, fn_args = parsed
                    if fn_name not in _KNOWN_TOOLS:
                        # Model hallucinated a tool — correct it and retry
                        formatted.append({"role": "assistant", "content": content})
                        formatted.append({"role": "user", "content": f"Unknown tool '{fn_name}'. Only use: {', '.join(sorted(_KNOWN_TOOLS))}. Try again."})
                        continue
                    log.info("AI tool call: %s(%s)", fn_name, fn_args)
                    try:
                        result = await tool_executor(fn_name, fn_args)
                    except Exception as exc:
                        result = f"Error: {exc}"
                    formatted.append({"role": "assistant", "content": content})
                    formatted.append({"role": "user", "content": f"Tool result for {fn_name}:\n{result}\n\nNow answer the user's question using this information."})
                    continue

            return content

        return "Reached tool call limit without a final answer."


_KNOWN_TOOLS = {"sync_repository", "analyze_repository", "read_file", "write_file", "edit_file", "rename_file"}


def _try_parse_tool_call(text: str) -> tuple[str, dict] | None:
    """Return (function_name, args) if text looks like a tool call JSON, else None."""
    import re
    stripped = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    stripped = re.sub(r"\s*```$", "", stripped.strip())
    try:
        data = json.loads(stripped)
        if isinstance(data, dict) and "name" in data:
            # Accept known tools; reject hallucinated ones and return a sentinel
            return data["name"], data.get("arguments") or data.get("parameters") or {}
    except (json.JSONDecodeError, ValueError):
        pass
    return None
