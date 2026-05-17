from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class BaseMessage(BaseModel):
    type: str
    payload: dict[str, Any] = {}
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    session_id: str = ""


class ChatMessage(BaseMessage):
    type: Literal["chat.message"] = "chat.message"


class QuestionGroupMessage(BaseMessage):
    type: Literal["chat.question_group"] = "chat.question_group"


class CheckpointMessage(BaseMessage):
    type: Literal["chat.checkpoint"] = "chat.checkpoint"


class StageUpdateMessage(BaseMessage):
    type: Literal["status.stage_update"] = "status.stage_update"


class ProgressMessage(BaseMessage):
    type: Literal["status.progress"] = "status.progress"


class CompleteMessage(BaseMessage):
    type: Literal["status.complete"] = "status.complete"


class ErrorMessage(BaseMessage):
    type: Literal["error.llm_failure", "error.pipeline_failure"] = "error.pipeline_failure"


class ActivityMessage(BaseMessage):
    type: Literal["status.activity"] = "status.activity"


class ControlMessage(BaseMessage):
    type: Literal["control.approve", "control.reject", "control.user_input"]
