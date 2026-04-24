from __future__ import annotations

from app.schemas.common import CamelModel


class AgentMessage(CamelModel):
    role: str
    content: str | None = None
    tool_call_id: str | None = None


class AgentRunRequest(CamelModel):
    prompt: str
    repo_id: str | None = None
    cloned_path: str | None = None
    system_prompt: str | None = None
    working_dir: str | None = None
    history: list[AgentMessage] = []
    max_rounds: int = 15


class AgentRunResult(CamelModel):
    final_response: str
    tool_calls_made: int
    elapsed_ms: int
    messages: list[dict]
