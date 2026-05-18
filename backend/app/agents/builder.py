"""Builder agent — compiles validated specs into working code.

Model: claude-sonnet-4-6 (overridable per config)
Purpose: Template-aware code generation for CrewAI or LangGraph projects.

Multi-pass architecture:
  1. PLAN — LLM produces a BuildPlan (tool signatures, agent task templates,
     kickoff inputs) before writing code. Forces explicit cross-referencing.
  2. GENERATE — LLM writes code conforming to the plan.
  3. VALIDATE — run `_validation.run_all` (AST imports, tool param safety,
     entry-point wiring, tool coverage).
  4. REPAIR — if validation fails, send the LLM the errors and ask for a
     targeted patch. Up to `settings.max_builder_repair_iterations` retries.
"""

import json
import logging
from pathlib import Path

from app.agents import _validation
from app.config import settings
from app.models.code import CodeBundle
from app.models.spec import AgentSpec
from app.models.state import FrankensteinState
from app.models.tools import ToolSchema
from app.services.chroma_service import ChromaService
from app.services.llm_service import LLMService, extract_json

logger = logging.getLogger(__name__)

AGENT_NAME = "builder"

_SHARED_RULES = """\

## NON-NEGOTIABLE RULES (violating any of these = broken build)

1. EVERY tool referenced anywhere in `agents.py` MUST be defined as a function
   in `tools.py`. No imports of symbols that don't exist.

2. Tool functions follow a STRICT convention:
       def tool_name(data: dict) -> dict:
   - Exactly ONE parameter named `data`, typed `dict`.
   - NO default values on parameters (CrewAI's strict schema rejects them).
   - NO *args, **kwargs.
   - Return a dict.

3. NEVER use these names as parameters: `schema`, `dict`, `json`, `copy`,
   `parse_obj`, `validate`, `construct`, or anything starting with `model_`.
   They shadow `pydantic.BaseModel` attributes.

4. The pipeline MUST receive input via `crew.kickoff(inputs={...})` /
   `graph.invoke({...})`, keys matching spec.metadata.pipeline_input_schema.

5. `main.py` MUST load real input data — NEVER pass `{}`. Load
   `sample_data.json` if present, otherwise fall back to an inline
   `SPEC_SAMPLE_INPUT` constant matching spec.sample_input.

6. requirements.txt MUST list every pip dependency used.

7. All files MUST be syntactically valid.

8. README.md MUST cover prerequisites, env (OPENROUTER_API_KEY), install,
   run command, expected input/output shape.

## Output format
Return ONE JSON object: {"filename": "<full file content>", ...}.
Do NOT wrap content in code fences. Do NOT add commentary outside the JSON.
"""

