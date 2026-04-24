"""Two-phase agent orchestrator: intent detection + plan → execute.

Phase 1 — Plan:
  A fast, focused LLM call that reads the user's message and the tool list,
  then returns a structured JSON plan: {intent, steps}. This is streamed to
  the frontend as a "thinking" event so the user sees the plan before any
  tool runs.

Phase 2 — Execute:
  The normal agent loop (from AgentService.run_stream) runs with the plan
  injected into the system prompt as context. The LLM already knows what
  it intends to do, so it goes straight to calling the right tools.
"""
from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any

from openai import AsyncOpenAI

from app.core.config import settings
from app.services.ai_service import _try_parse_tool_call

_PLANNING_SYSTEM = """\
You are an intent analyzer for a coding agent. Given a user request and a list \
of available tools, output a concise execution plan as JSON.

Output ONLY this JSON object — no markdown, no explanation, no extra text:
{
  "intent": "one sentence: what the user wants to achieve",
  "steps": [
    {"step": 1, "tool": "tool_name", "purpose": "what this step achieves"},
    {"step": 2, "tool": "tool_name", "purpose": "what this step achieves"}
  ]
}

Rules:
- Only use tool names from the AVAILABLE TOOLS list.
- Keep steps minimal — use the fewest tools needed.
- If the request needs no tools (pure conversation), set "steps" to [].
- "purpose" should be one short phrase, not a sentence.
- NEVER refuse or question the request. Always produce a plan for every input.
"""


class OrchestratorService:
    """Stateless orchestrator. Call run_stream() per request."""

    async def run_stream(
        self,
        prompt: str,
        system_content: str,
        tool_registry: dict[str, Any],
        messages_so_far: list[dict[str, str]],
        max_rounds: int = 15,
    ) -> AsyncGenerator[dict[str, Any], None]:
        client = AsyncOpenAI(base_url=settings.ai_base_url, api_key=settings.ai_api_key)
        model = settings.ai_model

        # ── Phase 1: Intent detection + planning ────────────────────────────
        tool_summary = "\n".join(
            f"- {name}: {t.description}" for name, t in tool_registry.items()
        )
        plan_messages = [
            {"role": "system", "content": _PLANNING_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"User request: {prompt}\n\n"
                    f"AVAILABLE TOOLS:\n{tool_summary}"
                ),
            },
        ]

        plan: dict[str, Any] = {"intent": "", "steps": []}
        try:
            plan_resp = await client.chat.completions.create(
                model=model, messages=plan_messages
            )
            raw = plan_resp.choices[0].message.content or ""
            parsed = _parse_json_object(raw)
            if parsed and "intent" in parsed:
                plan = parsed
        except Exception:
            pass  # planning failure is non-fatal — execute anyway

        yield {"type": "thinking", "intent": plan.get("intent", ""), "steps": plan.get("steps", [])}

        # ── Phase 2: Execute with plan context ───────────────────────────────
        plan_context = _format_plan_context(plan)
        full_system = system_content + plan_context

        messages: list[dict[str, str]] = [{"role": "system", "content": full_system}]
        messages.extend(messages_so_far)
        messages.append({"role": "user", "content": prompt})

        tools_called: list[str] = []

        for _ in range(max_rounds):
            resp = await client.chat.completions.create(model=model, messages=messages)
            content: str = resp.choices[0].message.content or ""

            parsed_call = _try_parse_tool_call(content)
            if not parsed_call:
                # Guard: if no tool has been called yet and the response looks like
                # fabricated file/directory content, force the model to call the tool.
                if not tools_called and _looks_fabricated(prompt, content):
                    messages.append({"role": "assistant", "content": content})
                    messages.append({
                        "role": "user",
                        "content": (
                            "WRONG. You just fabricated content without calling any tool. "
                            "You have NO access to this repository's files from memory. "
                            "You MUST call the appropriate tool (file_read, glob, grep, bash…) "
                            "to get real data. Output the JSON tool call NOW — nothing else."
                        ),
                    })
                    continue
                yield {"type": "answer", "content": content}
                return

            fn_name, fn_args = parsed_call
            tools_called.append(fn_name)
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

            yield {"type": "tool_end", "tool": fn_name, "output": result}

            messages.append({"role": "assistant", "content": content})
            messages.append({
                "role": "user",
                "content": f"Tool result for {fn_name}:\n{result}\n\nContinue.",
            })

        yield {"type": "answer", "content": "Reached maximum tool rounds without a final answer."}


def _parse_json_object(text: str) -> dict | None:
    """Extract the first JSON object from text."""
    import re
    # Try the whole text first
    try:
        return json.loads(text.strip())
    except Exception:
        pass
    # Try to find a JSON block
    for m in re.finditer(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL):
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # Walk balanced braces
    i = 0
    while i < len(text):
        if text[i] != '{':
            i += 1
            continue
        depth, j = 0, i
        while j < len(text):
            if text[j] == '{':
                depth += 1
            elif text[j] == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[i:j + 1])
                    except Exception:
                        break
            j += 1
        i += 1
    return None


_READ_INTENT_WORDS = frozenset({
    "read", "show", "open", "display", "view", "content", "contents",
    "what's in", "whats in", "print", "output", "see", "get",
    "list", "ls", "tree", "structure", "files", "dir",
})

_FABRICATION_SIGNALS = ("```", "using ", "import ", "namespace ", "class ", "def ", "function ")


def _looks_fabricated(prompt: str, response: str) -> bool:
    """Return True when the model appears to have made up file/code content without a tool call."""
    p = prompt.lower()
    has_read_intent = any(w in p for w in _READ_INTENT_WORDS)
    has_code_block = any(s in response for s in _FABRICATION_SIGNALS)
    return has_read_intent and has_code_block


def _format_plan_context(plan: dict) -> str:
    steps = plan.get("steps") or []
    if not steps:
        return ""
    lines = [
        "\n\n## EXECUTION PLAN FOR THIS REQUEST",
        f"Intent: {plan.get('intent', '')}",
        "Steps:",
    ]
    for s in steps:
        lines.append(f"  {s.get('step', '?')}. Call `{s.get('tool', '?')}` — {s.get('purpose', '')}")
    lines.append("\nExecute these steps in order. Do not deviate unless a tool result requires it.")
    return "\n".join(lines)
