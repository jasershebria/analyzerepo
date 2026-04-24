"""LangGraph-based AgentService. Replaces the hand-rolled OpenAI SDK loop."""
from __future__ import annotations

import json
import time
from collections.abc import AsyncGenerator
from typing import Any

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from app.schemas.agent import AgentMessage, AgentRunRequest, AgentRunResult

_SYSTEM_PROMPT = """\
You are an autonomous software engineering agent. You have access to tools for \
reading/writing files, running shell commands, searching code, and browsing the web. \
Use tools to accomplish tasks — never give manual instructions to the user. \
Always act; never ask the user to do something you can do yourself.\
"""


class AgentService:
    """Stateless service. The compiled LangGraph graph is a module-level singleton."""

    async def run(self, req: AgentRunRequest) -> AgentRunResult:
        from app.agent.graph import get_graph

        start = time.monotonic()

        messages: list[BaseMessage] = [
            SystemMessage(content=req.system_prompt or _SYSTEM_PROMPT)
        ]
        for m in req.history:
            messages.append(_agent_message_to_lc(m))
        messages.append(HumanMessage(content=req.prompt))

        # Each "round" = call_model + tools node; +1 for the final clean exit.
        recursion_limit = req.max_rounds * 2 + 1

        try:
            final_state = await get_graph().ainvoke(
                {"messages": messages},
                config={"recursion_limit": recursion_limit},
            )
        except Exception as exc:
            # Catches GraphRecursionError and any unexpected graph errors.
            if "recursion" in str(exc).lower():
                return AgentRunResult(
                    final_response="Reached maximum tool call rounds without a final answer.",
                    tool_calls_made=req.max_rounds,
                    elapsed_ms=int((time.monotonic() - start) * 1000),
                    messages=[_lc_to_wire(m) for m in messages],
                )
            raise

        all_messages: list[BaseMessage] = list(final_state["messages"])

        tool_calls_made = sum(
            len(m.tool_calls)
            for m in all_messages
            if isinstance(m, AIMessage) and m.tool_calls
        )

        final_response = ""
        for msg in reversed(all_messages):
            if isinstance(msg, AIMessage) and not msg.tool_calls:
                content = msg.content
                final_response = content if isinstance(content, str) else json.dumps(content)
                break

        return AgentRunResult(
            final_response=final_response,
            tool_calls_made=tool_calls_made,
            elapsed_ms=int((time.monotonic() - start) * 1000),
            messages=[_lc_to_wire(m) for m in all_messages],
        )

    async def run_stream(self, req: AgentRunRequest) -> AsyncGenerator[dict[str, Any], None]:
        """Stream agent events as dicts suitable for SSE.

        Uses a direct text-based tool-call loop (same pattern as AIChatService)
        so it works with models that output JSON in the response text rather than
        using native API-level function calling.

        Event shapes:
          {"type": "tool_start", "tool": str, "input": dict}
          {"type": "tool_end",   "tool": str, "output": str}
          {"type": "plan",       "tasks": list}
          {"type": "answer",     "content": str}
          {"type": "error",      "message": str}
        """
        from app.services.ai_service import _try_parse_tool_call
        from app.tools import get_all

        # Build tool registry: name → BaseTool instance
        tool_registry = {t.name: t for t in get_all()}

        # Describe tools for the system prompt
        tool_lines = "\n".join(
            f"- {t.name}: {t.description}" for t in tool_registry.values()
        )
        system_content = (req.system_prompt or _SYSTEM_PROMPT) + (
            "\n\n"
            "## HOW TO CALL TOOLS — READ CAREFULLY\n"
            "When you need a tool, output EXACTLY this on its own line — nothing else:\n"
            '{"name": "tool_name", "arguments": {"key": "value"}}\n'
            "\n"
            "ABSOLUTE RULES:\n"
            "- Output raw JSON only. No ```json``` code fences. No markdown.\n"
            "- Do NOT say 'I will use', 'Here is how', or explain the tool call.\n"
            "- Do NOT output example JSON — output the real call and it will execute.\n"
            "- One tool call per response. After seeing the result, continue.\n"
            "- If no tool is needed, reply in plain text.\n"
            "\n"
            "Available tools:\n"
            + tool_lines
        )

        messages: list[dict[str, str]] = [{"role": "system", "content": system_content}]
        for m in req.history:
            messages.append({"role": m.role, "content": m.content or ""})
        messages.append({"role": "user", "content": req.prompt})

        try:
            from openai import AsyncOpenAI
            from app.core.config import settings
            client = AsyncOpenAI(base_url=settings.ai_base_url, api_key=settings.ai_api_key)
            model = settings.ai_model

            for _ in range(req.max_rounds):
                resp = await client.chat.completions.create(model=model, messages=messages)
                content: str = resp.choices[0].message.content or ""

                parsed = _try_parse_tool_call(content)
                if not parsed:
                    yield {"type": "answer", "content": content}
                    return

                fn_name, fn_args = parsed
                yield {"type": "tool_start", "tool": fn_name, "input": fn_args}

                if fn_name == "todo_write":
                    yield {"type": "plan", "tasks": fn_args.get("todos") or []}

                tool = tool_registry.get(fn_name)
                if tool:
                    try:
                        result = await tool.call(fn_args)
                    except Exception as exc:
                        result = f"Error running {fn_name}: {exc}"
                else:
                    result = f"Unknown tool '{fn_name}'. Available: {', '.join(tool_registry)}"

                yield {"type": "tool_end", "tool": fn_name, "output": result[:2000]}

                messages.append({"role": "assistant", "content": content})
                messages.append({
                    "role": "user",
                    "content": f"Tool result for {fn_name}:\n{result}\n\nContinue.",
                })

            yield {"type": "answer", "content": "Reached maximum tool rounds without a final answer."}

        except Exception as exc:
            yield {"type": "error", "message": str(exc)}


def _agent_message_to_lc(m: AgentMessage) -> BaseMessage:
    content = m.content or ""
    if m.role == "system":
        return SystemMessage(content=content)
    if m.role == "user":
        return HumanMessage(content=content)
    if m.role == "tool":
        return ToolMessage(content=content, tool_call_id=m.tool_call_id or "")
    return AIMessage(content=content)


def _lc_to_wire(msg: BaseMessage) -> dict[str, Any]:
    if isinstance(msg, SystemMessage):
        return {"role": "system", "content": _str(msg.content)}
    if isinstance(msg, HumanMessage):
        return {"role": "user", "content": _str(msg.content)}
    if isinstance(msg, AIMessage):
        entry: dict[str, Any] = {"role": "assistant", "content": _str(msg.content)}
        if msg.tool_calls:
            entry["tool_calls"] = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc["args"]),
                    },
                }
                for tc in msg.tool_calls
            ]
        return entry
    if isinstance(msg, ToolMessage):
        return {
            "role": "tool",
            "tool_call_id": msg.tool_call_id,
            "content": _str(msg.content),
        }
    return {"role": "unknown", "content": _str(msg.content)}


def _str(content: Any) -> str:
    return content if isinstance(content, str) else json.dumps(content, default=str)
