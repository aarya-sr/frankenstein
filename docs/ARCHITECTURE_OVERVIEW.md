# Frankenstein — Full Architecture & What We Built

## The Concept

**Meta-agentic system**: you describe an agent in plain English, Frankenstein asks clarifying questions, designs the architecture, stress-tests it, writes the code, runs it in Docker, fixes what breaks, and learns from every build. The human validates twice (requirements + blueprint) but never writes code.

**Core insight**: building agents requires domain knowledge (what to do) AND engineering knowledge (how to build). Frankenstein splits that — human provides domain, Frankenstein provides engineering.

---

## Architecture: Six-Agent LangGraph Pipeline

```
Human prompt
    │
    ▼
[1. ELICITOR] (gpt-4o-mini)
    │  Structured Q&A across 5 categories
    │  Gap analysis loop (up to 3 rounds)
    │  Scores each dimension 0-1, loops until ≥0.85
    ▼
RequirementsDoc → Human Checkpoint 1 ("Is this what you meant?")
    │
    ▼
[2. ARCHITECT] (claude-sonnet-4-5)
    │  RAG: past specs, tools, anti-patterns from Chroma
    │  8-step process: decompose → match tools → group agents
    │  → design flow → memory → error handling → I/O contracts
    ▼
AgentSpec
    │
    ▼
[3. CRITIC] (gpt-4o) ←── different model family on purpose
    │  6 attack vectors (programmatic + LLM semantic)
    │  Circular deps, format compat, dead-ends, resource conflicts
    │  ↕ loops back to Architect until no criticals (max 3 iterations)
    ▼
Validated Spec + CritiqueReport → Human Checkpoint 2 ("Approve blueprint?")
    │
    ▼
[4. BUILDER] (claude-sonnet-4-5)
    │  Plan → Generate → Validate → Repair loop (max 3 repairs)
    │  Template-driven: tool schemas have pre-validated code_templates
    │  Outputs: agents.py, tools.py, orchestration.py, main.py,
    │           sample_data.json, requirements.txt, README.md, app.py
    ▼
CodeBundle
    │
    ▼
[5. TESTER] (gpt-4o-mini)
    │  Static validation (AST, imports, tool signatures)
    │  Live execution in Docker sandbox with real LLM calls
    │  Rule-based failure classification → LLM fallback
    │  root_cause_level: "code" → Builder, "spec" → Architect
    ▼
TestReport + FailureTraces
    │
    ▼
[6. LEARNER] (gpt-4o-mini)
    │  Extracts success/failure/anti patterns
    │  Stores BuildOutcome + patterns in Chroma
    │  Updates tool compatibility from real results
    ▼
END — downloadable agent + Streamlit app preview
```

---

## Key Technical Decisions

### Model-per-Agent Strategy (OpenRouter)

Each agent uses a different model optimized for its task:

| Agent | Model | Why |
|---|---|---|
| Elicitor | gpt-4o-mini | Fast, cheap, good at structured Q&A |
| Architect | claude-sonnet-4-5 | Best at complex structured generation |
| Critic | gpt-4o | Different family from Architect — cross-model review catches blind spots |
| Builder | claude-sonnet-4-5 | Best at code generation with constraints |
| Tester | gpt-4o-mini | Fast analysis, rule-based does the heavy lifting |
| Learner | gpt-4o-mini | Pattern extraction doesn't need frontier model |

### Chroma Vector Memory (5 Collections)

| Collection | What | Used By |
|---|---|---|
| `tool_schemas` | 14 pre-seeded validated tool definitions | Architect (tool matching) |
| `spec_patterns` | Past validated specs + outcomes | Architect (structural reference) |
| `anti_patterns` | Patterns that caused failures | Architect (avoidance) |
| `domain_insights` | Domain-specific learnings | Elicitor (question refinement) |
| `builder_repair_patterns` | Error→fix pairs from past repairs | Builder (RAG-guided repair) |

**The system literally gets smarter with every build.** The Learner stores what worked, what failed, and what to avoid. Future builds query this memory.

### Human-in-the-Loop via LangGraph `interrupt()`

Two checkpoints use LangGraph's native interrupt mechanism — the graph pauses, WebSocket pushes the payload to the frontend, human reviews, and `Command(resume=...)` continues the graph. No polling, no hacks.

### Feedback Loops (Self-Healing)

- **Architect ↔ Critic**: spec revisions until no critical findings (max 3 loops)
- **Builder → Validate → Repair**: AST/import/signature validation with up to 3 LLM repair cycles
- **Tester → Builder OR Architect**: failure traces classify root cause level — code bugs go back to Builder, spec bugs go back to Architect

---

## Deep Dives

### Elicitor Agent

**Implementation:** LangGraph subgraph with a loop.

