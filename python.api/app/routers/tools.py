from __future__ import annotations

from fastapi import APIRouter

from app.core.routing import CamelCaseRoute
from app.schemas.tools import ToolCallRequest, ToolCallResponse
import app.tools as tool_registry

router = APIRouter(prefix="/tools", tags=["Tools"], route_class=CamelCaseRoute)


@router.get(
    "/definitions",
    summary="List all available tools in OpenAI function-calling format",
)
async def get_tool_definitions() -> list[dict]:
    return tool_registry.definitions()


@router.post(
    "/call",
    response_model=ToolCallResponse,
    summary="Execute a named tool with the given arguments",
)
async def call_tool(request: ToolCallRequest) -> ToolCallResponse:
    try:
        result = await tool_registry.execute(request.name, request.arguments)
        return ToolCallResponse(tool=request.name, result=result)
    except Exception as exc:
        return ToolCallResponse(tool=request.name, error=str(exc))
