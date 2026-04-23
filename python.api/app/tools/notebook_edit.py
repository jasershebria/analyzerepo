from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from ._base import BaseTool, ToolDef


class NotebookEditTool(BaseTool):
    name = "notebook_edit"
    description = (
        "Edit a Jupyter notebook (.ipynb). Supports replace, insert (after a cell), "
        "and delete operations on code or markdown cells."
    )

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "notebook_path": {"type": "string", "description": "Absolute path to the .ipynb file"},
                "cell_id": {
                    "type": "string",
                    "description": "Cell id or 0-based index. For insert, new cell goes after this cell.",
                },
                "new_source": {"type": "string", "description": "New source for the cell"},
                "cell_type": {
                    "type": "string",
                    "enum": ["code", "markdown"],
                    "description": "Cell type (default: code)",
                },
                "edit_mode": {
                    "type": "string",
                    "enum": ["replace", "insert", "delete"],
                    "description": "Operation (default: replace)",
                },
            },
            required=["notebook_path", "new_source"],
        )

    async def _run(self, args: dict[str, Any]) -> str:
        import asyncio
        return await asyncio.to_thread(self._run_sync, args)

    def _run_sync(self, args: dict[str, Any]) -> str:
        path = Path(args["notebook_path"])
        if not path.exists():
            raise FileNotFoundError(f"Notebook not found: {args['notebook_path']}")

        nb = json.loads(path.read_text(encoding="utf-8"))
        cells: list[dict] = nb.get("cells", [])
        cell_id = args.get("cell_id")
        new_source: str = args.get("new_source", "")
        cell_type: str = args.get("cell_type", "code")
        edit_mode: str = args.get("edit_mode", "replace")

        # Locate target cell
        target_idx: int | None = None
        if cell_id is not None:
            # Try as integer index first
            try:
                target_idx = int(cell_id)
                if target_idx < 0 or target_idx >= len(cells):
                    raise ValueError(f"Cell index {target_idx} out of range")
            except ValueError:
                # Try by cell id string
                for i, c in enumerate(cells):
                    if c.get("id") == cell_id:
                        target_idx = i
                        break
                if target_idx is None:
                    raise ValueError(f"Cell '{cell_id}' not found")

        src_lines = new_source.splitlines(keepends=True)

        if edit_mode == "replace":
            if target_idx is None:
                raise ValueError("cell_id is required for replace mode")
            cells[target_idx]["source"] = src_lines
            cells[target_idx]["cell_type"] = cell_type
            msg = f"Replaced cell {target_idx}"

        elif edit_mode == "insert":
            new_cell: dict = {
                "id": str(uuid.uuid4())[:8],
                "cell_type": cell_type,
                "source": src_lines,
                "metadata": {},
                "outputs": [] if cell_type == "code" else None,
            }
            if cell_type != "code":
                new_cell.pop("outputs", None)
            insert_at = (target_idx + 1) if target_idx is not None else len(cells)
            cells.insert(insert_at, new_cell)
            msg = f"Inserted new {cell_type} cell at index {insert_at}"

        elif edit_mode == "delete":
            if target_idx is None:
                raise ValueError("cell_id is required for delete mode")
            cells.pop(target_idx)
            msg = f"Deleted cell {target_idx}"

        else:
            raise ValueError(f"Unknown edit_mode: {edit_mode}")

        nb["cells"] = cells
        path.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
        return msg
