from __future__ import annotations

from fastapi import APIRouter

import app.tools as tool_registry
from app.core.config import settings
from app.core.routing import CamelCaseRoute
from app.schemas.agent import AgentRunRequest, AgentRunResult
from app.services.agent_service import AgentService
from app.services.tools_service import ToolsService

router = APIRouter(prefix="/agent", tags=["Agent"], route_class=CamelCaseRoute)

_tools_service = ToolsService()
_agent_service = AgentService(_tools_service)


@router.post("/run", response_model=AgentRunResult)
async def run_agent(request: AgentRunRequest) -> AgentRunResult:
    return await _agent_service.run(request)


@router.get("/info")
async def agent_info() -> dict:
    return {
        "model": settings.ollama_model,
        "ollamaBaseUrl": settings.ollama_base_url,
        "availableTools": len(tool_registry.get_all()),
    }
