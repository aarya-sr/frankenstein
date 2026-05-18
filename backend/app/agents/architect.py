"""Architect agent — generates framework-agnostic agent specifications.

Model: claude-sonnet-4-6
Purpose: Transform validated RequirementsDoc into a complete AgentSpec.
Process: RAG queries (past specs, tools, anti-patterns) → task decomposition
         → tool matching → agent grouping → flow design → compile spec.

Two modes:
  Generate — fresh spec from requirements + RAG context.
  Revise  — address Critic findings while preserving working parts.
"""

import json
import logging

from pydantic import ValidationError

from app.models.requirements import RequirementsDoc
from app.models.spec import AgentSpec
from app.models.state import FrankensteinState
from app.models.tools import ToolSchema
from app.services.chroma_service import ChromaService
from app.services.llm_service import LLMService, extract_json

logger = logging.getLogger(__name__)

AGENT_NAME = "architect"

# ── System Prompts ────────────────────────────────────────────────────

SPEC_GENERATION_SYSTEM = """\
You are the Architect agent in Frankenstein, a meta-agentic system that builds
AI agent pipelines from natural language requirements.

Transform the provided RequirementsDoc into a complete AgentSpec.

## Your 8-Step Process

### 1. TASK DECOMPOSITION
Break requirements.process_steps into discrete computational tasks.
Tag each with: input format, output format, capability type
(text_extraction | calculation | reasoning | generation | api_call | data_processing).

### 2. TOOL SELECTION
Match each task to a tool from the provided Tool Schema Library.
Selection criteria — in order of importance:
  a. tool.accepts MUST include the task's input format
  b. tool.outputs MUST produce what downstream tasks need
  c. Respect tool.limitations — never assign a tool for something it cannot do
  d. Respect tool.incompatible_with — never pair conflicting tools
  e. Prefer tools in each other's compatible_with lists

### 3. AGENT GROUPING
Group related tasks into agents:
  - Tasks in a tight data loop → same agent
  - Independent task chains → separate agents
  - Each agent needs: id (snake_case), role, goal, backstory, tools list
  - reasoning_strategy: "react" (tool-using), "cot" (analysis), "plan_execute" (multi-step)

### 4. EXECUTION FLOW
Choose pattern from agent dependencies:
  - Independent agents → parallel
  - Linear chain → sequential
  - Conditional branching / state routing → graph → set framework_target="langgraph"
  - Manager delegates to workers → hierarchical → set framework_target="crewai"

If pattern is "graph": define nodes (agent IDs) and edges.
If pattern is NOT "graph": set graph to null.

### 5. MEMORY DESIGN
  - shared_keys: fields flowing between agents
  - strategy: "shared" for multi-agent state, "none" for independent agents
  - persistence: "session" (one-off) or "permanent" (learning system)

### 6. ERROR HANDLING
Per agent: on_failure (retry | fallback | skip | abort), max_retries, fallback_agent.
Never use "skip" on agents that have downstream dependents.

### 7. I/O CONTRACTS
Per agent: input_schema + output_schema with typed, named fields.
Every required output of agent A must appear in the input_schema of downstream agent B.
Each task in the first agent's input_schema MUST be in the pipeline_input_schema (step 8).

### 8. PIPELINE INPUT/OUTPUT CONTRACT (CRITICAL)
This is how data ENTERS and LEAVES the entire pipeline. Without this, the generated
code has nothing to wire `crew.kickoff(inputs=...)` or `graph.invoke(...)` to.

  - metadata.pipeline_input_schema: SchemaField list describing the shape the very
    first agent receives. EVERY required field of the first agent's input_schema
    MUST appear here (subset rule). Use the requirements.sample_input_example as
    a source of truth for field names.
  - metadata.pipeline_output_schema: SchemaField list describing the final return
    shape (typically matches the last agent's output_schema).
  - sample_input: a concrete dict, keys matching pipeline_input_schema field names.
    Pull from requirements.sample_input_example if present; otherwise synthesize a
    realistic example from the domain. NEVER leave this empty — the test harness
    uses it to actually run the pipeline.

Additionally, write each agent's task description so it references its input fields
by their EXACT field names (e.g. "Process the {application_data} to extract..."),
because the Builder will turn those into CrewAI template variables.

## Output — strict JSON

Return ONE JSON object matching this exact schema (no extra keys):

{
  "metadata": {
    "name": "descriptive_pipeline_name",
    "domain": "matches requirements.domain",
    "framework_target": "crewai" or "langgraph",
    "decision_rationale": "2-4 sentences: why this framework, why these tools, why this agent grouping",
    "created_from_pattern": null,
    "pipeline_input_schema": {"fields": [{"name": "f", "type": "string", "required": true}]},
    "pipeline_output_schema": {"fields": [{"name": "f", "type": "string", "required": true}]}
  },
  "agents": [
    {
      "id": "snake_case",
      "role": "one-line",
      "goal": "achievement statement",
      "backstory": "persona context for the LLM driving this agent",
      "tools": ["tool_instance_id"],
      "reasoning_strategy": "react",
      "receives_from": ["agent_id"],
      "sends_to": ["agent_id"]
    }
  ],
  "tools": [
    {
      "id": "instance_id",
      "library_ref": "tool_schema_library_id",
      "config": {},
      "accepts": ["format"],
      "outputs": ["format"]
    }
  ],
  "memory": {
    "strategy": "shared",
    "shared_keys": ["key"],
    "persistence": "session"
  },
  "execution_flow": {
    "pattern": "sequential",
    "graph": null
  },
  "error_handling": [
    {"agent_id": "id", "on_failure": "retry", "max_retries": 2, "fallback_agent": null}
  ],
  "io_contracts": [
    {
      "agent_id": "id",
      "input_schema": {"fields": [{"name": "f", "type": "string", "required": true}]},
      "output_schema": {"fields": [{"name": "f", "type": "string", "required": true}]}
    }
  ],
  "sample_input": {"<field>": "<concrete value matching pipeline_input_schema>"}
}

CRITICAL RULES:
- Every agent MUST appear in io_contracts AND error_handling
- tools[].library_ref MUST match an ID from the provided Tool Schema Library — NEVER
  invent tool IDs that are not in the library. If a capability is not covered by the
  available tools, implement it as inline logic in the agent rather than referencing
  a nonexistent tool. The ONLY valid library_ref values are the "id" fields from the
  "Available Tools from Library" section below.
- agents[].tools MUST reference tools[].id values
- execution_flow.graph is REQUIRED when pattern is "graph", null otherwise
- For "graph" edges, use "from_agent" and "to_agent" as the key names
- metadata.pipeline_input_schema MUST be populated (non-empty fields list)
- sample_input MUST be a non-empty dict with keys matching pipeline_input_schema
- First agent's input_schema fields MUST be a subset of pipeline_input_schema fields"""

