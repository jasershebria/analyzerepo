from __future__ import annotations

from typing import Any

from ._base import BaseTool, ToolDef


class ToolSearchTool(BaseTool):
    name = "tool_search"
    description = "Search available tools by keyword. Returns matching tool names and descriptions."

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "query": {"type": "string", "description": "Search query"},
                "max_results": {
                    "type": "integer",
                    "description": "Maximum results to return (default: 5)",
                },
            },
            required=["query"],
        )

    async def _run(self, args: dict[str, Any]) -> list[dict]:
        # Import here to avoid circular import at module load time
        from . import get_all

        query: str = args["query"].lower()
        max_results: int = args.get("max_results") or 5
        results = []
        for tool in get_all():
            if query in tool.name.lower() or query in tool.description.lower():
                results.append({"name": tool.name, "description": tool.description})
            if len(results) >= max_results:
                break
        return results