CREWAI_SYSTEM = """\
You are the Builder generating a CrewAI project from an AgentSpec.

## Required files

### main.py (template — adapt SPEC_SAMPLE_INPUT to actual sample)
```python
import json, os
from pathlib import Path
from dotenv import load_dotenv
from orchestration import create_crew

SPEC_SAMPLE_INPUT = {}  # fill from spec.sample_input

def load_inputs():
    p = Path(__file__).parent / "sample_data.json"
    if p.exists():
        return json.loads(p.read_text())
    return SPEC_SAMPLE_INPUT

def main():
    load_dotenv()
    if os.getenv("OPENROUTER_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = os.environ["OPENROUTER_API_KEY"]
        os.environ.setdefault("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
        os.environ.setdefault("OPENAI_MODEL_NAME", "openai/gpt-4o-mini")

    inputs = load_inputs()
    crew = create_crew()
    result = crew.kickoff(inputs=inputs)
    print(json.dumps({"result": str(result.raw if hasattr(result, "raw") else result)}, indent=2))

if __name__ == "__main__":
    main()
```

### agents.py
Import every tool function explicitly. Build the Agent dict per spec.

### tools.py
Every tool referenced anywhere MUST appear here:
```python
from crewai.tools import tool

@tool("Display Name")
def tool_function(data: dict) -> dict:
    \"\"\"Adapt the code_template — single dict-param convention.\"\"\"
    value = data.get("field_x")
    ...
    return {"output_key": result}
```

### orchestration.py
Task descriptions MUST contain `{field_name}` template variables matching
keys in kickoff_inputs. Example: `description="Analyze {application_data} for fraud risk..."`.

### requirements.txt
crewai>=0.70.0, python-dotenv>=1.0.0, streamlit>=1.30.0, plus tool deps.

### app.py (Streamlit Web UI)
```python
import json, os, streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from orchestration import create_crew

load_dotenv()
if os.getenv("OPENROUTER_API_KEY") and not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.environ["OPENROUTER_API_KEY"]
    os.environ.setdefault("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    os.environ.setdefault("OPENAI_MODEL_NAME", "openai/gpt-4o-mini")

st.set_page_config(page_title=spec.metadata.name, layout="wide")
st.title(spec.metadata.name)
st.caption(spec.metadata.description)

# Build input form from pipeline_input_schema fields
with st.form("input_form"):
    inputs = {}
    # One text_area per pipeline_input_schema field
    for field_name, field_info in spec.metadata.pipeline_input_schema.items():
        inputs[field_name] = st.text_area(field_name, height=100)
    submitted = st.form_submit_button("Run Pipeline")

if submitted:
    with st.spinner("Running agent pipeline..."):
        crew = create_crew()
        result = crew.kickoff(inputs=inputs)
    st.subheader("Results")
    st.json(json.loads(json.dumps({"result": str(result.raw if hasattr(result, "raw") else result)})))
```
Adapt the template above: use actual spec field names, title, description.
For LangGraph projects, import `create_graph` from orchestration and call `graph.invoke(inputs)`.

### .env.example
OPENROUTER_API_KEY=...

### sample_data.json
A JSON dict matching spec.sample_input exactly.
""" + _SHARED_RULES


LANGGRAPH_SYSTEM = """\
You are the Builder generating a LangGraph project from an AgentSpec.

## Required files

### main.py
Same env-injection + sample-loading pattern as the CrewAI builder. Call
`graph.invoke(load_inputs())`.

### state.py
TypedDict union of all io_contract fields + pipeline_input_schema fields.

### agents.py
Each agent: `def agent_id(state: dict) -> dict: ...`.

### tools.py
Same `def fn(data: dict) -> dict` convention.

### orchestration.py
StateGraph wiring per spec.execution_flow.

### requirements.txt
langgraph>=0.2.0, langchain-core>=0.3.0, langchain-openai>=0.2.0, python-dotenv>=1.0.0, streamlit>=1.30.0, tool deps.

### app.py (Streamlit Web UI)
Same pattern as CrewAI app.py but import `create_graph` from orchestration
and call `graph.invoke(inputs)`. Display results as JSON.

### .env.example, sample_data.json
Same as CrewAI.
""" + _SHARED_RULES


PLAN_SYSTEM = """\
You are planning a code build. Before writing any code, produce a BuildPlan
that pins down: tool signatures, agent task templates, and how data enters
the pipeline. This plan will be enforced verbatim in the generation pass.

Return ONE JSON object (no commentary):
{
  "files": [{"name": "main.py", "purpose": "...", "exports": ["main"]}, ...],
  "tool_functions": [
    {
      "name": "<snake_case>",
      "description": "<one line>",
      "input_subkeys": ["<key in data dict>", ...],
      "output_subkeys": ["<key in returned dict>", ...]
    }
  ],
  "agent_task_map": [
    {
      "agent_id": "<from spec>",
      "task_description_template": "Use {field_a} and {field_b} to ...",
      "expected_output": "<from spec io_contract>",
      "tools_used": ["<tool function name>", ...]
    }
  ],
  "kickoff_inputs": {"<field>": "<source: pipeline_input_schema or upstream agent>"}
}

HARD RULES:
- Every tool referenced in tools_used MUST appear in tool_functions.
- All tool_functions take a single `data: dict` parameter.
- Every key in kickoff_inputs MUST be a field of spec.metadata.pipeline_input_schema.
- Every {placeholder} in task_description_template MUST be a key in kickoff_inputs
  OR a known upstream-agent output field.
"""