SPEC_REVISION_SYSTEM = """\
You are the Architect agent revising a specification after Critic review.

You receive:
1. Current AgentSpec (JSON)
2. CritiqueReport with severity-scored findings
3. Original requirements

Rules:
- MUST fix every finding with severity "critical"
- SHOULD fix "warning" findings where feasible
- MAY address "suggestion" findings
- Preserve everything that already works — minimal, targeted changes
- Do NOT introduce new issues while fixing
- If removing an agent, ensure no downstream agents are orphaned
- If adding a field, ensure contracts stay consistent

Return the COMPLETE revised AgentSpec as JSON (same schema as original)."""


# ── Agent Entry Point ─────────────────────────────────────────────────


def architect_agent(
    state: FrankensteinState,
    *,
    llm: LLMService | None = None,
    chroma: ChromaService | None = None,
) -> dict:
    """Architect node — generates or revises an AgentSpec.

    Generate mode: requirements present, no critique feedback.
    Revise mode: spec + critique present (looping back from Critic).
    """
    from app.services.chroma_service import ChromaService as _CS
    from app.services.llm_service import LLMService as _LS

    if llm is None:
        llm = _LS()
    if chroma is None:
        chroma = _CS()

    has_critique = state.get("critique") is not None and state.get("spec") is not None

    if has_critique:
        return _revise(state, llm)
    return _generate(state, llm, chroma)


# ── Generate Mode ─────────────────────────────────────────────────────


def _generate(
    state: FrankensteinState,
    llm: LLMService,
    chroma: ChromaService,
) -> dict:
    """Generate a fresh AgentSpec from requirements + RAG context."""
    requirements: RequirementsDoc = state["requirements"]
    logger.info("Architect: generating spec for domain '%s'", requirements.domain)

    # ── RAG: gather context ───────────────────────────────────────────
    req_summary = _requirements_summary(requirements)

    past_specs = chroma.find_similar_specs(req_summary, n_results=3)
    anti_patterns = chroma.check_anti_patterns(req_summary, n_results=5)

    # Query tools for each process step's capability
    all_tools: list[ToolSchema] = []
    seen_ids: set[str] = set()
    for step in requirements.process_steps:
        matches = chroma.find_tools_for_capability(step.description, n_results=5)
        for t in matches:
            if t.id not in seen_ids:
                all_tools.append(t)
                seen_ids.add(t.id)

    logger.info(
        "Architect RAG: %d past specs, %d tools, %d anti-patterns",
        len(past_specs),
        len(all_tools),
        len(anti_patterns),
    )

    # ── Build LLM context ────────────────────────────────────────────
    tool_ids = [t.id for t in all_tools]
    user_parts = [
        "## Requirements\n\n" + requirements.model_dump_json(indent=2),
        "\n\n## Available Tools from Library\n\n"
        + f"**VALID tool IDs (only use these as library_ref):** {tool_ids}\n\n"
        + _format_tools(all_tools),
    ]
    if past_specs:
        user_parts.append(
            "\n\n## Past Similar Specs (reference only)\n\n"
            + json.dumps(past_specs, indent=2, default=str)
        )
    if anti_patterns:
        user_parts.append(
            "\n\n## Known Anti-Patterns (AVOID these)\n\n"
            + json.dumps(anti_patterns, indent=2, default=str)
        )

    # ── Call LLM ─────────────────────────────────────────────────────
    response = llm.call(
        agent_name=AGENT_NAME,
        system_prompt=SPEC_GENERATION_SYSTEM,
        user_prompt="\n".join(user_parts),
        json_mode=True,
        temperature=0.15,
    )

    spec = _parse_spec(response)
    reasoning = spec.metadata.decision_rationale or ""
    logger.info(
        "Architect: generated '%s' — %d agents, framework=%s",
        spec.metadata.name,
        len(spec.agents),
        spec.metadata.framework_target,
    )

    return {
        "spec": spec,
        "architect_reasoning": reasoning,
        "tool_library_matches": all_tools,
        "past_spec_matches": past_specs,
        "spec_iteration": state.get("spec_iteration", 0) + 1,
    }


