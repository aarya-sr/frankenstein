"""Critic agent — adversarial specification review.

Model: gpt-4o (different family from Architect — cross-model review on purpose)
Purpose: Attack the spec from 6 angles, surface flaws before building.
Process: 5 programmatic checks + LLM semantic review → aggregated CritiqueReport.

Attack vectors:
  1. Circular dependencies  — topological sort
  2. Format compatibility   — output→input schema matching across edges
  3. Dependency completeness — required fields traced to upstream producers
  4. Dead-end analysis      — error-handling coverage + skip-on-critical-path
  5. Resource conflicts     — parallel agents writing same shared memory keys
  6. Tool + semantic review — LLM-powered capability / coherence check
"""

import json
import logging
from collections import defaultdict

from app.agents._validation import PYDANTIC_RESERVED
from app.models.critique import CritiqueReport, Finding
from app.models.spec import AgentSpec, GraphEdge
from app.models.state import FrankensteinState
from app.services.chroma_service import ChromaService
from app.services.llm_service import extract_json
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

AGENT_NAME = "critic"

# ── LLM prompt for semantic review ────────────────────────────────────

SEMANTIC_REVIEW_SYSTEM = """\
You are the Critic agent in Frankenstein. Your job is adversarial — find flaws
in agent specifications that automated checks cannot catch.

Five automated checks have already run (circular deps, format compat, dependency
completeness, dead-ends, resource conflicts).  Their findings are provided.

YOUR additional responsibilities:

1. **TOOL VALIDATION**
   For each tool assigned to an agent:
   - Can this tool actually perform the task described in the agent's goal?
   - Does the tool's category match the agent's role?
   - Do any tool limitations conflict with the requirements?

2. **SEMANTIC COHERENCE**
   - Do agent roles/goals make sense for the domain?
   - Is reasoning_strategy appropriate? (react → tool-heavy, cot → analysis)
   - Are backstories useful context or generic filler?
   - Does the chosen execution flow match the problem's real dependency structure?

3. **SUMMARY** — 2-3 sentences assessing overall spec quality.

For each NEW issue, produce a Finding object:
{
  "vector": "tool_validation" or "semantic_coherence",
  "severity": "critical" | "warning" | "suggestion",
  "description": "what is wrong",
  "location": "agent/tool/edge affected",
  "evidence": "specific spec values",
  "suggested_fix": "actionable change"
}

Return JSON:
{
  "additional_findings": [ ... ],
  "summary": "2-3 sentence overall assessment"
}"""


# ── Agent Entry Point ─────────────────────────────────────────────────


def critic_agent(
    state: FrankensteinState,
    *,
    llm: LLMService | None = None,
    chroma: ChromaService | None = None,
) -> dict:
    """Critic node — runs 9 attack vectors against the spec."""
    from app.services.chroma_service import ChromaService as _CS
    from app.services.llm_service import LLMService as _LS

    if llm is None:
        llm = _LS()
    if chroma is None:
        chroma = _CS()

    spec: AgentSpec = state["spec"]
    iteration = state.get("spec_iteration", 1)
    logger.info("Critic: reviewing '%s' (iteration %d)", spec.metadata.name, iteration)

    # ── Programmatic checks ──────────────────────────────────────────
    findings: list[Finding] = []
    findings.extend(_check_circular_dependencies(spec))
    findings.extend(_check_format_compatibility(spec))
    findings.extend(_check_dependency_completeness(spec))
    findings.extend(_check_dead_ends(spec))
    findings.extend(_check_resource_conflicts(spec))
    findings.extend(_check_pipeline_input_wirability(spec))
    findings.extend(_check_tool_template_availability(spec, chroma))
    findings.extend(_check_tool_param_safety(spec, chroma))

    prog_count = len(findings)
    logger.info("Critic: %d findings from programmatic checks", prog_count)

    # ── LLM semantic review ──────────────────────────────────────────
    sem = _semantic_review(llm, spec, findings)
    findings.extend(sem["additional_findings"])
    summary = sem["summary"]

    logger.info(
        "Critic: %d total findings (%d programmatic, %d semantic)",
        len(findings),
        prog_count,
        len(findings) - prog_count,
    )

    return {
        "critique": CritiqueReport(
            findings=findings,
            summary=summary,
            iteration=iteration,
        ),
    }


# ── Edge Inference ───────────────────────────────────────────────────


