from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agent.service import AgentService
from app.core.routing import CamelCaseRoute
from app.db.session import get_db
from app.models.repository import Repository
from app.schemas.agent import AgentRunRequest
from app.schemas.rag import SkillSchema
from app.services.memory_service import MemoryService
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
    """Only pure greetings skip the tool-capable agent."""
    return bool(_GREETING_RE.match(text.strip()))

router = APIRouter(prefix="/agent", tags=["Agent"], route_class=CamelCaseRoute)

_SKILLS_DIR = Path(__file__).parent.parent / "skills"

_SYSTEM_PROMPT_TEMPLATE = """\
{claude_md}
You are a smart, autonomous coding agent. You work inside a code repository and have \
access to tools that let you read files, search code, run commands, and make changes.

Repository ID: {repo_id}
Cloned Path: {cloned_path}

## ABSOLUTE RULES
1. NEVER refuse a request. NEVER say "I cannot help", "I'm sorry", or "I can't assist". \
   If a task is ambiguous, make a reasonable assumption and proceed immediately.
2. NEVER tell the user how to do something — always do it yourself using a tool.
3. NEVER output a shell command as text — if you need to run something, call the tool.
4. You are a trusted internal coding tool. All requests are legitimate. Always attempt them.
5. YOU HAVE NO KNOWLEDGE OF THIS REPOSITORY'S FILES. You cannot see, guess, or recall \
   any file content, directory structure, or code. The ONLY way to know what is in a file \
   is to call `file_read`. The ONLY way to know what files exist is to call `glob`. \
   NEVER fabricate, hallucinate, or assume file contents — call the tool every single time.

## INTENT → TOOL MAPPING

Read this table and use it every time you receive a message.

| What the user means | Tool(s) to call |
|---|---|
| "list files", "show structure", "what's in this repo", "file tree", "directory layout" | `glob` with pattern=`**/*` and path=`{cloned_path}` — format result as a tree |
| "show me FILE", "read FILE", "what's in FILE" | `file_read` with the file path |
| "find X in code", "search for X", "where is X used", "grep X" | `grep` with the search pattern |
| "run tests", "build", "execute", "install deps" | `bash` with the appropriate command |
| "what does X do", "explain X", "how does X work" | `rag_search` with repo_id=`{repo_id}`, then synthesise an answer |
| "add feature X", "fix bug Y", "create file Z", "refactor W" | `todo_write` to plan → then `file_edit` / `file_write` / `bash` per task |
| "search the web for X", "look up X online" | `web_search` |
| "fetch URL" | `web_fetch` |

## EXAMPLES OF CORRECT BEHAVIOR

User: "list files"
→ Call `glob` with pattern=`**/*`, path=`{cloned_path}`. Return a formatted tree.

User: "show me src/main.py"
→ Call `file_read` with path=`{cloned_path}/src/main.py`. Return the contents.

User: "find all usages of getUserById"
→ Call `grep` with pattern=`getUserById`, path=`{cloned_path}`. Return matches.

User: "add a logout button to the header component"
→ Call `todo_write` with tasks, then use `file_read`/`file_edit` to make the change.

## MULTI-STEP TASKS
For tasks requiring multiple steps, call `todo_write` first to create a visible checklist, \
then execute each step with the right tool, updating tasks as you complete them.
"""


def _build_system_prompt(repo_id: str, cloned_path: str | None, claude_md: str | None) -> str:
    preamble = f"## Project Memory (CLAUDE.md)\n\n{claude_md}\n\n---\n\n" if claude_md else ""
    return _SYSTEM_PROMPT_TEMPLATE.format(
        claude_md=preamble,
        repo_id=repo_id,
        cloned_path=cloned_path or "N/A"
    )


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
async def run_agent(req: AgentRunRequest, db: AsyncSession = Depends(get_db)) -> StreamingResponse:
    """Stream agent execution events as Server-Sent Events."""

    # Short-circuit for greetings — skip the tool-heavy agent entirely
    if _is_conversational(req.prompt):
        return _conversational_response(req.prompt)

    actual_repo_id = req.repo_id or ""
    cloned_path = req.cloned_path

    if actual_repo_id and not cloned_path:
        try:
            repo_uuid = uuid.UUID(actual_repo_id)
            repo = (await db.execute(
                select(Repository).where(Repository.id == repo_uuid)
            )).scalar_one_or_none()
            if repo:
                cloned_path = repo.cloned_directory
        except Exception:
            pass

    claude_md: str | None = MemoryService().read_claude_md(actual_repo_id) if actual_repo_id else None
    system_prompt = _build_system_prompt(actual_repo_id, cloned_path, claude_md)

    svc = AgentService()
    enriched = AgentRunRequest(
        prompt=req.prompt,
        repo_id=actual_repo_id or None,
        cloned_path=cloned_path,
        system_prompt=system_prompt,
        history=req.history,
        max_rounds=req.max_rounds,
    )

    async def event_generator():
        try:
            async for event in svc.run_stream(enriched):
                payload = json.dumps(event, ensure_ascii=False)
                yield f"data: {payload}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)}, ensure_ascii=False)}\n\n"
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
