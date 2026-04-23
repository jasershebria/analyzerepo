from __future__ import annotations

from html.parser import HTMLParser
from typing import Any

import httpx

from ._base import BaseTool, ToolDef

_MAX_BYTES = 50_000


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip:
            stripped = data.strip()
            if stripped:
                self._chunks.append(stripped)

    def get_text(self) -> str:
        return "\n".join(self._chunks)


class WebFetchTool(BaseTool):
    name = "web_fetch"
    description = (
        "Fetch the content of a URL and return it as plain text. "
        "HTML tags are stripped. Maximum 50 KB returned."
    )

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "url": {"type": "string", "description": "URL to fetch"},
                "prompt": {
                    "type": "string",
                    "description": "Optional context hint prepended to the result",
                },
            },
            required=["url"],
        )

    async def _run(self, args: dict[str, Any]) -> str:
        url: str = args["url"]
        prompt: str | None = args.get("prompt")
        headers = {"User-Agent": "Mozilla/5.0 (compatible; AnalyzeRepo/1.0)"}
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            raw = resp.text[:_MAX_BYTES]

        ct = resp.headers.get("content-type", "")
        if "html" in ct:
            extractor = _TextExtractor()
            extractor.feed(raw)
            text = extractor.get_text()
        else:
            text = raw

        if prompt:
            text = f"[Context: {prompt}]\n\n{text}"
        return text