def _get_edges(spec: AgentSpec) -> list[GraphEdge]:
    """Get edges from graph definition, or infer from agent sends_to/receives_from."""
    if spec.execution_flow.graph and spec.execution_flow.graph.edges:
        return spec.execution_flow.graph.edges

    # Infer edges from agent relationships for sequential/hierarchical specs
    edges: list[GraphEdge] = []
    seen: set[tuple[str, str]] = set()
    for agent in spec.agents:
        for target in agent.sends_to:
            pair = (agent.id, target)
            if pair not in seen:
                edges.append(GraphEdge(from_agent=agent.id, to_agent=target))
                seen.add(pair)
        for source in agent.receives_from:
            pair = (source, agent.id)
            if pair not in seen:
                edges.append(GraphEdge(from_agent=source, to_agent=agent.id))
                seen.add(pair)

    # Fallback for sequential: chain agents in order
    if not edges and spec.execution_flow.pattern == "sequential" and len(spec.agents) > 1:
        for i in range(len(spec.agents) - 1):
            edges.append(GraphEdge(
                from_agent=spec.agents[i].id,
                to_agent=spec.agents[i + 1].id,
            ))

    return edges


# ── Vector 1: Circular Dependencies ──────────────────────────────────


def _check_circular_dependencies(spec: AgentSpec) -> list[Finding]:
    """Topological sort on the execution graph — cycles are critical."""
    inferred_edges = _get_edges(spec)
    if not inferred_edges:
        return []

    adj: dict[str, list[str]] = defaultdict(list)
    in_degree: dict[str, int] = defaultdict(int)
    nodes: set[str] = {a.id for a in spec.agents}

    for edge in inferred_edges:
        adj[edge.from_agent].append(edge.to_agent)
        in_degree[edge.to_agent] += 1
        nodes.add(edge.from_agent)
        nodes.add(edge.to_agent)

    for n in nodes:
        in_degree.setdefault(n, 0)

    # Kahn's algorithm
    queue = [n for n in nodes if in_degree[n] == 0]
    ordered: list[str] = []
    while queue:
        node = queue.pop(0)
        ordered.append(node)
        for nb in adj[node]:
            in_degree[nb] -= 1
            if in_degree[nb] == 0:
                queue.append(nb)

    if len(ordered) < len(nodes):
        cycle = sorted(nodes - set(ordered))
        return [
            Finding(
                vector="circular_dependencies",
                severity="critical",
                description=f"Circular dependency among: {cycle}",
                location="execution_flow.graph",
                evidence=f"Nodes unreachable in topological sort: {cycle}",
                suggested_fix="Remove or reverse edges to break the cycle",
            )
        ]
    return []


# ── Vector 2: Format Compatibility ───────────────────────────────────


def _check_format_compatibility(spec: AgentSpec) -> list[Finding]:
    """Compare output→input schemas for every edge in the graph."""
    findings: list[Finding] = []
    contracts = {c.agent_id: c for c in spec.io_contracts}

    edges = _get_edges(spec)
    if not edges:
        return findings

    for edge in edges:
        src = contracts.get(edge.from_agent)
        dst = contracts.get(edge.to_agent)

        if not src:
            findings.append(
                Finding(
                    vector="format_compatibility",
                    severity="warning",
                    description=f"No I/O contract for source agent '{edge.from_agent}'",
                    location=f"io_contracts[{edge.from_agent}]",
                    evidence="Missing from io_contracts list",
                    suggested_fix=f"Add io_contract for '{edge.from_agent}'",
                )
            )
        if not dst:
            findings.append(
                Finding(
                    vector="format_compatibility",
                    severity="warning",
                    description=f"No I/O contract for target agent '{edge.to_agent}'",
                    location=f"io_contracts[{edge.to_agent}]",
                    evidence="Missing from io_contracts list",
                    suggested_fix=f"Add io_contract for '{edge.to_agent}'",
                )
            )
        if not src or not dst:
            continue

        src_fields = {f.name: f for f in src.output_schema.fields}

        for field in dst.input_schema.fields:
            if not field.required:
                continue
            if field.name not in src_fields:
                findings.append(
                    Finding(
                        vector="format_compatibility",
                        severity="critical",
                        description=(
                            f"'{edge.to_agent}' requires field '{field.name}' "
                            f"but '{edge.from_agent}' does not produce it"
                        ),
                        location=f"edge {edge.from_agent} → {edge.to_agent}",
                        evidence=(
                            f"Required: {field.name} ({field.type}); "
                            f"Available: {sorted(src_fields)}"
                        ),
                        suggested_fix=(
                            f"Add '{field.name}' to {edge.from_agent}'s output_schema "
                            f"or make it optional in {edge.to_agent}'s input_schema"
                        ),
                    )
                )
            elif src_fields[field.name].type != field.type:
                findings.append(
                    Finding(
                        vector="format_compatibility",
                        severity="warning",
                        description=(
                            f"Type mismatch on '{field.name}': "
                            f"'{edge.from_agent}' outputs {src_fields[field.name].type}, "
                            f"'{edge.to_agent}' expects {field.type}"
                        ),
                        location=f"edge {edge.from_agent} → {edge.to_agent}",
                        evidence=(
                            f"Source: {src_fields[field.name].type}, "
                            f"Target: {field.type}"
                        ),
                        suggested_fix="Align types or insert a transformation agent",
                    )
                )

    return findings


