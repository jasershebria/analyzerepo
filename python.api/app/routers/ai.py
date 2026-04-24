from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.routing import CamelCaseRoute
from app.db.session import get_db
from app.schemas.ai import AIChatResponse, AIChatWithHistoryRequest
from app.services.ai_service import AIChatService
from app.services.tool_service import ToolService

router = APIRouter(prefix="/ai", tags=["AI"], route_class=CamelCaseRoute)

_ai_service = AIChatService()


@router.get("/test-connection")
async def test_connection() -> dict:
    success = await _ai_service.check_connection()
    return {"success": success, "model": settings.ai_model}



@router.post("/chat/history", response_model=AIChatResponse)
async def chat_with_history(req: AIChatWithHistoryRequest, db: AsyncSession = Depends(get_db)) -> AIChatResponse:
    messages: list[tuple[str, str]] = []
    if req.system_prompt:
        messages.append(("system", req.system_prompt))
    for msg in req.messages:
        messages.append((msg.role, msg.content))

    tool_executor = None
    if req.repo_id:
        tool_svc = ToolService(db, uuid.UUID(req.repo_id))
        tool_executor = tool_svc.execute_tool

    reply = await _ai_service.chat_with_history(messages, tool_executor=tool_executor)
    return AIChatResponse(reply=reply)
