from __future__ import annotations

from fastapi import APIRouter

import app.tools as tool_registry
from app.agent.service import AgentService
from app.core.config import settings
from app.core.routing import CamelCaseRoute
from app.schemas.agent import AgentRunRequest, AgentRunResult

router = APIRouter(prefix="/agent", tags=["Agent"], route_class=CamelCaseRoute)

_agent_service = AgentService()


@router.post("/run", response_model=AgentRunResult)
async def run_agent(request: AgentRunRequest) -> AgentRunResult:
    return await _agent_service.run(request)


@router.get("/info")
async def agent_info() -> dict:
    return {
        "model": settings.ai_model,
        "aiBaseUrl": settings.ai_base_url,
        "availableTools": len(tool_registry.get_all()),
    }