# ── Vector 3: Dependency Completeness ─────────────────────────────────


def _check_dependency_completeness(spec: AgentSpec) -> list[Finding]:
    """Every agent's required inputs must be produced by some upstream agent."""
    findings: list[Finding] = []
    contracts = {c.agent_id: c for c in spec.io_contracts}

    # Build upstream map
    upstream: dict[str, set[str]] = defaultdict(set)
    for edge in _get_edges(spec):
        upstream[edge.to_agent].add(edge.from_agent)

    for agent in spec.agents:
        # Entry-point agents (no upstream) receive pipeline input — skip
        if not upstream.get(agent.id):
            continue

        contract = contracts.get(agent.id)
        if not contract:
            continue

        # Collect all fields from upstream
        available: set[str] = set()
        for up_id in upstream[agent.id]:
            up_contract = contracts.get(up_id)
            if up_contract:
                available.update(f.name for f in up_contract.output_schema.fields)

        for field in contract.input_schema.fields:
            if field.required and field.name not in available:
                findings.append(
                    Finding(
                        vector="dependency_completeness",
                        severity="critical",
                        description=(
                            f"'{agent.id}' requires '{field.name}' but no "
                            f"upstream agent produces it"
                        ),
                        location=f"agent {agent.id}",
                        evidence=(
                            f"Required: {field.name}; "
                            f"Upstream: {sorted(upstream[agent.id])}; "
                            f"Available: {sorted(available)}"
                        ),
                        suggested_fix=(
                            "Add field to an upstream output_schema or "
                            "make it optional"
                        ),
                    )
                )

    return findings


# ── Vector 4: Dead-End Analysis ───────────────────────────────────────


def _check_dead_ends(spec: AgentSpec) -> list[Finding]:
    """Verify error handling coverage and catch skip-on-critical-path."""
    findings: list[Finding] = []
    handled = {eh.agent_id for eh in spec.error_handling}

    # Agents missing error handling
    for agent in spec.agents:
        if agent.id not in handled:
            findings.append(
                Finding(
                    vector="dead_end_analysis",
                    severity="warning",
                    description=f"'{agent.id}' has no error handling defined",
                    location=f"error_handling[{agent.id}]",
                    evidence="Agent missing from error_handling list",
                    suggested_fix=f"Add error_handling for '{agent.id}' (retry recommended)",
                )
            )

    # "skip" on agents with downstream dependents
    downstream: dict[str, set[str]] = defaultdict(set)
    for edge in _get_edges(spec):
        downstream[edge.from_agent].add(edge.to_agent)

    for eh in spec.error_handling:
        if eh.on_failure == "skip" and downstream.get(eh.agent_id):
            findings.append(
                Finding(
                    vector="dead_end_analysis",
                    severity="critical",
                    description=(
                        f"'{eh.agent_id}' uses on_failure='skip' but has "
                        f"downstream dependents: {sorted(downstream[eh.agent_id])}"
                    ),
                    location=f"error_handling[{eh.agent_id}]",
                    evidence=f"skip + dependents={sorted(downstream[eh.agent_id])}",
                    suggested_fix="Change to 'retry' or 'fallback'",
                )
            )

    return findings


# ── Vector 5: Resource Conflicts ──────────────────────────────────────