REPAIR_SYSTEM = """\
You are repairing a failed code build. You receive:
  - the current files
  - validator errors (each with stable `code`, `message`, `fix` hint)
  - the original spec + build plan

Fix ONLY the listed errors. Do not refactor unrelated code.
Re-emit the COMPLETE file set as JSON: {"filename": "<full content>", ...}.
Every file in the original set must appear in your response.

Common patterns:
- UNRESOLVED_SYMBOL → add the missing function. Use `def fn(data: dict) -> dict`.
- PARAM_SHADOWS_PYDANTIC → rename or refactor to single-dict convention.
- TOOL_WRONG_ARITY / TOOL_HAS_DEFAULTS → convert to `def fn(data: dict) -> dict`,
  read former params from `data` subkeys.
- KICKOFF_EMPTY_INPUTS → load sample_data.json / SPEC_SAMPLE_INPUT, pass to kickoff.
- ENTRY_POINT_MISSING_FIELD → ensure kickoff dict has every pipeline_input_schema field.
"""


def builder_agent(
    state: FrankensteinState,
    *,
    llm: LLMService | None = None,
    chroma: ChromaService | None = None,
) -> dict:
    """Plan → generate → validate → repair loop."""
    from app.services.chroma_service import ChromaService as _CS
    from app.services.llm_service import LLMService as _LS

    if llm is None:
        llm = _LS()
    if chroma is None:
        chroma = _CS()

    spec: AgentSpec = state["spec"]
    framework = spec.metadata.framework_target
    session_id = state.get("session_id", "?")
    logger.info("[%s] Builder: START — compiling '%s' → %s", session_id, spec.metadata.name, framework)

    tool_templates = _get_tool_templates(chroma, spec)
    logger.info("[%s] Builder: loaded %d tool templates: %s", session_id, len(tool_templates), list(tool_templates.keys()))

    failure_feedback = None
    if state.get("failure_traces"):
        failure_feedback = [ft.model_dump() for ft in state["failure_traces"]]
        logger.info("[%s] Builder: %d failure traces from previous attempt", session_id, len(failure_feedback))

    # On rebuild, use previous code as context for targeted repair instead of
    # regenerating from scratch (which hits the same validation errors again)
    previous_code = state.get("generated_code")
    if previous_code and failure_feedback and previous_code.validation_passed:
        logger.info("[%s] Builder: previous build passed validation — doing targeted repair from test failures", session_id)
        plan = _plan_build(llm, spec, tool_templates, failure_feedback)
        files = dict(previous_code.files)
        # Feed failure traces into repair pass
        repair_errors = [
            {"code": "TEST_FAILURE", "message": ft.get("raw_error", "") or ft.get("root_cause_analysis", ""), "fix": ft.get("suggested_fix", "")}
            for ft in failure_feedback
        ]
        files = _repair_code(llm, files, repair_errors, spec, plan)
    else:
        logger.info("[%s] Builder: PHASE 1 — planning build...", session_id)
        plan = _plan_build(llm, spec, tool_templates, failure_feedback)
        logger.info("[%s] Builder: plan produced — %d tools, %d agents",
                    session_id,
                    len(plan.get("tool_functions", [])),
                    len(plan.get("agent_task_map", [])))

        logger.info("[%s] Builder: PHASE 2 — generating code...", session_id)
        files = _generate_code(llm, spec, tool_templates, plan, failure_feedback)
    logger.info("[%s] Builder: generated %d files: %s", session_id, len(files), list(files.keys()))
    _inject_sample_data(files, spec)

    logger.info("[%s] Builder: PHASE 3 — validation & repair loop...", session_id)
    repair_history: list[dict] = list(state.get("repair_history", []))
    max_repairs = settings.max_builder_repair_iterations
    errors: list[dict] = []

    for attempt in range(max_repairs + 1):
        logger.info("[%s] Builder: validation attempt %d/%d", session_id, attempt, max_repairs)
        errors = _validation.run_all(files, spec=spec, framework=framework)
        critical = [e for e in errors if e.get("severity") == "error"]
        warnings = [e for e in errors if e.get("severity") == "warning"]
        logger.info("[%s] Builder: validation result — %d critical, %d warnings", session_id, len(critical), len(warnings))
        if not critical:
            logger.info("[%s] Builder: validation CLEAN on attempt %d", session_id, attempt)
            break

        logger.warning("[%s] Builder: %d critical errors on attempt %d: %s",
                       session_id, len(critical), attempt,
                       [e["code"] for e in critical])

        if attempt == max_repairs:
            logger.error("[%s] Builder: exhausted repair budget, shipping with errors", session_id)
            break

        repair_history.append({"attempt": attempt, "errors": critical})
        repair_context = []
        for err in critical:
            patterns = chroma.find_similar_repair_patterns(
                err.get("message", "") or err.get("code", ""), n_results=2
            )
            if patterns:
                repair_context.extend(patterns)
        logger.info("[%s] Builder: REPAIR attempt %d — %d RAG patterns found", session_id, attempt, len(repair_context))
        files = _repair_code(llm, files, critical, spec, plan, repair_context)
        logger.info("[%s] Builder: repair produced %d files: %s", session_id, len(files), list(files.keys()))
        _inject_sample_data(files, spec)

    deps = _collect_dependencies(spec, tool_templates)
    passed = not any(e.get("severity") == "error" for e in errors)
    error_strings = [
        f"{e.get('code', 'ERR')}: {e.get('file', '?')}: {e.get('message', '')}"
        for e in errors
    ]

    logger.info("[%s] Builder: PHASE 4 — persisting to disk...", session_id)
    if state.get("session_id"):
        _persist_to_disk(state["session_id"], files)
        logger.info("[%s] Builder: wrote %d files to generated_agents/%s", session_id, len(files), session_id)

    logger.info("[%s] Builder: DONE — passed=%s, %d errors, %d files, framework=%s",
                session_id, passed, len(error_strings), len(files), framework)
    return {
        "generated_code": CodeBundle(
            files=files,
            framework=framework,
            dependencies=deps,
            validation_passed=passed,
            validation_errors=error_strings,
        ),
        "build_attempts": state.get("build_attempts", 0) + 1,
        "repair_history": repair_history,
    }


