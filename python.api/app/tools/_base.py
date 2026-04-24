from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Union


def _json_schema_to_python_type(schema: dict[str, Any]) -> Any:
    """Convert a JSON Schema property sub-schema to a Python type annotation."""
    enum_vals = schema.get("enum")
    if enum_vals is not None:
        from typing import Literal
        return Union[tuple(Literal[v] for v in enum_vals)]

    t = schema.get("type")
    if t == "string":
        return str
    if t == "integer":
        return int
    if t == "number":
        return float
    if t == "boolean":
        return bool
    if t == "object":
        return dict
    if t == "array":
        items_schema = schema.get("items", {})
        if items_schema:
            item_type = _json_schema_to_python_type(items_schema)
            return List[item_type]
        return list
    return Any


class ToolDef:
    """OpenAI function-calling tool definition."""

    def __init__(
        self,
        name: str,
        description: str,
        properties: dict[str, Any],
        required: list[str] | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self.properties = properties
        self.required = required or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.properties,
                    "required": self.required,
                },
            },
        }


class BaseTool(ABC):
    name: str = ""
    description: str = ""

    def __init__(self, working_dir: str | None = None) -> None:
        self.working_dir = working_dir

    @abstractmethod
    def definition(self) -> ToolDef: ...

    @abstractmethod
    async def _run(self, args: dict[str, Any]) -> Any: ...

    async def call(self, args: dict[str, Any]) -> str:
        print(f"DEBUG: Tool Fired: {self.name}({json.dumps(args)})")
        result = await self._run(args)
        if result is None:
            return ""
        if isinstance(result, str):
            return result
        return json.dumps(result, default=str, ensure_ascii=False)

    def to_langchain_tool(self):
        """Wrap this BaseTool as a LangChain StructuredTool with a generated args_schema."""
        import pydantic
        from langchain_core.tools import StructuredTool

        tool_def = self.definition()
        fields: dict[str, Any] = {}

        for fname, fschema in tool_def.properties.items():
            py_type = _json_schema_to_python_type(fschema)
            field_desc = fschema.get("description", "")
            if fname in tool_def.required:
                fields[fname] = (py_type, pydantic.Field(description=field_desc))
            else:
                fields[fname] = (
                    Optional[py_type],
                    pydantic.Field(default=None, description=field_desc),
                )

        if fields:
            ArgsModel = pydantic.create_model(f"{self.name}_args", **fields)
        else:
            ArgsModel = pydantic.create_model(f"{self.name}_args")

        _self = self

        async def _coroutine(**kwargs: Any) -> str:
            return await _self.call(kwargs)

        return StructuredTool(
            name=self.name,
            description=self.description,
            args_schema=ArgsModel,
            coroutine=_coroutine,
        )
