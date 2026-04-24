from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agent.service import AgentService
from app.core.routing import CamelCaseRoute
from app.schemas.agent import AgentRunRequest
from app.schemas.rag import SkillSchema
from app.services.memory_service import MemoryService

_GREETING_RE = re.compile(
    r"^\s*(hi|hello|hey|howdy|greetings|good\s+(morning|afternoon|evening|day)|"
    r"what'?s up|sup|yo|how are you|how r u|hiya)\W*\s*$",
    re.IGNORECASE,
)

_FRIENDLY_SYSTEM = (
    "You are a helpful AI assistant for a code repository analysis tool. "
    "Be warm, friendly, and brief. Do not output JSON or tool calls."
)


def _is_conversational(text: str) -> bool:
    q = text.strip()
    if _GREETING_RE.match(q):
        return True
    words = q.split()
    has_code = any(c in q for c in (".", "()", "->", "::", "def ", "class ", "import ", "return "))
    return len(words) <= 5 and not has_code

router = APIRouter(prefix="/agent", tags=["Agent"], route_class=CamelCaseRoute)

_SKILLS_DIR = Path(__file__).parent.parent / "skills"

_SYSTEM_PROMPT_TEMPLATE = """\
{claude_md}
You are an intelligent web-based coding agent with access to a full suite of tools.

Repository ID: {repo_id}

Respond based on the user's intent:

1. GREETING / SMALL TALK — reply naturally and briefly.

2. CODE QUESTION — call `rag_search` with repo_id="{repo_id}" to find relevant code snippets, \
then answer with specific file paths and line references.

3. FILE CHANGE / REPO ACTION — always follow this sequence:
   a. Call `todo_write` to create a clear task checklist
   b. Execute each task using the right tool (file_edit, file_write, bash, glob, grep, etc.)
   c. Mark tasks done as you complete them

Never give manual instructions. Always use tools to act.
"""


def _build_system_prompt(repo_id: str, claude_md: str | None) -> str:
    preamble = f"## Project Memory (CLAUDE.md)\n\n{claude_md}\n\n---\n\n" if claude_md else ""
    return _SYSTEM_PROMPT_TEMPLATE.format(claude_md=preamble, repo_id=repo_id)


def _load_skills() -> list[dict]:
    skills: list[dict] = []
    if not _SKILLS_DIR.exists():
        return skills
    for md_file in sorted(_SKILLS_DIR.glob("*.md")):
        try:
            content = md_file.read_text(encoding="utf-8")
            lines = content.splitlines()
            name = md_file.stem
            description = ""
            prompt_lines: list[str] = []
            in_frontmatter = False
            past_frontmatter = False
            for line in lines:
                if line.strip() == "---" and not past_frontmatter:
                    in_frontmatter = not in_frontmatter
                    if not in_frontmatter:
                        past_frontmatter = True
                    continue
                if in_frontmatter:
                    if line.startswith("name:"):
                        name = line.split(":", 1)[1].strip()
                    elif line.startswith("description:"):
                        description = line.split(":", 1)[1].strip()
                elif past_frontmatter:
                    prompt_lines.append(line)
            skills.append({
                "name": name,
                "description": description,
                "prompt": "\n".join(prompt_lines).strip(),
            })
        except Exception:
            pass
    return skills


@router.post("/run")
async def run_agent(req: AgentRunRequest) -> StreamingResponse:
    """Stream agent execution events as Server-Sent Events."""

    # Short-circuit for greetings — skip the tool-heavy agent entirely
    if _is_conversational(req.prompt):
        return _conversational_response(req.prompt)

    actual_repo_id = req.repo_id or ""
    claude_md: str | None = MemoryService().read_claude_md(actual_repo_id) if actual_repo_id else None
    system_prompt = _build_system_prompt(actual_repo_id, claude_md)

    svc = AgentService()
    enriched = AgentRunRequest(
        prompt=req.prompt,
        repo_id=actual_repo_id or None,
        system_prompt=system_prompt,
        history=req.history,
        max_rounds=req.max_rounds,
    )

    async def event_generator():
        async for event in svc.run_stream(enriched):
            payload = json.dumps(event, ensure_ascii=False)
            yield f"data: {payload}\n\n"
        yield "data: {\"type\": \"done\"}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _conversational_response(prompt: str) -> StreamingResponse:
    """Direct LLM call with no tools — for greetings and small talk."""
    from app.services.ai_service import AIChatService

    async def event_generator():
        try:
            ai = AIChatService()
            answer = await ai.chat_with_history(
                messages=[("system", _FRIENDLY_SYSTEM), ("user", prompt)]
            )
            yield f"data: {json.dumps({'type': 'answer', 'content': answer})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
        yield "data: {\"type\": \"done\"}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/skills", response_model=list[SkillSchema])
async def list_skills() -> list[dict]:
    """Return all available skills (slash commands)."""
    return _load_skills()