def _plan_build(llm, spec, tool_templates, failure_feedback):
    user_parts = [
        "## AgentSpec\n\n" + spec.model_dump_json(indent=2),
        "\n\n## Available Tool Templates\n\n"
        + json.dumps(
            {k: {"description": v.get("description"), "accepts": v.get("accepts"),
                 "outputs": v.get("outputs")}
             for k, v in tool_templates.items()},
            indent=2,
        ),
    ]
    if failure_feedback:
        user_parts.append("\n\n## Previous Failures\n\n" + json.dumps(failure_feedback, indent=2))

    raw = llm.call(
        agent_name=AGENT_NAME,
        system_prompt=PLAN_SYSTEM,
        user_prompt="\n".join(user_parts),
        json_mode=True,
        temperature=0.1,
    )
    try:
        return json.loads(extract_json(raw))
    except json.JSONDecodeError as e:
        logger.warning("Builder: plan LLM returned invalid JSON, using empty plan: %s", e)
        return {"files": [], "tool_functions": [], "agent_task_map": [], "kickoff_inputs": {}}


def _generate_code(llm, spec, tool_templates, plan, failure_feedback):
    system = CREWAI_SYSTEM if spec.metadata.framework_target == "crewai" else LANGGRAPH_SYSTEM

    if failure_feedback:
        system += (
            "\n\n## PREVIOUS BUILD FAILED — FIX THESE\n\n"
            + json.dumps(failure_feedback, indent=2)
        )

    user_parts = [
        "## AgentSpec\n\n" + spec.model_dump_json(indent=2),
        "\n\n## Build Plan (code MUST conform to this exactly)\n\n"
        + json.dumps(plan, indent=2),
        "\n\n## Tool Code Templates (adapt — never rewrite logic)\n\n"
        + json.dumps(tool_templates, indent=2),
        "\n\n## Sample Input\n\n" + json.dumps(spec.sample_input, indent=2, default=str),
    ]

    response = llm.call(
        agent_name=AGENT_NAME,
        system_prompt=system,
        user_prompt="\n".join(user_parts),
        json_mode=True,
        temperature=0.1,
    )
    try:
        data = json.loads(extract_json(response))
    except json.JSONDecodeError as e:
        logger.error("Builder: invalid JSON from generation pass: %s", e)
        raise ValueError(f"Builder generation pass returned invalid JSON: {e}") from e

    if not isinstance(data, dict):
        raise ValueError("Builder did not return a filename→code mapping")

    return {k: v for k, v in data.items() if isinstance(v, str)}


