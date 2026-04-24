from __future__ import annotations

from typing import Any

from ._base import BaseTool, ToolDef


class RagSearchTool(BaseTool):
    name = "rag_search"
    description = (
        "Search the indexed repository for relevant code using a natural-language query. "
        "Returns matching code snippets with file paths. "
        "Use this before answering any question about the codebase."
    )

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "query": {"type": "string", "description": "Natural-language search query"},
                "repo_id": {"type": "string", "description": "Repository UUID to search in"},
                "top_k": {"type": "integer", "description": "Number of results to return (default 5)"},
            },
            required=["query", "repo_id"],
        )

    async def _run(self, args: dict[str, Any]) -> str:
        from app.rag import vector_store as vs

        query: str = args["query"]
        repo_id: str = args["repo_id"]
        top_k: int = args.get("top_k") or 5

        col = vs.get_collection(repo_id)
        chunks = await vs.similarity_search(col, query, top_k=top_k)

        if not chunks:
            return "No relevant code found for this query."

        parts = []
        for c in chunks:
            file_path = c.get("metadata", {}).get("file_path", "unknown")
            score = round(c.get("score", 0.0), 3)
            content = c.get("content", "")
            parts.append(f"// {file_path}  (score: {score})\n{content}")

        return "\n\n---\n\n".join(parts)
