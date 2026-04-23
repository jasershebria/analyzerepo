from __future__ import annotations

import json
import logging
from typing import Callable, Awaitable

from openai import AsyncOpenAI

from app.core.config import settings

log = logging.getLogger(__name__)

def _build_tool_instructions() -> str:
    workspace = settings.git_clone_base_path.replace("\\", "\\\\")
    return f"""\
You are an autonomous software engineering agent. Use tools to act — never give manual instructions.

To call a tool output ONLY this JSON (no markdown, no extra text):
{{"name": "<tool>", "arguments": {{<args>}}}}

The repository workspace root is: {settings.git_clone_base_path}

Tools:
- analyze_repository — list all files. args: {{}}
- read_file — read a file. args: {{"path": "<absolute path>"}}
- write_file — overwrite a file. args: {{"path": "<absolute path>", "content": "<content>"}}
- edit_file — replace text in file. args: {{"path": "<absolute path>", "old": "<text>", "new": "<text>"}}
- rename_file — rename a file. args: {{"path": "<absolute path>", "new_name": "<filename only>"}}
- sync_repository — clone/pull repo. args: {{}}

Rules:
1. ALWAYS call analyze_repository first if you don't know the file tree.
2. ALWAYS call read_file before editing or writing a file.
3. Build the absolute path as: workspace_root + \\\\ + relative path from fileTree. Example: {settings.git_clone_base_path}\\\\angular\\\\src\\\\app\\\\foo.ts
4. Never say "I don't have that file" — call read_file instead.
5. After every tool result, either call another tool or confirm what you did.\
"""

ToolExecutor = Callable[[str, dict], Awaitable[str]]


class AIChatService:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            base_url=settings.ai_base_url,
            api_key=settings.ai_api_key,
        )
        self._model = settings.ai_model

    async def check_connection(self) -> bool:
        """Verify API connectivity by making a minimal request."""
        try:
            await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1,
            )
            return True
        except Exception as e:
            log.error("AI model connection check failed: %s", e)
            return False

    async def chat(self, prompt: str, system_prompt: str | None = None) -> str:
        try:
            messages: list[dict] = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            total_chars = sum(len(m["content"]) for m in messages)
            print(f"DEBUG: Sending {len(messages)} messages ({total_chars} chars) to Groq", flush=True)
            
            resp = await self._client.chat.completions.create(model=self._model, messages=messages)
            return resp.choices[0].message.content or ""
        except Exception as e:
            import traceback
            log.error("Error in chat: %s\n%s", e, traceback.format_exc())
            raise e

    async def chat_with_history(
        self,
        messages: list[tuple[str, str]],
        tool_executor: ToolExecutor | None = None,
    ) -> str:
        try:
            formatted: list[dict] = []
            has_system = any(role == "system" for role, _ in messages)
            for role, content in messages:
                if role == "system":
                    if tool_executor:
                        content = f"{content}\n\n{_build_tool_instructions()}"
                formatted.append({"role": role, "content": content})

            if tool_executor and not has_system:
                formatted.insert(0, {"role": "system", "content": _build_tool_instructions()})

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
                            formatted.append({"role": "assistant", "content": content})
                            formatted.append({"role": "user", "content": f"Unknown tool '{fn_name}'. Available tools: {', '.join(_KNOWN_TOOLS)}"})
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
        except Exception as e:
            import traceback
            log.error("Error in chat_with_history: %s\n%s", e, traceback.format_exc())
            raise e

        return "Reached tool call limit without a final answer."


_KNOWN_TOOLS = {"sync_repository", "analyze_repository", "read_file", "write_file", "edit_file", "rename_file"}


def _try_parse_tool_call(text: str) -> tuple[str, dict] | None:
    """Return (function_name, args) by finding the first and last braces in the text."""
    # 1. Find the largest possible JSON block
    start = text.find('{')
    end = text.rfind('}')
    
    if start == -1 or end == -1 or end <= start:
        return None
        
    candidate = text[start:end+1]
    
    # 2. Try parsing it
    try:
        data = json.loads(candidate)
        if isinstance(data, dict) and "name" in data:
            return data["name"], data.get("arguments") or data.get("parameters") or {}
    except (json.JSONDecodeError, ValueError):
        # 3. Aggressive fallback for malformed escaping (common in small models)
        try:
            # Fix unescaped backslashes before trying again
            fixed = candidate.replace('\\', '\\\\').replace('\\\\\\\\', '\\\\')
            data = json.loads(fixed)
            if isinstance(data, dict) and "name" in data:
                return data["name"], data.get("arguments") or {}
        except:
            pass
            
    return None