def _check_resource_conflicts(spec: AgentSpec) -> list[Finding]:
    """Flag parallel agents that write to the same shared memory keys."""
    findings: list[Finding] = []
    if not spec.memory.shared_keys:
        return findings

    edges = _get_edges(spec)
    if not edges:
        # Parallel pattern without edges — all agents are parallel
        if spec.execution_flow.pattern == "parallel" and len(spec.agents) > 1:
            findings.append(
                Finding(
                    vector="resource_conflicts",
                    severity="warning",
                    description=(
                        f"Parallel execution with shared memory keys "
                        f"{spec.memory.shared_keys} — potential race condition"
                    ),
                    location="memory.shared_keys + execution_flow.pattern=parallel",
                    evidence=f"shared_keys={spec.memory.shared_keys}",
                    suggested_fix="Partition keys per agent or add sequencing",
                )
            )
        return findings

    # Build dependency map to find truly parallel agent pairs
    depends_on: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        depends_on[edge.to_agent].add(edge.from_agent)

    ids = [a.id for a in spec.agents]
    for i, a1 in enumerate(ids):
        for a2 in ids[i + 1 :]:
            a1_deps = _transitive_deps(a1, depends_on)
            a2_deps = _transitive_deps(a2, depends_on)
            if a2 not in a1_deps and a1 not in a2_deps:
                findings.append(
                    Finding(
                        vector="resource_conflicts",
                        severity="warning",
                        description=(
                            f"'{a1}' and '{a2}' may run in parallel and "
                            f"both access shared keys: {spec.memory.shared_keys}"
                        ),
                        location=f"memory.shared_keys + agents {a1}, {a2}",
                        evidence="No dependency between these agents",
                        suggested_fix="Partition keys or add ordering edge",
                    )
                )

    return findings


def _transitive_deps(
    agent_id: str, depends_on: dict[str, set[str]]
) -> set[str]:
    """Compute all transitive upstream dependencies."""
    visited: set[str] = set()
    stack = list(depends_on.get(agent_id, set()))
    while stack:
        dep = stack.pop()
        if dep in visited:
            continue
        visited.add(dep)
        stack.extend(depends_on.get(dep, set()))
    return visited


# ── Vector 6: LLM Semantic Review ────────────────────────────────────


def _semantic_review(
    llm: LLMService,
    spec: AgentSpec,
    programmatic_findings: list[Finding],
) -> dict:
    """LLM-powered tool validation + semantic coherence + summary."""
    prog_json = (
        json.dumps([f.model_dump() for f in programmatic_findings], indent=2)
        if programmatic_findings
        else "No issues found by automated checks."
    )

    user_msg = (
        f"## Spec to Review\n\n{spec.model_dump_json(indent=2)}"
        f"\n\n## Automated Check Results\n\n{prog_json}"
    )

    response = llm.call(
        agent_name=AGENT_NAME,
        system_prompt=SEMANTIC_REVIEW_SYSTEM,
        user_prompt=user_msg,
        json_mode=True,
        temperature=0.2,
    )

    try:
        data = json.loads(extract_json(response))
        additional = [Finding(**f) for f in data.get("additional_findings", [])]
        summary = data.get("summary", "Review complete.")
        return {"additional_findings": additional, "summary": summary}
    except (json.JSONDecodeError, Exception) as e:
        logger.error("Critic: semantic review parse failed: %s", e)
        return {
            "additional_findings": [],
            "summary": (
                f"Semantic review parse failed: {e}. "
                f"{len(programmatic_findings)} programmatic findings stand."
            ),
        }


# ── Vector 7: Pipeline Input Wirability ───────────────────────────────


def _check_pipeline_input_wirability(spec: AgentSpec) -> list[Finding]:
    """The first agent's required input_schema fields MUST be a subset of pipeline_input_schema.

    Without this, the Builder has no anchor for `crew.kickoff(inputs=...)` /
    `graph.invoke(input)`.
    """
    findings: list[Finding] = []
    pis = spec.metadata.pipeline_input_schema

    if pis is None or not pis.fields:
        findings.append(Finding(
            vector="pipeline_input_wirability",
            severity="critical",
            description="metadata.pipeline_input_schema is missing or empty",
            location="metadata.pipeline_input_schema",
            evidence="No fields declared as pipeline entry points",
            suggested_fix="Add pipeline_input_schema describing the dict shape that "
                          "crew.kickoff(inputs=...) / graph.invoke(...) will receive",
        ))
        return findings

    if not spec.sample_input:
        findings.append(Finding(
            vector="pipeline_input_wirability",
            severity="critical",
            description="spec.sample_input is empty",
            location="sample_input",
            evidence="No concrete sample input provided for testing",
            suggested_fix="Populate sample_input with a realistic dict matching "
                          "pipeline_input_schema",
        ))
    else:
        pis_names = {f.name for f in pis.fields}
        sample_names = set(spec.sample_input.keys())
        missing_in_sample = {f.name for f in pis.fields if f.required} - sample_names
        if missing_in_sample:
            findings.append(Finding(
                vector="pipeline_input_wirability",
                severity="critical",
                description=f"sample_input is missing required pipeline fields: {sorted(missing_in_sample)}",
                location="sample_input",
                evidence=f"pipeline_input_schema requires {sorted(pis_names)}, sample has {sorted(sample_names)}",
                suggested_fix="Add the missing keys to sample_input with concrete example values",
            ))

    if not spec.agents:
        return findings

    first_agent = spec.agents[0]
    contracts = {c.agent_id: c for c in spec.io_contracts}
    first_contract = contracts.get(first_agent.id)
    if not first_contract:
        return findings

    pis_names = {f.name for f in pis.fields}
    required_inputs = {f.name for f in first_contract.input_schema.fields if f.required}
    missing = required_inputs - pis_names
    if missing:
        findings.append(Finding(
            vector="pipeline_input_wirability",
            severity="critical",
            description=(
                f"First agent '{first_agent.id}' requires fields {sorted(missing)} that "
                f"are NOT in pipeline_input_schema"
            ),
            location=f"agents[0]={first_agent.id}.input_schema",
            evidence=f"pipeline_input_schema fields: {sorted(pis_names)}",
            suggested_fix=f"Either add {sorted(missing)} to pipeline_input_schema or "
                          f"remove from first agent's input_schema",
        ))

    return findings


