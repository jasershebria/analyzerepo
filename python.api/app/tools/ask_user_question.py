from __future__ import annotations

from typing import Any

from ._base import BaseTool, ToolDef


class AskUserQuestionTool(BaseTool):
    name = "ask_user_question"
    description = (
        "Present a question with options to the user. "
        "First call returns a prompt sentinel; call again with 'answer' populated to complete the round-trip."
    )

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            properties={
                "question": {"type": "string", "description": "Question to ask the user"},
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Answer choices to present",
                },
                "answer": {
                    "type": "string",
                    "description": "Populate on the second call with the user's selected answer",
                },
            },
            required=["question"],
        )

    async def _run(self, args: dict[str, Any]) -> Any:
        if args.get("answer") is not None:
            return {"answer": args["answer"]}
        return {
            "type": "ask_user_question",
            "question": args["question"],
            "options": args.get("options") or [],
            "note": (
                "Render this question in your UI, then call this tool again "
                "with 'answer' set to the user's selection."
            ),
        }