# ── Revise Mode ───────────────────────────────────────────────────────


def _revise(state: FrankensteinState, llm: LLMService) -> dict:
    """Revise an existing spec to address Critic findings."""
    spec: AgentSpec = state["spec"]
    critique = state["critique"]
    requirements: RequirementsDoc = state["requirements"]

    criticals = [f for f in critique.findings if f.severity == "critical"]
    warnings = [f for f in critique.findings if f.severity == "warning"]
    logger.info(
        "Architect: revising — %d criticals, %d warnings",
        len(criticals),
        len(warnings),
    )

    user_parts = [
        "## Current Spec\n\n" + spec.model_dump_json(indent=2),
        "\n\n## Critique Findings\n\n" + critique.model_dump_json(indent=2),
        "\n\n## Original Requirements\n\n" + requirements.model_dump_json(indent=2),
    ]

    response = llm.call(
        agent_name=AGENT_NAME,
        system_prompt=SPEC_REVISION_SYSTEM,
        user_prompt="\n".join(user_parts),
        json_mode=True,
        temperature=0.1,
    )

    revised = _parse_spec(response)
    reasoning = revised.metadata.decision_rationale or ""
    logger.info("Architect: revision complete — '%s'", revised.metadata.name)

    return {
        "spec": revised,
        "architect_reasoning": reasoning,
        "spec_iteration": state.get("spec_iteration", 0) + 1,
    }


# ── Helpers ───────────────────────────────────────────────────────────


def _requirements_summary(req: RequirementsDoc) -> str:
    """Concise text summary for RAG queries."""
    steps = " → ".join(s.description for s in req.process_steps)
    inputs = ", ".join(f"{i.name} ({i.format})" for i in req.inputs)
    outputs = ", ".join(f"{o.name} ({o.format})" for o in req.outputs)
    return f"Domain: {req.domain}. Inputs: {inputs}. Process: {steps}. Outputs: {outputs}."


def _format_tools(tools: list[ToolSchema]) -> str:
    """Format tool schemas for prompt injection (omits code_template to save tokens)."""
    entries = []
    for t in tools:
        entries.append(
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "accepts": t.accepts,
                "outputs": t.outputs,
                "output_format": t.output_format,
                "limitations": t.limitations,
                "compatible_with": t.compatible_with,
                "incompatible_with": t.incompatible_with,
            }
        )
    return json.dumps(entries, indent=2)


def _parse_spec(response: str) -> AgentSpec:
    """Parse LLM JSON response into AgentSpec, normalising edge key names."""
    cleaned = extract_json(response)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error("Raw architect response (first 500 chars): %s", response[:500])
        raise ValueError(f"Architect returned invalid JSON: {e}") from e

    # LLMs sometimes use "from"/"to" instead of "from_agent"/"to_agent"
    ef = data.get("execution_flow", {})
    graph = ef.get("graph")
    if graph and "edges" in graph:
        for edge in graph["edges"]:
            if "from" in edge and "from_agent" not in edge:
                edge["from_agent"] = edge.pop("from")
            if "to" in edge and "to_agent" not in edge:
                edge["to_agent"] = edge.pop("to")

    # Coerce invalid execution_flow.pattern to nearest valid value
    valid_patterns = {"sequential", "parallel", "hierarchical", "graph"}
    pattern = ef.get("pattern", "")
    if pattern and pattern not in valid_patterns:
        logger.warning("Architect returned invalid pattern '%s', coercing to 'graph'", pattern)
        ef["pattern"] = "graph"

    try:
        return AgentSpec(**data)
    except ValidationError as e:
        raise ValueError(f"Architect produced invalid spec: {e}") from e
