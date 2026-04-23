from __future__ import annotations

from typing import Any

from ._base import BaseTool, ToolDef


class WebSearchTool(BaseTool):
    name = "web_search"
    description = (
        "Search the web using DuckDuckGo. Returns up to 10 results with title, URL, and snippet."
    )

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "query": {"type": "string", "description": "Search query"},
                "allowed_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter results to these domains only",
                },
                "blocked_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Exclude results from these domains",
                },
            },
            required=["query"],
        )

    async def _run(self, args: dict[str, Any]) -> list[dict]:
        import asyncio
        return await asyncio.to_thread(self._run_sync, args)

    def _run_sync(self, args: dict[str, Any]) -> list[dict]:
        from duckduckgo_search import DDGS

        query: str = args["query"]
        allowed: list[str] = args.get("allowed_domains") or []
        blocked: list[str] = args.get("blocked_domains") or []

        with DDGS() as ddgs:
            raw = list(ddgs.text(query, max_results=20))

        results = []
        for item in raw:
            url: str = item.get("href", "")
            if allowed and not any(d in url for d in allowed):
                continue
            if any(d in url for d in blocked):
                continue
            results.append({
                "title": item.get("title", ""),
                "url": url,
                "snippet": item.get("body", ""),
            })
            if len(results) >= 10:
                break
        return results
