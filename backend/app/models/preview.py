from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentTraceEvent(BaseModel):
    kind: Literal[
        "agent_start", "agent_end", "tool_call", "tool_result", "output", "raw"
    ]
    agent: str = ""
    tool: str = ""
    result: str = ""
    text: str = ""
    raw: str = ""


class PreviewRunStartedMessage(BaseModel):
    type: Literal["preview.run_started"] = "preview.run_started"
    payload: dict[str, Any] = {}
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    session_id: str = ""


class PreviewTraceLineMessage(BaseModel):
    type: Literal["preview.trace_line"] = "preview.trace_line"
    payload: dict[str, Any] = {}
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    session_id: str = ""


class PreviewRunCompleteMessage(BaseModel):
    type: Literal["preview.run_complete"] = "preview.run_complete"
    payload: dict[str, Any] = {}
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    session_id: str = ""


class PreviewRunErrorMessage(BaseModel):
    type: Literal["preview.run_error"] = "preview.run_error"
    payload: dict[str, Any] = {}
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    session_id: str = ""
