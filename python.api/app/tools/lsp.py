from __future__ import annotations

from typing import Any

from ._base import BaseTool, ToolDef


class LSPTool(BaseTool):
    name = "lsp"
    description = (
        "Code intelligence operations (go-to-definition, find-references, hover, symbols). "
        "Requires a running language server."
    )

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "operation": {
                    "type": "string",
                    "enum": [
                        "goToDefinition", "findReferences", "hover",
                        "documentSymbol", "workspaceSymbol", "goToImplementation",
                        "prepareCallHierarchy", "incomingCalls", "outgoingCalls",
                    ],
                },
                "file_path": {"type": "string", "description": "Absolute or relative file path"},
                "line": {"type": "integer", "description": "1-based line number"},
                "character": {"type": "integer", "description": "1-based character offset"},
            },
            required=["operation", "file_path", "line", "character"],
        )

    async def _run(self, args: dict[str, Any]) -> str:
        return (
            "LSP tool requires a running language server. "
            "Start a language server and configure lsp_server_url in config to enable."
        )
