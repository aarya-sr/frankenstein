"""Learner agent — stores build outcomes and extracts patterns.

Model: gpt-4o-mini
Purpose: Post-build analysis, pattern extraction, Chroma memory storage.
Process: Analyse full pipeline run → extract success/failure/anti patterns →
         construct BuildOutcome → store in Chroma collections for future RAG.
"""

import hashlib
import json
import logging
import time
import uuid

from pydantic import ValidationError

from app.models.learning import BuildOutcome
from app.models.requirements import RequirementsDoc
from app.models.spec import AgentSpec
from app.models.state import FrankensteinState
from app.models.testing import TestReport
from app.services.chroma_service import ChromaService
from app.services.llm_service import LLMService, extract_json

logger = logging.getLogger(__name__)

AGENT_NAME = "learner"

# ── System Prompt ─────────────────────────────────────────────────────

PATTERN_EXTRACTION_SYSTEM = """\
You are the Learner agent analysing a completed Frankenstein build pipeline.

Given the full build context (requirements, spec, test results, failure traces),
extract patterns for future builds.

Produce four lists:

1. **success_patterns** — things that worked well.
   Example: "Sequential flow for document-processing pipelines reduces format
   conversion errors between agents."

2. **failure_patterns** — things that went wrong THIS build.
   Example: "pdf_parser_pymupdf assigned to handle scanned documents despite
   'no OCR' limitation — caused extraction failures."

3. **anti_patterns** — generalised patterns to AVOID in future builds.
   Example: "Never assign text-extraction tools to scanned-document input
   without an OCR preprocessing step."

4. **lessons_learned** — domain-specific takeaways.
   Example: "Financial domain requires explicit decimal precision handling
   in all calculation tools."

Rules:
- Each entry is a single, self-contained sentence.
- Be specific — reference actual tool IDs, agent roles, or domain details.
- Empty lists are fine if nothing applies.
- Do not repeat the same insight in multiple lists.

Return JSON:
{
  "success_patterns": ["..."],
  "failure_patterns": ["..."],
  "anti_patterns": ["..."],
  "lessons_learned": ["..."]
}"""


# ── Agent Entry Point ─────────────────────────────────────────────────


def learner_agent(
    state: FrankensteinState,
    *,
    llm: LLMService | None = None,
    chroma: ChromaService | None = None,
) -> dict:
    """Learner node — extracts patterns, stores build outcome in Chroma."""
    from app.services.chroma_service import ChromaService as _CS
    from app.services.llm_service import LLMService as _LS

    if llm is None:
        llm = _LS()
    if chroma is None:
        chroma = _CS()

    spec: AgentSpec = state["spec"]
    requirements: RequirementsDoc = state["requirements"]
    test_results: TestReport | None = state.get("test_results")
    failure_traces = state.get("failure_traces", [])

    session_id = state.get("session_id", "?")
    logger.info("[%s] Learner: START — analysing build for '%s'", session_id, spec.metadata.name)

    # ── 1. Extract patterns via LLM ──────────────────────────────────
    patterns = _extract_patterns(llm, state)

    # ── 2. Determine outcome status ──────────────────────────────────
    if test_results and test_results.all_passed:
        outcome_status = "success"
        partial_details = None
    elif test_results and test_results.passed > 0:
        outcome_status = "partial_success"
        partial_details = (
            f"{test_results.passed}/{test_results.total} tests passed, "
            f"{test_results.failed} failed"
        )
    else:
        outcome_status = "failure"
        partial_details = "No tests passed" if test_results else "No test results"

    # ── 3. Build outcome record ──────────────────────────────────────
    req_json = requirements.model_dump_json()
    req_hash = hashlib.sha256(req_json.encode()).hexdigest()[:16]

    req_summary = (
        f"{requirements.domain}: "
        + " → ".join(s.description for s in requirements.process_steps[:4])
    )

    outcome = BuildOutcome(
        requirements_hash=req_hash,
        requirements_summary=req_summary,
        domain=requirements.domain,
        spec_snapshot=spec,
        framework_used=spec.metadata.framework_target,
        tools_used=[t.library_ref for t in spec.tools],
        test_results=test_results or TestReport(),
        iterations_needed=(
            state.get("spec_iteration", 0) + state.get("build_iteration", 0)
        ),
        success_patterns=patterns.get("success_patterns", []),
        failure_patterns=patterns.get("failure_patterns", []),
        anti_patterns=patterns.get("anti_patterns", []),
        lessons_learned=patterns.get("lessons_learned", []),
        outcome=outcome_status,
        partial_success_details=partial_details,
    )

    # ── 4. Store in Chroma ───────────────────────────────────────────
    _store_learnings(chroma, outcome, requirements)
    _store_repair_patterns(chroma, state, outcome)
    logger.info(
        "Learner: stored outcome '%s' for domain '%s'",
        outcome_status,
        requirements.domain,
    )

    logger.info("[%s] Learner: DONE — outcome=%s", session_id, outcome_status)
    return {"build_outcome": outcome}


# ── Pattern Extraction ────────────────────────────────────────────────