```
analyze_prompt → identify_gaps → generate_questions → receive_answers → update_requirements → check_completeness
     ↑                                                                                              │
     └──────────────────────── (if incomplete) ◄────────────────────────────────────────────────────┘
```

- Runs gap analysis against 5 categories: Input/Output, Process, Data, Edge Cases, Quality Bar
- Each category has a confidence score (0-1), loops until all ≥ 0.85
- Maximum 3 rounds of questions — flags remaining gaps as assumptions
- Output: structured `RequirementsDoc` with typed fields

```python
class RequirementsDoc(BaseModel):
    domain: str
    inputs: list[DataSpec]           # name, format, description, example
    outputs: list[DataSpec]
    process_steps: list[ProcessStep] # step_number, description, rules, depends_on
    edge_cases: list[EdgeCase]
    quality_criteria: list[QualityCriterion]
    constraints: list[str]
```

### Architect Agent

**8-step process:**

1. **RAG Query** — query Chroma for similar past specs, tools, anti-patterns
2. **Task Decomposition** — break requirements into discrete computational tasks, tag each with capability type (text_extraction, calculation, reasoning, generation, api_call, data_processing)
3. **Tool Selection** — match each task to a tool from the library. Selection by: format compatibility (accepts/outputs), limitation check, incompatibility avoidance
4. **Agent Grouping** — related tasks → same agent, independent chains → separate agents
5. **Execution Flow** — analyze dependencies → pick pattern (sequential, parallel, hierarchical, graph). Graph patterns → LangGraph, role delegation → CrewAI
6. **Memory Design** — shared keys, strategy, persistence
7. **I/O Contracts** — per-agent input/output schemas with typed fields. Every required output of agent A must appear in input_schema of downstream agent B
8. **Pipeline Input/Output Contract** — how data enters and leaves the entire pipeline. Wired to `crew.kickoff(inputs=...)` or `graph.invoke(...)`

### Critic Agent

**6 attack vectors (5 programmatic + 1 LLM semantic):**

| Vector | What It Checks | How |
|---|---|---|
| Circular Dependencies | Cycles in execution graph | Topological sort |
| Format Compatibility | Agent A output → Agent B input format match | Walk every edge, compare schemas |
| Dependency Completeness | Every agent receives all required fields | Trace required fields to upstream producers |
| Dead-End Analysis | Agents that can fail without being caught | Check on_failure config, flag skip-on-critical-path |
| Resource Conflicts | Parallel agents writing same shared memory keys | Check shared_keys against parallel paths |
| Tool + Semantic Review | Tool capability match, coherence, reasoning strategy fit | LLM-powered (gpt-4o) |

Output: `CritiqueReport` with findings scored as critical/warning/suggestion. Criticals force Architect revision.

### Builder Agent

**Multi-pass architecture:**

1. **PLAN** — LLM produces a BuildPlan (tool signatures, agent task templates, kickoff inputs) before writing code. Forces explicit cross-referencing.
2. **GENERATE** — code conforming to the plan, framework-specific (CrewAI or LangGraph)
3. **VALIDATE** — `_validation.run_all()` with 8+ AST-level checks
4. **REPAIR** — if validation fails, send errors + RAG-retrieved past repair patterns to LLM for targeted fix. Up to 3 repair cycles.

**On rebuild from test failures:** if previous code passed validation, does targeted repair from failure traces instead of regenerating from scratch.

**Generated project structure:**
```
generated_agent/
├── main.py              # entry point with env injection
├── agents.py            # agent definitions (roles, goals, backstories)
├── tools.py             # tool implementations (strict def fn(data: dict) -> dict)
├── orchestration.py     # CrewAI crew or LangGraph graph definition
├── app.py               # Streamlit web UI
├── sample_data.json     # concrete test data matching pipeline_input_schema
├── requirements.txt     # Python dependencies
├── .env.example         # OPENROUTER_API_KEY=...
└── README.md            # prerequisites, setup, run command, I/O shape
```

### Validation System (`_validation.py`)

Shared between Builder (self-repair) and Tester (sanity checks):

| Code | What It Catches |
|---|---|
| `SYNTAX_ERROR` | File won't parse |
| `UNRESOLVED_SYMBOL` | Imports that don't exist |
| `PARAM_SHADOWS_PYDANTIC` | Params named `schema`, `dict`, `json` etc. that break CrewAI |
| `TOOL_WRONG_ARITY` | Tool function doesn't follow `def fn(data: dict) -> dict` |
| `TOOL_HAS_DEFAULTS` | Default params break OpenAI strict schema |
| `KICKOFF_EMPTY_INPUTS` | `crew.kickoff(inputs={})` guaranteed to fail |
| `ENTRY_POINT_MISSING_FIELD` | pipeline_input_schema fields not wired |
| `TOOL_NOT_DEFINED` | Referenced in agents.py but never implemented in tools.py |

### Tester Agent

