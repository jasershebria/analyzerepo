"""
MCP server that exposes every tool in app/tools/ to OpenHands (OpenDevin).

Mount point in FastAPI: /mcp
OpenHands config:
    [mcp]
    servers = [{name="analyzerepo", transport="sse",
                url="http://localhost:8000/mcp/sse"}]
"""
from __future__ import annotations

import mcp.types as types
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Route

import app.tools as tools_registry

_server = Server("analyzerepo-tools")


@_server.list_tools()
async def _list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name=td["function"]["name"],
            description=td["function"]["description"],
            inputSchema={
                "type": "object",
                "properties": td["function"]["parameters"]["properties"],
                "required": td["function"]["parameters"]["required"],
            },
        )
        for td in tools_registry.definitions()
    ]


@_server.call_tool()
async def _call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    try:
        result = await tools_registry.execute(name, arguments or {})
    except Exception as exc:
        result = f"Error: {exc}"
    return [types.TextContent(type="text", text=str(result))]


# Full path where clients POST messages — must include the /mcp mount prefix
_sse = SseServerTransport("/mcp/messages/")


async def _sse_endpoint(request: Request) -> None:
    async with _sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await _server.run(
            streams[0],
            streams[1],
            _server.create_initialization_options(),
        )


async def _messages_endpoint(request: Request) -> None:
    await _sse.handle_post_message(request.scope, request.receive, request._send)


# Starlette sub-app — mounted at /mcp in the main FastAPI application
mcp_app = Starlette(
    routes=[
        Route("/sse", endpoint=_sse_endpoint),
        Route("/messages/", endpoint=_messages_endpoint, methods=["POST"]),
    ]
)