# ── Vector 8: Tool Template Availability ──────────────────────────────


def _check_tool_template_availability(spec: AgentSpec, chroma: ChromaService) -> list[Finding]:
    """Every tools[].library_ref must resolve to a tool with a non-empty code_template.

    Builder can't write working code if there's no template to start from.
    """
    findings: list[Finding] = []
    for tool in spec.tools:
        try:
            schema = chroma.get_tool_by_id(tool.library_ref)
        except Exception as e:
            findings.append(Finding(
                vector="tool_template_availability",
                severity="critical",
                description=f"Tool '{tool.id}' references library_ref '{tool.library_ref}' which is not in the library",
                location=f"tools[id={tool.id}]",
                evidence=str(e),
                suggested_fix="Choose a library_ref from the available Tool Schema Library, "
                              "or remove this tool",
            ))
            continue
        if not schema:
            findings.append(Finding(
                vector="tool_template_availability",
                severity="critical",
                description=f"Tool '{tool.id}' references library_ref '{tool.library_ref}' which does not exist in the library",
                location=f"tools[id={tool.id}]",
                evidence=f"chroma.get_tool_by_id('{tool.library_ref}') returned None",
                suggested_fix="Use only tool IDs from the available Tool Schema Library, or remove this tool",
            ))
        elif not getattr(schema, "code_template", None):
            findings.append(Finding(
                vector="tool_template_availability",
                severity="warning",
                description=f"Tool '{tool.library_ref}' has no code_template — Builder will "
                            f"need to synthesize it from scratch",
                location=f"tools[id={tool.id}]",
                evidence=f"Library entry exists but code_template is empty",
                suggested_fix="Prefer tools with code_template in the library, or accept "
                              "higher build risk",
            ))
    return findings


# ── Vector 9: Tool Param Safety ───────────────────────────────────────


def _check_tool_param_safety(spec: AgentSpec, chroma: ChromaService) -> list[Finding]:
    """Inspect each tool's code_template for params that shadow pydantic/CrewAI reserved names.

    Caught examples: `schema`, `dict`, `json`, `model_*`. These shadow `BaseModel`
    attributes that CrewAI's tool wrapper relies on.
    """
    import re
    findings: list[Finding] = []
    for tool in spec.tools:
        try:
            schema = chroma.get_tool_by_id(tool.library_ref)
        except Exception:
            continue
        template = getattr(schema, "code_template", None) if schema else None
        if not template:
            continue
        # Naive scan for `def fn(params)`
        for match in re.finditer(r"def\s+(\w+)\s*\(([^)]*)\)", template):
            fn_name = match.group(1)
            params_str = match.group(2)
            for part in params_str.split(","):
                name = part.strip().split(":")[0].split("=")[0].strip()
                if name in {"self", "cls", "", "*args", "**kwargs"} or name.startswith("*"):
                    continue
                if name in PYDANTIC_RESERVED:
                    findings.append(Finding(
                        vector="tool_param_safety",
                        severity="warning",
                        description=(
                            f"Tool '{tool.library_ref}' function '{fn_name}' has param '{name}' "
                            f"that shadows a pydantic BaseModel attribute"
                        ),
                        location=f"tools[id={tool.id}]",
                        evidence=f"def {fn_name}({params_str})",
                        suggested_fix=f"Builder must rename '{name}' to e.g. '{name}_value' "
                                      f"when generating code, or use single 'data: dict' convention",
                    ))
    return findings
