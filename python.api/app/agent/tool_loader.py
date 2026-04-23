"""Dynamic tool loader: scans a directory for BaseTool subclasses and wraps them."""
from __future__ import annotations

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import TYPE_CHECKING

from app.tools._base import BaseTool

if TYPE_CHECKING:
    from langchain_core.tools import BaseTool as LCBaseTool


def load_tools_from_directory(tools_package_path: str | Path) -> list[BaseTool]:
    """
    Dynamically import every module in the given directory, find all non-abstract
    BaseTool subclasses, instantiate them, and return a deduplicated list (by tool name).

    Modules whose names start with '_' are skipped (internal/private).
    Tools that fail to instantiate are silently skipped.
    """
    path = Path(tools_package_path).resolve()
    package_name = _resolve_package_name(path)

    seen_names: set[str] = set()
    tools: list[BaseTool] = []

    for module_info in pkgutil.iter_modules([str(path)]):
        mod_name = module_info.name
        if mod_name.startswith("_"):
            continue
        full_module = f"{package_name}.{mod_name}"
        try:
            mod = importlib.import_module(full_module)
        except Exception:
            continue

        for _, obj in inspect.getmembers(mod, inspect.isclass):
            if (
                obj is not BaseTool
                and issubclass(obj, BaseTool)
                and not inspect.isabstract(obj)
                and obj.__module__ == full_module
            ):
                try:
                    instance = obj()
                    if instance.name and instance.name not in seen_names:
                        seen_names.add(instance.name)
                        tools.append(instance)
                except Exception:
                    pass

    return tools


def _resolve_package_name(path: Path) -> str:
    """Walk up from path collecting package name parts until a non-package dir."""
    parts: list[str] = [path.name]
    current = path.parent
    while (current / "__init__.py").exists():
        parts.append(current.name)
        current = current.parent
    parts.reverse()
    return ".".join(parts)


def as_langchain_tools(tools: list[BaseTool] | None = None) -> list["LCBaseTool"]:
    """
    Convert a list of BaseTool instances to LangChain StructuredTool objects.
    If tools is None, uses the full registered tool list from app.tools.
    """
    if tools is None:
        from app.tools import get_all
        tools = get_all()
    return [t.to_langchain_tool() for t in tools]