**Execution pipeline:**
1. Generate test cases from spec (LLM, for the report)
2. Static validation via `_validation.run_all()` (same checks as Builder)
3. Live execution in Docker sandbox with real LLM calls via OpenRouter
4. Output validation: parse stdout JSON, flag known failure signatures
5. Rule-based failure classification (regex) for common patterns; LLM handles the rest

**Failure signatures detected:**
- `EMPTY_INPUTS` — kickoff with no data
- `MISSING_API_KEY` — env injection issue
- `STRICT_SCHEMA` — tool function breaks OpenAI strict schema
- `IMPORT_ERROR` — symbol not generated
- `KEY_ERROR` — field not in input dict

**Root cause routing:** `root_cause_level: "code"` → loops to Builder, `"spec"` → loops to Architect

### Learner Agent

**Stores after every build:**
- `BuildOutcome` with requirements hash, spec snapshot, framework, tools used, test results, iterations needed
- `success_patterns` — what worked well
- `failure_patterns` — what went wrong this build
- `anti_patterns` — generalized patterns to avoid
- `lessons_learned` — domain-specific takeaways
- `repair_patterns` — error→fix pairs from Builder repair history

Updates tool `compatible_with`/`incompatible_with` from real build results.

---

## 14 Pre-Seeded Tool Schemas

Each with validated code_template, accepts/outputs formats, limitations, and compatibility info:

| Tool | Category |
|---|---|
| `pdf_parser_pymupdf` | Document extraction |
| `ocr_tesseract` | Document extraction |
| `csv_parser` | Data processing |
| `json_transformer` | Data processing |
| `file_reader` | Data processing |
| `financial_calculator` | Calculation |
| `statistical_analyzer` | Analysis |
| `scoring_engine` | Analysis |
| `rule_engine` | Reasoning |
| `llm_reasoner` | Reasoning |
| `report_generator` | Generation |
| `data_visualizer` | Generation |
| `web_search` | API call |
| `code_executor` | Execution |

---

## Frontend Architecture

### Landing Page (React Three Fiber + Custom GLSL)

- **LaboratoryVoid**: custom GLSL shader background with biological noise patterns
- **OrganismFragments**: 6 3D shapes representing agents (sphere, box, octahedron, cylinder, dodecahedron, icosahedron) with custom vertex displacement shaders, per-fragment particle trails (ring buffer), and assembly animation sequence
- **EnergyConnections**: animated THREE.Line objects connecting agents with traveling pulse dots (additive blending)
- **AssemblyAnimation**: fragments pull → stitch → lightning → heartbeat sequence driven by Zustand state
- **Bloom post-processing** via `@react-three/postprocessing`
- **TypewriterHeadline**: animated text reveal

### Chat Interface

- Real-time dual WebSocket (chat + status channels)
- **QuestionGroupCard**: renders elicitor questions with per-category grouping, AI-assist button
- **RequirementsCard**: human checkpoint 1 — approve/edit requirements
- **SpecReviewCard**: human checkpoint 2 — approve/feedback on blueprint with critique findings
- **TypingIndicator**: 18 shuffled cycling facts about Frankenstein's architecture while pipeline runs
- **PipelineSidebar**: live stage tracker with active/done/pending states
- **ActivityPill**: real-time sub-step updates ("Querying past blueprints...", "Running adversarial review...")
- **CodingScreen**: animated terminal showing build progress
- **CompletionCard**: download button + build stats (time, files, tests, agents)
- **PipelineGraph**: visual node graph of the pipeline stages
- **ErrorCard**: recoverable/non-recoverable error display

### Preview System

- **CodeViewer**: syntax-highlighted file explorer for generated code
- **ExecutionPanel**: Docker streaming execution with agent trace log
- **StreamlitPreview**: embedded iframe for the generated Streamlit app (live preview)
- **SplitPane**: resizable panels for code + execution side-by-side

---

## Real-Time Streaming Architecture

### Queue-Based Node Streaming

Post-approval pipeline (`builder→tester→learner`) runs `graph.stream()` in a thread. A queue bridge forwards node events to the async WebSocket consumer in real-time:

```python
# Sync thread (graph.stream)
for chunk in compiled_graph.stream(Command(resume=...), config, stream_mode="updates"):
    for node_name in chunk:
        asyncio.run_coroutine_threadsafe(queue.put(("node", node_name)), loop)

# Async consumer (WebSocket)
while True:
    event_type, node_name = await event_queue.get()
    # Send stage update, activity messages, mark previous node done
```

Supports cycling — Builder appearing multiple times in repair loops gets retry-specific activity messages.

### WebSocket Channels

| Path | Purpose |
|---|---|
| `/ws/chat/{session_id}` | Bidirectional: user input, system messages, questions, checkpoints, errors, completion |
| `/ws/status/{session_id}` | Server→client: stage updates, activity feed |
| `/ws/preview/{session_id}` | Server→client: Docker execution trace lines, run start/complete/error |

