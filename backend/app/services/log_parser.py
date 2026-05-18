"""Parse agent execution log lines into structured AgentTraceEvent objects.

Supports CrewAI and LangGraph output patterns. Falls back to raw for unrecognized lines.
"""

import re

from app.models.preview import AgentTraceEvent

# ── CrewAI Patterns ──────────────────────────────────────────────────

_CREWAI_AGENT_START = re.compile(
    r"^\[(?:Agent|Working Agent):\s*(.+?)\]", re.IGNORECASE
)
_CREWAI_TASK = re.compile(r"^\[Task\]\s*(.+)", re.IGNORECASE)
_CREWAI_ACTION = re.compile(r"^Action:\s*(.+)", re.IGNORECASE)
_CREWAI_ACTION_INPUT = re.compile(r"^Action Input:\s*(.+)", re.IGNORECASE)
_CREWAI_OBSERVATION = re.compile(r"^Observation:\s*(.+)", re.IGNORECASE)
_CREWAI_FINAL = re.compile(r"^Final Answer:\s*(.+)", re.IGNORECASE)
_CREWAI_AGENT_END = re.compile(
    r"^\[(?:Agent|Working Agent):\s*(.+?)\]\s+(?:finished|completed|done)",
    re.IGNORECASE,
)

# ── LangGraph Patterns ──────────────────────────────────────────────

_LG_ENTERING = re.compile(r"^>\s*Entering\s+(?:new\s+)?(\w+)", re.IGNORECASE)
_LG_TOOL_CALL = re.compile(r"^tool_call\s*[:\(]\s*(\w+)", re.IGNORECASE)
_LG_TOOL_MSG = re.compile(r"^ToolMessage\s*[:\(]\s*(.+)", re.IGNORECASE)

# Current agent tracker (module-level, reset per parse session via framework)
_current_agent = ""


def parse_line(line: str, framework: str = "crewai") -> AgentTraceEvent:
    """Parse a single log line into an AgentTraceEvent."""
    global _current_agent
    stripped = line.strip()

    if not stripped:
        return AgentTraceEvent(kind="raw", text="", raw=line)

    if framework.lower() in ("crewai", "crew"):
        return _parse_crewai(stripped, line)
    elif framework.lower() in ("langgraph", "lang_graph"):
        return _parse_langgraph(stripped, line)

    return AgentTraceEvent(kind="raw", text=stripped, raw=line)


def _parse_crewai(stripped: str, raw: str) -> AgentTraceEvent:
    global _current_agent

    m = _CREWAI_AGENT_END.match(stripped)
    if m:
        agent = m.group(1).strip()
        _current_agent = ""
        return AgentTraceEvent(kind="agent_end", agent=agent, raw=raw)

    m = _CREWAI_AGENT_START.match(stripped)
    if m:
        agent = m.group(1).strip()
        _current_agent = agent
        return AgentTraceEvent(kind="agent_start", agent=agent, raw=raw)

    m = _CREWAI_ACTION.match(stripped)
    if m:
        tool = m.group(1).strip()
        return AgentTraceEvent(
            kind="tool_call", agent=_current_agent, tool=tool, raw=raw
        )

    m = _CREWAI_OBSERVATION.match(stripped)
    if m:
        result = m.group(1).strip()
        return AgentTraceEvent(
            kind="tool_result", agent=_current_agent, tool="", result=result, raw=raw
        )

    m = _CREWAI_FINAL.match(stripped)
    if m:
        return AgentTraceEvent(kind="output", text=m.group(1).strip(), raw=raw)

    m = _CREWAI_TASK.match(stripped)
    if m:
        return AgentTraceEvent(
            kind="agent_start", agent=_current_agent or "Task", raw=raw
        )

    return AgentTraceEvent(kind="raw", text=stripped, raw=raw)


def _parse_langgraph(stripped: str, raw: str) -> AgentTraceEvent:
    global _current_agent

    m = _LG_ENTERING.match(stripped)
    if m:
        agent = m.group(1).strip()
        _current_agent = agent
        return AgentTraceEvent(kind="agent_start", agent=agent, raw=raw)

    m = _LG_TOOL_CALL.match(stripped)
    if m:
        tool = m.group(1).strip()
        return AgentTraceEvent(
            kind="tool_call", agent=_current_agent, tool=tool, raw=raw
        )

    m = _LG_TOOL_MSG.match(stripped)
    if m:
        result = m.group(1).strip()
        return AgentTraceEvent(
            kind="tool_result", agent=_current_agent, tool="", result=result, raw=raw
        )

    return AgentTraceEvent(kind="raw", text=stripped, raw=raw)


def reset_parser_state() -> None:
    """Reset module-level state between parse sessions."""
    global _current_agent
    _current_agent = ""
