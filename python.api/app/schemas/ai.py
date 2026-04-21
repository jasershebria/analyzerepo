from __future__ import annotations

from app.schemas.common import CamelModel


class AIChatRequest(CamelModel):
    prompt: str
    system_prompt: str | None = None


class AIChatResponse(CamelModel):
    reply: str


class ChatMessageDto(CamelModel):
    role: str
    content: str


class AIChatWithHistoryRequest(CamelModel):
    messages: list[ChatMessageDto]
    system_prompt: str | None = None
    repo_id: str | None = None