---

## Problems Solved

### 1. Empty Elicitor Interrupt (Dead State Bug)
**Problem**: Elicitor round 2 generated 0 questions (all gaps scored ≥0.85) but still called `interrupt()` with empty payload. Frontend got empty question group → `isWorking=false` → no loader → dead state.
**Fix**: Added early return with `elicitor_all_complete=True` when no questions generated, skipping the interrupt entirely.

### 2. WebSocket Disconnection at Builder Stage
**Problem**: Builder writes files to `generated_agents/`, uvicorn's `--reload` file watcher detects changes, restarts server, kills all WebSocket connections mid-pipeline.
**Fix**: `--reload-exclude 'generated_agents/*' --reload-exclude 'chroma_data/*' --reload-exclude '*.sqlite3'`

### 3. Vite HMR WebSocket Collision
**Problem**: Broad `/ws` proxy in vite.config.ts caught Vite's own HMR WebSocket → "send before connect" errors.
**Fix**: Narrowed proxy to specific paths: `/ws/chat`, `/ws/status`, `/ws/preview`

### 4. Port Conflicts
**Problem**: Default ports (8000, 5173) collided with other services.
**Fix**: Backend → 7749, Frontend → 7751, Chroma → 7753

### 5. Landing Page Restoration
**Problem**: Commit `8173db5` reduced App.tsx to just HeroSection, losing the full landing page with all sections.
**Fix**: Restored from commit `0171066` with all sections intact.

### 6. Comprehensive Verbose Logging
**Problem**: Pipeline failures were invisible — couldn't trace what happened between stages.
**Fix**: Added session-tagged DEBUG logging across all 6 agents, LLM service (call timing + token usage), graph routing decisions, WebSocket lifecycle, and post-approval pipeline streaming.

### 7. Real-Time Streaming for Post-Approval Pipeline
**Problem**: Original implementation collected all stream events after completion, so no real-time updates during the longest part of the pipeline.
**Fix**: Queue-based bridge so `graph.stream()` running in a thread pushes node events to async consumer for immediate WebSocket dispatch. Supports builder retry cycling.

### 8. Builder Targeted Repair from Test Failures
**Problem**: Rebuilding after test failures regenerated everything from scratch, hitting the same validation errors.
**Fix**: When previous code passed validation, Builder does targeted repair from failure traces instead of full regeneration.

### 9. Streamlit App Generation + Live Preview
**Problem**: Generated agents were CLI-only — no visual interface.
**Fix**: Builder generates `app.py` (Streamlit web UI) with input forms from pipeline_input_schema. `StreamlitService` launches it in Docker. Frontend embeds it via `StreamlitPreview` iframe.

---

## Stack Summary

| Layer | Technology |
|---|---|
| Pipeline Orchestration | LangGraph StateGraph + SqliteSaver checkpointer |
| Backend | FastAPI + Uvicorn |
| Frontend | React + Vite + Tailwind CSS + Framer Motion |
| 3D Graphics | React Three Fiber + drei + postprocessing + custom GLSL shaders |
| LLM Routing | OpenRouter (model-per-agent strategy) |
| Vector Database | ChromaDB (5 collections, persistent) |
| Code Execution | Docker (pre-built base image + streaming) |
| Frontend State | Zustand |
| Communication | Native FastAPI WebSockets (3 channels: chat, status, preview) |
| Generated Output | CrewAI or LangGraph project + Streamlit app |

---

## Pipeline State Object

Single state flows through entire graph — every node reads from it, does work, writes back:

```python
class FrankensteinState(TypedDict):
    # Elicitor
    raw_prompt: str
    session_id: str
    elicitor_questions: list[dict]
    human_answers: list[dict]
    requirements: RequirementsDoc
    requirements_approved: bool

    # Architect + Critic
    tool_library_matches: list[ToolSchema]
    past_spec_matches: list[dict]
    spec: AgentSpec
    architect_reasoning: str
    critique: CritiqueReport
    spec_iteration: int
    spec_approved: bool

    # Builder + Tester
    generated_code: CodeBundle
    test_cases: list[TestCase]
    test_results: TestReport
    failure_traces: list[FailureTrace]
    build_iteration: int
    build_attempts: int
    repair_history: list[dict]

    # Learner
    build_outcome: BuildOutcome
```

---

## Demo Targets

- **PS-08**: Loan Underwriting Co-Pilot — multi-agent pipeline for document extraction, risk scoring, compliance checking, report generation
- **PS-06**: Supplier Reliability Scoring Agent — data aggregation, statistical analysis, scoring, ranking

Both run end-to-end: prompt → elicitor questions → requirements → architect design → critic review → builder code → tester execution → learner storage → downloadable project + Streamlit app.
