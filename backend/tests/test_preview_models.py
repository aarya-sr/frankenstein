"""Tests for preview Pydantic models."""

from app.models.preview import (
    AgentTraceEvent,
    PreviewRunCompleteMessage,
    PreviewRunErrorMessage,
    PreviewRunStartedMessage,
    PreviewTraceLineMessage,
)


class TestAgentTraceEvent:
    def test_agent_start(self):
        e = AgentTraceEvent(kind="agent_start", agent="Researcher", raw="[Agent: Researcher]")
        assert e.kind == "agent_start"
        assert e.agent == "Researcher"
        assert e.tool == ""
        assert e.text == ""

    def test_tool_call(self):
        e = AgentTraceEvent(kind="tool_call", agent="A", tool="search", raw="Action: search")
        assert e.tool == "search"

    def test_raw(self):
        e = AgentTraceEvent(kind="raw", text="hello", raw="hello")
        assert e.text == "hello"

    def test_all_kinds_valid(self):
        for kind in ["agent_start", "agent_end", "tool_call", "tool_result", "output", "raw"]:
            e = AgentTraceEvent(kind=kind, raw="test")
            assert e.kind == kind


class TestPreviewMessages:
    def test_run_started_defaults(self):
        msg = PreviewRunStartedMessage(payload={"container_id": "abc"}, session_id="s1")
        d = msg.model_dump(mode="json")
        assert d["type"] == "preview.run_started"
        assert d["payload"]["container_id"] == "abc"
        assert d["session_id"] == "s1"
        assert "timestamp" in d

    def test_trace_line(self):
        event = AgentTraceEvent(kind="agent_start", agent="R", raw="raw")
        msg = PreviewTraceLineMessage(
            payload={"event": event.model_dump()},
            session_id="s1",
        )
        d = msg.model_dump(mode="json")
        assert d["type"] == "preview.trace_line"
        assert d["payload"]["event"]["kind"] == "agent_start"

    def test_run_complete(self):
        msg = PreviewRunCompleteMessage(
            payload={"exit_code": 0, "duration_ms": 1234, "output": "done"},
            session_id="s1",
        )
        d = msg.model_dump(mode="json")
        assert d["type"] == "preview.run_complete"
        assert d["payload"]["exit_code"] == 0

    def test_run_error(self):
        msg = PreviewRunErrorMessage(
            payload={"message": "boom"},
            session_id="s1",
        )
        d = msg.model_dump(mode="json")
        assert d["type"] == "preview.run_error"
        assert d["payload"]["message"] == "boom"