def _extract_patterns(llm: LLMService, state: FrankensteinState) -> dict:
    """LLM call to analyse the build and extract reusable patterns."""
    spec: AgentSpec = state["spec"]
    requirements: RequirementsDoc = state["requirements"]
    test_results: TestReport | None = state.get("test_results")
    failure_traces = state.get("failure_traces", [])

    user_parts = [
        f"## Requirements\n\n{requirements.model_dump_json(indent=2)}",
        f"\n\n## Spec\n\n{spec.model_dump_json(indent=2)}",
    ]

    if test_results:
        user_parts.append(
            f"\n\n## Test Results\n\n{test_results.model_dump_json(indent=2)}"
        )

    if failure_traces:
        traces_json = json.dumps(
            [ft.model_dump() for ft in failure_traces], indent=2
        )
        user_parts.append(f"\n\n## Failure Traces\n\n{traces_json}")

    user_parts.append(
        f"\n\n## Pipeline Iterations\n\n"
        f"Spec iterations: {state.get('spec_iteration', 0)}\n"
        f"Build iterations: {state.get('build_iteration', 0)}"
    )

    response = llm.call(
        agent_name=AGENT_NAME,
        system_prompt=PATTERN_EXTRACTION_SYSTEM,
        user_prompt="\n".join(user_parts),
        json_mode=True,
        temperature=0.3,
    )

    try:
        return json.loads(extract_json(response))
    except json.JSONDecodeError as e:
        logger.error("Learner: pattern extraction parse failed: %s", e)
        return {
            "success_patterns": [],
            "failure_patterns": [],
            "anti_patterns": [],
            "lessons_learned": [],
        }


# ── Chroma Storage ────────────────────────────────────────────────────


def _store_learnings(
    chroma: ChromaService,
    outcome: BuildOutcome,
    requirements: RequirementsDoc,
) -> None:
    """Persist build outcome across Chroma collections."""
    build_id = f"build_{outcome.requirements_hash}_{uuid.uuid4().hex[:6]}"

    # ── spec_patterns: store the validated spec for future RAG ────────
    spec_meta = {
        "domain": outcome.domain,
        "framework": outcome.framework_used,
        "outcome": outcome.outcome,
        "tools_used": json.dumps(outcome.tools_used),
        "iterations": outcome.iterations_needed,
        "pipeline_input_schema": json.dumps(
            outcome.spec_snapshot.metadata.pipeline_input_schema.model_dump()
            if outcome.spec_snapshot.metadata.pipeline_input_schema else {}
        ),
        "sample_input": json.dumps(
            outcome.spec_snapshot.sample_input
            if getattr(outcome.spec_snapshot, "sample_input", None) else {}
        ),
    }
    chroma.store_spec_pattern(
        spec_id=build_id,
        requirements_summary=outcome.requirements_summary,
        metadata=spec_meta,
    )

    # ── anti_patterns: store each anti-pattern separately ────────────
    for i, ap in enumerate(outcome.anti_patterns):
        chroma.store_anti_pattern(
            pattern_id=f"{build_id}_anti_{i}",
            description=ap,
            metadata={
                "domain": outcome.domain,
                "source_build": build_id,
                "severity": "high",
            },
        )

    # ── domain_insights: store lessons learned ───────────────────────
    for i, lesson in enumerate(outcome.lessons_learned):
        chroma.store_domain_insight(
            insight_id=f"{build_id}_lesson_{i}",
            insight=lesson,
            metadata={
                "domain": outcome.domain,
                "source_build": build_id,
                "outcome": outcome.outcome,
            },
        )

    # ── tool_compatibility: update from build results ────────────────
    if outcome.outcome == "success":
        # Tools that worked together are compatible
        for i, t1 in enumerate(outcome.tools_used):
            others = [t for j, t in enumerate(outcome.tools_used) if j != i]
            if others:
                chroma.update_tool_compatibility(t1, compatible=others)

    for fp in outcome.failure_patterns:
        # Try to extract tool IDs from failure patterns for incompatibility
        for tool_id in outcome.tools_used:
            if tool_id in fp:
                other_tools = [t for t in outcome.tools_used if t != tool_id]
                if other_tools:
                    chroma.update_tool_compatibility(
                        tool_id, incompatible=other_tools
                    )

    logger.info(
        "Learner: stored %d anti-patterns, %d lessons for build %s",
        len(outcome.anti_patterns),
        len(outcome.lessons_learned),
        build_id,
    )


def _store_repair_patterns(
    chroma: ChromaService, state: FrankensteinState, outcome: BuildOutcome
) -> None:
    """Persist Builder repair history as RAG hints for future builds."""
    repair_history = state.get("repair_history", [])
    if not repair_history:
        return
    build_id = f"build_{outcome.requirements_hash}"
    stored = 0
    for i, entry in enumerate(repair_history):
        errors = entry.get("errors", [])
        fix_summary = entry.get("fix_summary") or entry.get("notes") or "applied LLM repair"
        for j, err in enumerate(errors):
            err_code = err.get("code", "UNKNOWN")
            err_msg = err.get("message", "")
            try:
                chroma.store_repair_pattern(
                    pattern_id=f"{build_id}_rep_{i}_{j}_{uuid.uuid4().hex[:4]}",
                    error_text=f"[{err_code}] {err_msg}",
                    fix_text=str(fix_summary),
                    metadata={
                        "code": err_code,
                        "framework": outcome.framework_used,
                        "domain": outcome.domain,
                        "build_outcome": outcome.outcome,
                    },
                )
                stored += 1
            except Exception as e:
                logger.warning("Learner: repair pattern store failed: %s", e)
    if stored:
        logger.info("Learner: stored %d repair patterns", stored)
