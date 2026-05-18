"""Tests for log_parser — CrewAI and LangGraph pattern matching."""

import pytest

from app.services.log_parser import parse_line, reset_parser_state


@pytest.fixture(autouse=True)
def _reset():
    reset_parser_state()
    yield
    reset_parser_state()


# ── CrewAI Patterns ──────────────────────────────────────────────────


class TestCrewAI:
    def test_agent_start(self):
        event = parse_line("[Agent: Researcher] Starting analysis", "crewai")
        assert event.kind == "agent_start"
        assert event.agent == "Researcher"

    def test_agent_start_working_agent(self):
        event = parse_line("[Working Agent: Analyst] Running", "crewai")
        assert event.kind == "agent_start"
        assert event.agent == "Analyst"

    def test_agent_end(self):
        event = parse_line("[Agent: Researcher] finished task", "crewai")
        assert event.kind == "agent_end"
        assert event.agent == "Researcher"

    def test_action_tool_call(self):
        # Set current agent first
        parse_line("[Agent: Researcher] Starting", "crewai")
        event = parse_line("Action: web_search", "crewai")
        assert event.kind == "tool_call"
        assert event.tool == "web_search"
        assert event.agent == "Researcher"

    def test_observation_tool_result(self):
        parse_line("[Agent: Researcher] Starting", "crewai")
        event = parse_line("Observation: Found 3 results", "crewai")
        assert event.kind == "tool_result"
        assert event.result == "Found 3 results"

    def test_final_answer_output(self):
        event = parse_line("Final Answer: The result is 42", "crewai")
        assert event.kind == "output"
        assert event.text == "The result is 42"

    def test_task_line(self):
        event = parse_line("[Task] Analyze the data", "crewai")
        assert event.kind == "agent_start"

    def test_unrecognized_line_is_raw(self):
        event = parse_line("some random log output", "crewai")
        assert event.kind == "raw"
        assert event.text == "some random log output"

    def test_empty_line_is_raw(self):
        event = parse_line("", "crewai")
        assert event.kind == "raw"
        assert event.text == ""

    def test_whitespace_only_is_raw(self):
        event = parse_line("   ", "crewai")
        assert event.kind == "raw"


# ── LangGraph Patterns ──────────────────────────────────────────────


class TestLangGraph:
    def test_entering_node(self):
        event = parse_line("> Entering new ResearchNode", "langgraph")
        assert event.kind == "agent_start"
        assert event.agent == "ResearchNode"

    def test_tool_call(self):
        parse_line("> Entering new ResearchNode", "langgraph")
        event = parse_line("tool_call: search_tool", "langgraph")
        assert event.kind == "tool_call"
        assert event.tool == "search_tool"
        assert event.agent == "ResearchNode"

    def test_tool_message(self):
        parse_line("> Entering new ResearchNode", "langgraph")
        event = parse_line("ToolMessage: search returned 5 results", "langgraph")
        assert event.kind == "tool_result"
        assert event.result == "search returned 5 results"

    def test_unrecognized_is_raw(self):
        event = parse_line("just some output", "langgraph")
        assert event.kind == "raw"


# ── Framework fallback ───────────────────────────────────────────────


class TestFallback:
    def test_unknown_framework_returns_raw(self):
        event = parse_line("[Agent: Test] hello", "autogen")
        assert event.kind == "raw"

    def test_raw_has_original_line(self):
        event = parse_line("original line here\n", "crewai")
        assert event.raw == "original line here\n"


# ── State tracking ──────────────────────────────────────────────────


class TestStateTracking:
    def test_agent_persists_across_tool_calls(self):
        parse_line("[Agent: Writer] Starting", "crewai")
        e1 = parse_line("Action: text_gen", "crewai")
        e2 = parse_line("Action: spell_check", "crewai")
        assert e1.agent == "Writer"
        assert e2.agent == "Writer"

    def test_agent_resets_on_end(self):
        parse_line("[Agent: Writer] Starting", "crewai")
        parse_line("[Agent: Writer] finished task", "crewai")
        e = parse_line("Action: orphan_tool", "crewai")
        assert e.agent == ""

    def test_reset_parser_state(self):
        parse_line("[Agent: Writer] Starting", "crewai")
        reset_parser_state()
        e = parse_line("Action: orphan_tool", "crewai")
        assert e.agent == ""
