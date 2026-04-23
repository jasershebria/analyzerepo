from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class GrepOutputMode(str, Enum):
    content = "content"
    files_with_matches = "files_with_matches"
    count = "count"


# ── Per-tool input models ─────────────────────────────────────────────────────

class FileReadInput(BaseModel):
    file_path: str
    offset: int | None = None
    limit: int | None = None
    pages: str | None = None


class FileWriteInput(BaseModel):
    file_path: str
    content: str


class FileEditInput(BaseModel):
    file_path: str
    old_string: str
    new_string: str
    replace_all: bool = False


class GlobInput(BaseModel):
    pattern: str
    path: str | None = None


class GrepInput(BaseModel):
    pattern: str
    path: str | None = None
    glob: str | None = None
    output_mode: GrepOutputMode = GrepOutputMode.files_with_matches
    context: int | None = None
    before_context: int | None = None
    after_context: int | None = None
    case_insensitive: bool = False
    multiline: bool = False
    head_limit: int | None = 250
    offset: int | None = None


class BashInput(BaseModel):
    command: str
    timeout: int | None = None  # milliseconds, default 120 000
    run_in_background: bool = False


class PowerShellInput(BaseModel):
    command: str
    timeout: int | None = None
    run_in_background: bool = False


class WebFetchInput(BaseModel):
    url: str
    prompt: str | None = None


class WebSearchInput(BaseModel):
    query: str
    allowed_domains: list[str] = Field(default_factory=list)


class TodoItem(BaseModel):
    id: str
    content: str
    status: Literal["pending", "in_progress", "completed"]
    priority: Literal["high", "medium", "low"]


class TodoWriteInput(BaseModel):
    todos: list[TodoItem]


class NotebookEditInput(BaseModel):
    notebook_path: str
    cell_id: str
    new_source: str


class AskUserQuestionInput(BaseModel):
    question: str
    options: list[str] = Field(default_factory=list)
    answer: str | None = None  # populated by caller on second round-trip


# ── Additional tools ──────────────────────────────────────────────────────────

class SleepInput(BaseModel):
    duration_ms: int = Field(description="Duration to sleep in milliseconds")


class ConfigInput(BaseModel):
    setting: str = Field(description='Setting key, e.g. "theme" or "model"')
    value: str | bool | int | float | None = None  # omit to get current value


class BriefInput(BaseModel):
    message: str
    attachments: list[str] = Field(default_factory=list)
    status: Literal["normal", "proactive"] = "normal"


class SendMessageInput(BaseModel):
    to: str = Field(description='Recipient: agent name or "*" for broadcast')
    message: str
    summary: str | None = None


class TaskCreateInput(BaseModel):
    subject: str
    description: str
    active_form: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskGetInput(BaseModel):
    task_id: str


class TaskUpdateInput(BaseModel):
    task_id: str
    subject: str | None = None
    description: str | None = None
    active_form: str | None = None
    status: Literal["pending", "in_progress", "completed", "deleted"] | None = None
    add_blocks: list[str] = Field(default_factory=list)
    add_blocked_by: list[str] = Field(default_factory=list)
    owner: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskStopInput(BaseModel):
    task_id: str | None = None
    shell_id: str | None = None  # deprecated alias


class CronCreateInput(BaseModel):
    cron: str = Field(description='5-field cron expression, e.g. "*/5 * * * *"')
    prompt: str = Field(description="Prompt to enqueue at each fire time")
    recurring: bool = True
    durable: bool = False


class CronDeleteInput(BaseModel):
    id: str = Field(description="Job ID returned by cron_create")


class ToolSearchInput(BaseModel):
    query: str
    max_results: int = 5


class LspInput(BaseModel):
    operation: Literal[
        "goToDefinition",
        "findReferences",
        "hover",
        "documentSymbol",
        "workspaceSymbol",
        "goToImplementation",
        "prepareCallHierarchy",
        "incomingCalls",
        "outgoingCalls",
    ]
    file_path: str
    line: int
    character: int


class RemoteTriggerInput(BaseModel):
    action: Literal["list", "get", "create", "update", "run"]
    trigger_id: str | None = None
    body: dict[str, Any] | None = None


class AgentInput(BaseModel):
    description: str
    prompt: str
    subagent_type: str | None = None
    model: Literal["sonnet", "opus", "haiku"] | None = None
    run_in_background: bool = False


# ── OpenAI function-calling wire types ───────────────────────────────────────

class ToolParameterSchema(BaseModel):
    type: str = "object"
    properties: dict[str, Any]
    required: list[str] = Field(default_factory=list)


class ToolFunctionDefinition(BaseModel):
    name: str
    description: str
    parameters: ToolParameterSchema


class ToolDefinition(BaseModel):
    type: Literal["function"] = "function"
    function: ToolFunctionDefinition


class ToolCallRequest(BaseModel):
    name: str
    arguments: dict[str, Any]


class ToolCallResponse(BaseModel):
    tool: str
    result: Any | None = None
    error: str | None = None