def _repair_code(llm, files, errors, spec, plan, repair_context=None):
    user_parts = [
        "## Current Files\n\n" + json.dumps(files, indent=2),
        "\n\n## Validator Errors (fix every one)\n\n" + json.dumps(errors, indent=2),
        "\n\n## Spec\n\n" + spec.model_dump_json(indent=2),
        "\n\n## Plan\n\n" + json.dumps(plan, indent=2),
    ]
    if repair_context:
        user_parts.append(
            "\n\n## Past Repair Patterns (similar errors fixed before)\n\n"
            + json.dumps(repair_context, indent=2)
        )
    response = llm.call(
        agent_name=AGENT_NAME,
        system_prompt=REPAIR_SYSTEM,
        user_prompt="\n".join(user_parts),
        json_mode=True,
        temperature=0.05,
    )
    try:
        data = json.loads(extract_json(response))
    except json.JSONDecodeError as e:
        logger.error("Builder: repair LLM returned invalid JSON: %s", e)
        return files

    if not isinstance(data, dict):
        return files

    merged = dict(files)
    for k, v in data.items():
        if isinstance(v, str):
            merged[k] = v
    return merged


def _inject_sample_data(files, spec):
    if spec.sample_input:
        files["sample_data.json"] = json.dumps(spec.sample_input, indent=2, default=str)


def _get_tool_templates(chroma, spec):
    templates = {}
    for tool_ref in spec.tools:
        tool = chroma.get_tool_by_id(tool_ref.library_ref)
        if tool:
            templates[tool_ref.library_ref] = {
                "id": tool.id,
                "name": tool.name,
                "description": tool.description,
                "code_template": tool.code_template,
                "dependencies": tool.dependencies,
                "accepts": tool.accepts,
                "outputs": tool.outputs,
            }
        else:
            logger.warning("Builder: tool '%s' not found in library", tool_ref.library_ref)
    return templates


def _collect_dependencies(spec, tool_templates):
    deps = set()
    if spec.metadata.framework_target == "crewai":
        deps.update(["crewai", "python-dotenv", "streamlit"])
    else:
        deps.update(["langgraph", "langchain-core", "langchain-openai", "python-dotenv", "streamlit"])
    for tmpl in tool_templates.values():
        for d in tmpl.get("dependencies", []):
            deps.add(d)
    return sorted(deps)


def _persist_to_disk(session_id, files):
    session_dir = Path(settings.generated_agents_dir) / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    for fname, content in files.items():
        fpath = session_dir / fname
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text(content, encoding="utf-8")
