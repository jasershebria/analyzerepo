"""LangGraph-based AgentService. Replaces the hand-rolled OpenAI SDK loop."""
from __future__ import annotations

import json
import time
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
