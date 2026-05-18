"""LangGraph pipeline graph definition for Frankenstein.

Six-stage StateGraph with two human checkpoints and two feedback loops:

  elicitor → [human_review_requirements] → architect → critic
                                              ↑            │
                                              └── (criticals > 0)
                                                           │
                                              (no criticals)
                                                           ▼
                                          [human_review_spec] → builder → tester
                                                                  ↑          │
                                                    (code-level fix) ────────┤
                                              ↑                              │
                                    (spec-level fix) ────────────────────────┤
                                                                             │
                                                                  (all pass) │
                                                                             ▼
                                                                          learner → END
"""

import logging

from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph

from app.agents.architect import architect_agent
from app.agents.builder import builder_agent
from app.agents.critic import critic_agent
from app.agents.elicitor import elicitor_ask, elicitor_compile, route_after_elicitor_ask
from app.agents.learner import learner_agent
from app.agents.tester import tester_agent
from app.config import settings
from app.models.state import FrankensteinState

logger = logging.getLogger(__name__)


# ── Human Checkpoints ─────────────────────────────────────────────────

from app.pipeline.checkpoints import (  # noqa: E402
    human_checkpoint_requirements,
    human_checkpoint_spec,
)


# ── Routing Functions ─────────────────────────────────────────────────


def route_after_critique(state: FrankensteinState) -> str:
    """Critic → Architect (loop on criticals) or → human_review_spec."""
    session_id = state.get("session_id", "?")
    critique = state.get("critique")
    if not critique:
        logger.info("[%s] ROUTE: critic → human_review_spec (no critique)", session_id)
        return "human_review_spec"

    criticals = [f for f in critique.findings if f.severity == "critical"]
    warnings = [f for f in critique.findings if f.severity == "warning"]
    iteration = state.get("spec_iteration", 0)
    max_iter = settings.max_spec_iterations

    if criticals and iteration < max_iter:
        logger.info(
            "[%s] ROUTE: critic → architect (criticals=%d, warnings=%d, iteration=%d/%d)",
            session_id, len(criticals), len(warnings), iteration, max_iter,
        )
        return "architect"

    logger.info("[%s] ROUTE: critic → human_review_spec (criticals=%d, iteration=%d/%d)",
                session_id, len(criticals), iteration, max_iter)
    return "human_review_spec"


def route_after_test(state: FrankensteinState) -> str:
    """Tester → learner (pass) | builder (code fix) | architect (spec fix)."""
    session_id = state.get("session_id", "?")
    test_results = state.get("test_results")
    if not test_results:
        logger.info("[%s] ROUTE: tester → learner (no test results)", session_id)
        return "learner"

    if test_results.all_passed:
        logger.info("[%s] ROUTE: tester → learner (all %d tests passed)", session_id, test_results.total)
        return "learner"

    # Check failure traces for root cause level
    failure_traces = state.get("failure_traces", [])
    has_spec_failure = any(t.root_cause_level == "spec" for t in failure_traces)

    spec_iter = state.get("spec_iteration", 0)
    build_iter = state.get("build_iteration", 0)
    max_spec = settings.max_spec_iterations
    max_build = settings.max_build_iterations

    if has_spec_failure:
        if spec_iter < max_spec:
            logger.info(
                "[%s] ROUTE: tester → architect (spec-level failure, spec_iter=%d/%d)",
                session_id, spec_iter, max_spec,
            )
            return "architect"
        logger.warning(
            "[%s] ROUTE: tester → learner (spec-level failure but spec_iter cap %d reached)",
            session_id, max_spec,
        )
        return "learner"

    if build_iter >= max_build:
        logger.warning(
            "[%s] ROUTE: tester → learner (build_iter cap %d reached, tests still failing)",
            session_id, max_build,
        )
        return "learner"

    logger.info("[%s] ROUTE: tester → builder (code-level fix, build_iter=%d/%d)", session_id, build_iter, max_build)
    return "builder"


# ── Graph Construction ────────────────────────────────────────────────


def build_graph() -> StateGraph:
    """Build the complete Frankenstein pipeline graph."""
    graph = StateGraph(FrankensteinState)

    # Nodes
    graph.add_node("elicitor_ask", elicitor_ask)
    graph.add_node("elicitor_compile", elicitor_compile)
    graph.add_node("human_review_requirements", human_checkpoint_requirements)
    graph.add_node("architect", architect_agent)
    graph.add_node("critic", critic_agent)
    graph.add_node("human_review_spec", human_checkpoint_spec)
    graph.add_node("builder", builder_agent)
    graph.add_node("tester", tester_agent)
    graph.add_node("learner", learner_agent)

    # Linear edges
    graph.set_entry_point("elicitor_ask")
    graph.add_edge("elicitor_compile", "human_review_requirements")
    graph.add_edge("human_review_requirements", "architect")
    graph.add_edge("architect", "critic")
    graph.add_edge("human_review_spec", "builder")
    graph.add_edge("builder", "tester")
    graph.add_edge("learner", END)

    # Conditional edges (feedback loops)
    graph.add_conditional_edges(
        "elicitor_ask",
        route_after_elicitor_ask,
        {"elicitor_ask": "elicitor_ask", "elicitor_compile": "elicitor_compile"},
    )
    graph.add_conditional_edges(
        "critic",
        route_after_critique,
        {"architect": "architect", "human_review_spec": "human_review_spec"},
    )
    graph.add_conditional_edges(
        "tester",
        route_after_test,
        {"learner": "learner", "builder": "builder", "architect": "architect"},
    )

    return graph


_db_path = Path(__file__).parent.parent.parent / "checkpoints.sqlite3"

import sqlite3 as _sqlite3
_conn = _sqlite3.connect(str(_db_path), check_same_thread=False)
checkpointer = SqliteSaver(_conn)

compiled_graph = build_graph().compile(checkpointer=checkpointer)
