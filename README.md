# Frankenstein

**Meta-agentic system that builds AI agent pipelines from natural language.**

One conversation. Working agents. Tested and ready.

> **Team:** Aarya Srivastava, Ved Pawar, Bhawana
> **Problem Statement:** PS-03 - Meta-Agentic Systems

---

## Table of Contents

- [The Problem](#the-problem)
- [What Frankenstein Does](#what-frankenstein-does)
- [How It Works](#how-it-works)
- [Architecture](#architecture)
  - [Pipeline Overview](#pipeline-overview)
  - [The Six Agents](#the-six-agents)
  - [Feedback Loops](#feedback-loops)
  - [Pipeline State](#pipeline-state)
  - [Graph Definition](#graph-definition)
  - [Routing Logic](#routing-logic)
- [Agent Deep Dive](#agent-deep-dive)
  - [1. Elicitor Agent](#1-elicitor-agent)
  - [2. Architect Agent](#2-architect-agent)
  - [3. Critic Agent](#3-critic-agent)
  - [4. Builder Agent](#4-builder-agent)
  - [5. Tester Agent](#5-tester-agent)
  - [6. Learner Agent](#6-learner-agent)
- [Data Models](#data-models)
- [Tool Schema Library](#tool-schema-library)
- [Chroma Memory Architecture](#chroma-memory-architecture)
- [Cross-Model Adversarial Review](#cross-model-adversarial-review)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Running the Application](#running-the-application)
- [Demo: Loan Underwriting Co-Pilot](#demo-loan-underwriting-co-pilot)
- [Configuration](#configuration)
- [What Frankenstein Does Not Do](#what-frankenstein-does-not-do)
- [Documentation](#documentation)

---

## The Problem

AI agents can automate loan underwriting, supplier scoring, compliance monitoring, report generation, and hundreds of other workflows. The technology exists. **The bottleneck is people.**

Building an AI agent is not a coding problem - it is a **decision problem**. For every natural-language requirement, an engineer must make 50+ interdependent technical decisions: how many sub-agents, what roles each plays, which tools to bind, what reasoning strategy to use, how to structure memory, how to handle failures, what architecture pattern fits the workflow.

- A loan officer wants an AI assistant to review applications - needs an engineering team for weeks
- A procurement manager wants supplier scoring - same weeks-long custom project
- Every new agent is a custom engineering effort: too slow, too expensive, most never get built

**The gap:** Domain experts know WHAT to build. Engineers know HOW to build. They're rarely the same person.

---

## What Frankenstein Does

Frankenstein lets the domain expert build the agent themselves - no engineering team needed.

You open a chat. You describe what you need. Frankenstein asks sharp questions to extract precise requirements. Then it does the engineering: picks the right tools, designs how agents work together, checks its own design for problems, writes the code, runs it, and fixes what breaks.

**Input:** One fuzzy prompt from a domain expert
**Output:** Tested, deployable multi-agent system (CrewAI or LangGraph)

What comes out is a real, working multi-agent system - not a prototype. It runs on the same frameworks professional engineers use.

### Who Is This For

People who know their domain cold but don't write code:

- A compliance officer who needs an agent to scan regulation changes
- A supply chain manager who wants suppliers scored and ranked automatically
- An underwriter who needs AI to pull data from loan documents and assess risk
- An analyst who wants to automate a weekly report that currently takes two days

---

## How It Works

```
USER: "I need an AI agent that reviews loan applications, pulls data from
       bank statements and credit reports, calculates risk ratios, evaluates
       underwriting rules, and generates a risk assessment report."

                          |
                          v

FRANKENSTEIN: Asks 12-15 targeted questions across 6 categories
             (Input/Output, Process, Data, Edge Cases, Quality Bar, Sample Data)

                          |
                          v

FRANKENSTEIN: Generates architectural blueprint
             - 5 agents, 10 tools, sequential CrewAI pipeline
             - Cross-model adversarial review (Claude designs, GPT attacks)
             - Human approves the blueprint

                          |
                          v

FRANKENSTEIN: Compiles spec into working code
             - agents.py, tools.py, orchestration.py, main.py
             - AST-validated, dependency-checked
             - Tested in Docker sandbox

                          |
                          v

OUTPUT: Downloadable, runnable 5-agent loan underwriting pipeline
        with Streamlit UI, 10 wired tools, and sample data
```

---

## Architecture

### Pipeline Overview

Frankenstein itself is a **LangGraph StateGraph** with 6 specialized AI agents, 2 human checkpoints, and 2 automated feedback loops.

```
  Human                          Frankenstein
  ------                         ------------

  Fuzzy prompt ───────────────> [1. ELICITOR]
                                 GPT-4o-mini
                                 Structured Q&A extraction
                                 6 assessment categories
                                        |
                                        v
                                 Requirements Document
                                        |
  Human validates <──────────── "Is this what you meant?"
                                        |
                                        v
                                [2. ARCHITECT]  <────────┐
                                 Claude Opus              |
                                 Spec from requirements   | (critique loop)
                                 + RAG context            |
                                        |                 |
                                        v                 |
                                [3. CRITIC]  ─────────────┘
                                 GPT-4o
                                 9 attack vectors
                                 Cross-model adversarial
                                        |
                                        v
                                 Validated Spec + Attack Report
                                        |
  Human reviews <──────────────  "Here's the blueprint.
                                  Here's what could go wrong.
                                  Approve?"
                                        |
                                        v
                                [4. BUILDER]  <──────────┐
                                 Claude Opus              |
                                 Spec -> CrewAI code      | (repair loop)
                                 AST validation           |
                                        |                 |
                                        v                 |
                                [5. TESTER]  ─────────────┘
                                 GPT-4o-mini
                                 Docker sandbox execution
                                 Root cause analysis
                                        |
                                        v
                                [6. LEARNER]
                                 GPT-4o-mini
                                 Store patterns in ChromaDB
                                        |
                                        v
                                 Working, tested agents
                                 + Learnings for future builds
```

### The Six Agents

| # | Agent | Model | Purpose |
|---|-------|-------|---------|
| 1 | **Elicitor** | `gpt-4o-mini` | Extracts domain knowledge via structured Q&A. Assesses completeness across 6 categories. Loops until all categories score >0.7 confidence. |
| 2 | **Architect** | `claude-opus-4-6` | Generates framework-agnostic AgentSpec. 8-step process: task decomposition, tool matching, agent grouping, flow design, memory design, error handling, I/O contracts, pipeline schema. RAG-powered (past specs, tools, anti-patterns). |
| 3 | **Critic** | `gpt-4o` | Adversarial spec review. 5 programmatic checks + LLM semantic review = 9 attack vectors. Different model family from Architect on purpose. |
| 4 | **Builder** | `claude-opus-4-6` | Compiles validated spec into runnable CrewAI/LangGraph code. Template-driven generation. AST-based validation. Targeted repair on test failures. |
| 5 | **Tester** | `gpt-4o-mini` | Runs generated agents in Docker sandbox. Traces failures to spec-level root cause decisions. |
| 6 | **Learner** | `gpt-4o-mini` | Stores build outcomes in ChromaDB. Extracts success patterns, failure patterns, anti-patterns. Future builds retrieve these via RAG. |

### Feedback Loops

**Loop 1: Architect ↔ Critic (Spec Refinement)**

The Critic attacks the spec. If critical findings exist and `spec_iteration < max_spec_iterations` (default 3), the spec routes back to the Architect for revision. The Architect must fix every critical finding while preserving working parts. Loop continues until no criticals remain or iteration cap is reached.

**Loop 2: Builder ↔ Tester (Code Repair)**

The Tester runs the generated code. If tests fail:
- **Code-level failures** route back to Builder for targeted repair (reuses previous code, patches specific issues)
- **Spec-level failures** route all the way back to Architect (design flaw, not code bug)
- **Max iterations reached** (default 3) routes to Learner with partial success flag

### Pipeline State

A single state object flows through the entire graph. Every node reads from it, does its work, writes back:

```python
class FrankensteinState(TypedDict, total=False):
    # Session
    session_id: str

    # Stage 1: Elicitor
    raw_prompt: str
    elicitor_questions: list[dict]         # generated questions per category
    human_answers: list[dict]              # human responses
    elicitor_round: int                    # current Q&A round
    elicitor_gap_scores: dict              # per-category confidence scores
    elicitor_all_complete: bool            # all categories above threshold
    elicitor_domain_insights: str          # RAG-retrieved domain context
    requirements: RequirementsDoc          # structured output
    requirements_approved: bool            # human checkpoint 1

    # Stage 2-3: Architect + Critic
    tool_library_matches: list[ToolSchema] # RAG results from tool library
    past_spec_matches: list[dict]          # RAG results from past specs
    spec: AgentSpec                        # generated specification
    architect_reasoning: str               # decision rationale
    critique: CritiqueReport               # critic findings
    spec_iteration: int                    # architect-critic loop count
    spec_approved: bool                    # human checkpoint 2

    # Stage 4-5: Builder + Tester
    generated_code: CodeBundle             # compiled code output
    test_cases: list[TestCase]             # auto-generated from spec contracts
    test_results: TestReport               # execution results
    failure_traces: list[FailureTrace]     # mapped to spec decisions
    build_iteration: int                   # build-test loop count
    build_attempts: int                    # total builder invocations
    repair_history: list[dict]             # what was repaired and why

    # Stage 6: Learning
    build_outcome: BuildOutcome            # final record for memory
```

### Graph Definition

```python
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
graph.add_conditional_edges("elicitor_ask", route_after_elicitor_ask,
    {"elicitor_ask": "elicitor_ask", "elicitor_compile": "elicitor_compile"})
graph.add_conditional_edges("critic", route_after_critique,
    {"architect": "architect", "human_review_spec": "human_review_spec"})
graph.add_conditional_edges("tester", route_after_test,
    {"learner": "learner", "builder": "builder", "architect": "architect"})
```

### Routing Logic

```python
def route_after_critique(state: FrankensteinState) -> str:
    criticals = [f for f in state["critique"].findings if f.severity == "critical"]
    if criticals and state["spec_iteration"] < MAX_SPEC_ITERATIONS:
        return "architect"   # loop back with critique attached
    return "human_review_spec"

def route_after_test(state: FrankensteinState) -> str:
    if state["test_results"].all_passed:
        return "learner"     # done
    if state["build_iteration"] >= MAX_BUILD_ITERATIONS:
        return "learner"     # partial success, store learnings
    for trace in state["failure_traces"]:
        if trace.root_cause_level == "spec":
            return "architect"  # spec-level fix needed
    return "builder"           # code-level fix sufficient
```

---

## Agent Deep Dive

### 1. Elicitor Agent

**Model:** `gpt-4o-mini` | **Purpose:** Turn fuzzy prompts into precise requirements

The Elicitor runs the raw prompt through gap analysis against 6 completeness categories:

| Category | What It Assesses |
|----------|-----------------|
| **Input/Output** | Data formats, sources, expected outputs |
| **Process** | Step-by-step workflow, rules, dependencies |
| **Data** | Schema, volumes, quality constraints |
| **Edge Cases** | Error conditions, missing data handling |
| **Quality Bar** | Success criteria, validation methods |
| **Sample Data** | Concrete examples for testing |

**Process:**
1. Analyze prompt against completeness checklist
2. Score each category (0.0 - 1.0 confidence)
3. Generate targeted questions for categories below 0.7 threshold
4. Present questions to user, receive answers
5. Re-score and loop (max 3 rounds)
6. Compile structured `RequirementsDoc`

**Output:** `RequirementsDoc` with domain, inputs, outputs, process steps, edge cases, quality criteria, constraints, assumptions, and sample data.

### 2. Architect Agent

**Model:** `claude-opus-4-6` | **Purpose:** Transform requirements into a complete AgentSpec

**8-Step Process:**

1. **RAG Query** - Query ChromaDB for similar past specs, available tools, known anti-patterns
2. **Task Decomposition** - Break process steps into discrete computational tasks tagged with capability type (text_extraction, calculation, reasoning, generation, api_call, data_processing)
3. **Tool Selection** - Match each task to a tool from the Tool Schema Library. Selection criteria: format compatibility (accepts/outputs), downstream needs, tool limitations, incompatibility constraints
4. **Agent Grouping** - Group related tasks into agents. Tight data loops = same agent. Independent chains = separate agents. Each agent gets: id, role, goal, backstory, tools, reasoning_strategy
5. **Execution Flow** - Choose pattern from dependencies: parallel, sequential, graph (LangGraph), hierarchical (CrewAI)
6. **Memory Design** - Determine shared keys, strategy, persistence
7. **I/O Contracts** - Define input/output schema per agent. Every required output must appear in downstream input
8. **Pipeline Schema** - Define how data enters and leaves the pipeline. Sample input for test harness

**Constraint:** The Architect can ONLY use tools that exist in the Tool Schema Library. It cannot invent tool IDs. An explicit allowlist of valid tool IDs is injected into every prompt.

**Revision mode:** When critique findings come back, the Architect receives the current spec + critique + original requirements and must fix every critical finding while preserving working parts.

### 3. Critic Agent

**Model:** `gpt-4o` (different model family from Architect) | **Purpose:** Adversarial spec review

**9 Attack Vectors:**

| # | Vector | Method | Severity |
|---|--------|--------|----------|
| 1 | **Circular Dependencies** | Topological sort on execution graph | Critical if cycle found |
| 2 | **Format Compatibility** | Walk every edge, compare output_schema to input_schema | Critical on mismatch |
| 3 | **Dependency Completeness** | Trace required fields to upstream producers | Critical if missing |
| 4 | **Dead-End Analysis** | Check error handling coverage, flag skip-on-critical-path | Warning/Critical |
| 5 | **Resource Conflicts** | Check parallel agents writing same shared memory keys | Warning |
| 6 | **Tool Validation** | Can this tool actually perform the agent's described task? | Critical if not |
| 7 | **Tool Template Availability** | Does the library_ref exist in the Tool Schema Library? | Critical if missing |
| 8 | **Semantic Coherence** | Are roles/goals/backstories appropriate for the domain? | Suggestion/Warning |
| 9 | **Pydantic Reserved Words** | Check field names against Python/Pydantic reserved words | Critical if collision |

Vectors 1-5 and 7-9 are **programmatic** (deterministic checks). Vector 6 and 8 are **LLM-powered** (semantic analysis by GPT-4o).

**Output:**
```python
class CritiqueReport(BaseModel):
    findings: list[Finding]   # severity-scored issues
    summary: str              # 2-3 sentence assessment
    iteration: int            # which review cycle

class Finding(BaseModel):
    vector: str               # which attack vector
    severity: "critical" | "warning" | "suggestion"
    description: str          # what's wrong
    location: str             # which agent/tool/edge
    evidence: str             # specific spec values
    suggested_fix: str        # actionable change
```

### 4. Builder Agent

**Model:** `claude-opus-4-6` | **Purpose:** Compile spec into runnable code

**Compilation process:**
1. Read spec and select framework compiler (CrewAI or LangGraph)
2. Retrieve tool code templates from Tool Schema Library
3. Plan the build (file structure, imports, wiring)
4. Generate each file: `main.py`, `agents.py`, `tools.py`, `orchestration.py`, `tasks.py`, `app.py`, `requirements.txt`, `sample_data.json`
5. AST-based validation (syntax, imports, tool coverage, schema compliance)
6. If validation fails: self-repair loop (max 2 iterations)

**Generated project structure:**
```
generated_agent/
  main.py              # CLI entry point
  app.py               # Streamlit UI
  agents.py            # Agent definitions (roles, goals, backstories, tools)
  tools.py             # Tool implementations with @tool decorators
  tasks.py             # Task definitions with context chains
  orchestration.py     # CrewAI Crew or LangGraph graph
  requirements.txt     # Python dependencies
  sample_data.json     # Test data matching pipeline_input_schema
  .env.example         # Required environment variables
  README.md            # Auto-generated usage instructions
```

**Targeted repair:** When previous build passed validation but tester found failures, the Builder reuses the previous code and does targeted repair instead of regenerating from scratch. This preserves working code and focuses fixes on actual failures.

**Validation checks (AST-based):**
- Syntax: `ast.parse()` on all `.py` files
- Imports: verify all imports resolve
- Tool coverage: every tool imported in agents.py exists in tools.py
- Schema compliance: function signatures match I/O contracts

### 5. Tester Agent

**Model:** `gpt-4o-mini` | **Purpose:** Execute and validate generated agents

**Execution flow:**
1. Install dependencies in isolated environment
2. Run `main.py` with sample input
3. Capture stdout, stderr, exit code
4. Parse output against expected schema
5. If failure: generate `FailureTrace` with root cause analysis

**Failure tracing:**
```python
class FailureTrace(BaseModel):
    test_name: str
    error_type: "crash" | "wrong_output" | "missing_field" | "quality_fail"
    raw_error: str                    # actual error message
    failing_agent: str                # which agent in generated pipeline
    root_cause_level: "code" | "spec" # determines routing
    root_cause_analysis: str          # "Agent 2 received XML but tool expects JSON"
    spec_decision_responsible: str    # "spec.tools[1].library_ref = xml_parser"
    suggested_fix: str                # actionable repair instruction
```

The `root_cause_level` determines routing: `"code"` loops back to Builder, `"spec"` loops back to Architect.

### 6. Learner Agent

**Model:** `gpt-4o-mini` | **Purpose:** Store build outcomes for future RAG retrieval

**What gets stored after every build:**
```python
class BuildOutcome(BaseModel):
    requirements_hash: str            # for similarity matching
    requirements_summary: str         # embedded for RAG retrieval
    domain: str
    spec_snapshot: AgentSpec          # the final validated spec
    framework_used: str               # crewai or langgraph
    tools_used: list[str]             # tool IDs from library
    test_results: TestReport
    iterations_needed: int            # total loops
    total_time_seconds: float
    success_patterns: list[str]       # patterns that worked
    failure_patterns: list[str]       # what went wrong and was fixed
    anti_patterns: list[str]          # patterns that caused failures
    lessons_learned: list[str]        # extracted insights
    outcome: "success" | "partial_success" | "failure"
```

**Learning loop:** Learner stores patterns in ChromaDB. On future builds, the Architect queries these collections to retrieve relevant past specs, avoid known anti-patterns, and learn from previous successes.

---

## Data Models

### RequirementsDoc

```python
class RequirementsDoc(BaseModel):
    domain: str
    inputs: list[DataSpec]               # name, format, description, example
    outputs: list[DataSpec]              # name, format, description, example
    process_steps: list[ProcessStep]     # step_number, description, rules, depends_on
    edge_cases: list[EdgeCase]           # description, expected_handling
    quality_criteria: list[QualityCriterion]  # criterion, validation_method
    constraints: list[str]
    assumptions: list[str]
    sample_input_example: dict | None
    sample_output_example: dict | None
```

### AgentSpec

```python
class AgentSpec(BaseModel):
    metadata: SpecMetadata               # name, domain, framework_target, rationale, pipeline schemas
    agents: list[AgentDef]               # id, role, goal, backstory, tools, reasoning_strategy
    tools: list[ToolRef]                 # id, library_ref, config, accepts, outputs
    memory: MemoryConfig                 # strategy, shared_keys, persistence
    execution_flow: ExecutionFlow        # pattern, graph (nodes + edges)
    error_handling: list[ErrorHandler]   # per-agent: on_failure, max_retries, fallback
    io_contracts: list[IOContract]       # per-agent: input_schema, output_schema
    sample_input: dict                   # concrete test data
```

### CodeBundle

```python
class CodeBundle(BaseModel):
    files: dict[str, str]                # filename -> content
    framework: str                       # "crewai" or "langgraph"
    entry_point: str                     # "main.py"
    dependencies: list[str]              # pip packages
    validation_passed: bool
    validation_errors: list[str]
```

### CritiqueReport

```python
class CritiqueReport(BaseModel):
    findings: list[Finding]              # severity-scored issues
    summary: str                         # overall assessment
    iteration: int                       # review cycle number

class Finding(BaseModel):
    vector: str                          # attack vector name
    severity: "critical" | "warning" | "suggestion"
    description: str
    location: str                        # affected component
    evidence: str                        # specific spec values
    suggested_fix: str
```

### TestReport & FailureTrace

```python
class TestReport(BaseModel):
    total: int
    passed: int
    failed: int
    errors: int
    all_passed: bool
    results: list[TestResult]            # per-test: status, stdout, stderr, exit_code

class FailureTrace(BaseModel):
    test_name: str
    error_type: "crash" | "wrong_output" | "missing_field" | "quality_fail"
    raw_error: str
    failing_agent: str
    root_cause_level: "code" | "spec"
    root_cause_analysis: str
    spec_decision_responsible: str
    suggested_fix: str
```

---

## Tool Schema Library

Pre-seeded library of 18 validated tool definitions stored as JSON in `backend/app/tool_library/` and indexed in ChromaDB. Each tool has:

```python
class ToolSchema(BaseModel):
    id: str                       # "pdf_parser_pymupdf"
    name: str                     # "PyMuPDF PDF Parser"
    description: str              # capabilities description
    category: str                 # "document_extraction"
    accepts: list[str]            # ["pdf"]
    outputs: list[str]            # ["text", "tables"]
    output_format: str            # "json"
    limitations: list[str]        # ["no OCR for scanned documents"]
    dependencies: list[str]       # ["pymupdf>=1.23.0"]
    code_template: str            # actual Python implementation
    compatible_with: list[str]    # tool IDs that work well together
    incompatible_with: list[str]  # tool IDs known to conflict
```

### Available Tools

| Tool ID | Category | Accepts | Outputs | Purpose |
|---------|----------|---------|---------|---------|
| `pdf_parser_pymupdf` | document_extraction | pdf | text, tables | Extract text and tables from PDFs |
| `csv_parser` | data_ingestion | csv | json | Parse CSV files into structured records |
| `xml_parser` | data_processing | xml | json | Parse XML into structured JSON |
| `file_reader` | data_ingestion | txt, json, yaml | text, json | Read common file formats |
| `json_transformer` | data_processing | json | json | Reshape, filter, merge JSON |
| `data_transformer` | data_processing | json, dict, list | json | Transform, filter, map, aggregate data |
| `ocr_tesseract` | document_extraction | image, scanned_pdf | text | OCR for scanned documents |
| `financial_calculator` | computation | json | json | DTI, LTV, financial ratios |
| `statistical_analyzer` | computation | json | json | Statistical analysis and trends |
| `scoring_engine` | reasoning | json | json | Weighted composite scoring |
| `rule_engine` | reasoning | json | json | Evaluate data against configurable rules |
| `llm_reasoner` | reasoning | text | text | LLM-powered analysis and reasoning |
| `report_generator` | generation | json | markdown, json | Compile analysis into structured reports |
| `data_visualizer` | generation | json | image, html | Generate charts and visualizations |
| `web_search` | research | query | json | Search the web for information |
| `code_executor` | computation | python | output | Execute Python code snippets |
| `email_sender` | communication | json, text | json | Send emails via SMTP |
| `database_writer` | data_storage | json, dict, list | json | Write data to SQL databases |

The `compatible_with` and `incompatible_with` fields grow over time as the Learner records which tool combinations work well or cause issues.

---

## Chroma Memory Architecture

Four collections power the RAG system:

| Collection | Content | Query Pattern |
|-----------|---------|---------------|
| `tool_schemas` | Validated tool definitions | Architect queries with task capability requirements |
| `spec_patterns` | Past validated specs + outcomes | Architect queries with current requirements |
| `anti_patterns` | Failed patterns with explanations | Architect queries to avoid known failures |
| `repair_patterns` | Successful repair strategies | Builder queries when fixing test failures |

### RAG Query Flow

```
Architect receives requirements
    |
    v
Query 1: spec_patterns - "Find specs similar to: [requirements_summary]"
    -> Returns top-3 past specs with outcomes
    -> Architect uses successful ones as structural reference
    |
    v
Query 2: tool_schemas - For each task: "Find tools that can: [capability]"
    -> Returns ranked tool options with compatibility info
    -> Architect selects based on format chain compatibility
    |
    v
Query 3: anti_patterns - "Has pattern similar to [proposed] failed before?"
    -> Returns matching anti-patterns
    -> Architect avoids known failure modes
```

**The system gets smarter with every build.** Learner stores outcomes after every pipeline run. Future Architect queries retrieve these patterns. Builder retrieves repair patterns when fixing failures.

---

## Cross-Model Adversarial Review

Architect and Critic deliberately use **different LLM model families**:

| Role | Model | Family |
|------|-------|--------|
| Architect | `claude-opus-4-6` | Anthropic |
| Critic | `gpt-4o` | OpenAI |

**Why:** Same-model review has blind spots. A model that generated a design will tend to approve it. Using a different model family for adversarial review catches flaws that same-model review misses. This is the same principle as code review by a different engineer.

The Critic doesn't just rubber-stamp - it runs 9 distinct attack vectors including programmatic graph analysis and semantic capability review.

---

## Tech Stack

| Layer | Technology | Role |
|-------|-----------|------|
| **Pipeline Orchestration** | LangGraph (StateGraph) | Frankenstein's internal pipeline with conditional edges for feedback loops |
| **LLM Gateway** | OpenRouter | Single API for all model access, model-per-agent routing |
| **Generated Agent Framework** | CrewAI / LangGraph | Architect decides per case - CrewAI for role-based crews, LangGraph for state-dependent flows |
| **Vector Database** | ChromaDB | Tool schemas, past specs, learnings, anti-patterns for RAG |
| **Backend** | FastAPI + WebSockets | API server, pipeline orchestration, session management |
| **Frontend** | React + TypeScript + Three.js | Chat interface, Q&A cards, spec review, pipeline visualization, code preview |
| **3D Rendering** | React Three Fiber + drei | Wireframe heart on landing page with scroll-driven dismantling |
| **Sandbox Execution** | Docker (pre-built base image) | Isolated agent testing with Python + CrewAI + common packages |
| **Code Validation** | AST-based (Python ast module) | Syntax checking, import verification, tool coverage, schema compliance |
| **State Persistence** | SQLite (LangGraph checkpointer) | Pipeline state checkpointing for human-in-the-loop interrupts |

### Model Routing

```python
MODEL_ROUTING = {
    "elicitor":  "openai/gpt-4o-mini",       # fast, conversational
    "architect": "anthropic/claude-opus-4-6",  # strongest structured reasoning
    "critic":    "openai/gpt-4o",              # different family for adversarial review
    "builder":   "anthropic/claude-opus-4-6",  # strong code generation
    "tester":    "openai/gpt-4o-mini",         # error analysis
    "learner":   "openai/gpt-4o-mini",         # lightweight data structuring
}
```

4 different models across 2 model families. Each chosen for its specific strength.

---

## Project Structure

```
frankenstein/
  backend/
    app/
      agents/
        elicitor.py            # Structured Q&A extraction (gpt-4o-mini)
        architect.py           # Spec generation + revision (claude-opus)
        critic.py              # 9-vector adversarial review (gpt-4o)
        builder.py             # Code compilation + repair (claude-opus)
        tester.py              # Docker sandbox execution (gpt-4o-mini)
        learner.py             # ChromaDB pattern storage (gpt-4o-mini)
        _validation.py         # AST-based code validation
      models/
        state.py               # FrankensteinState (TypedDict)
        requirements.py        # RequirementsDoc, GapAnalysis, CategoryAssessment
        spec.py                # AgentSpec, AgentDef, ToolRef, ExecutionFlow
        critique.py            # CritiqueReport, Finding
        code.py                # CodeBundle
        testing.py             # TestCase, TestResult, TestReport, FailureTrace
        learning.py            # BuildOutcome
        messages.py            # WebSocket message types
        tools.py               # ToolSchema
      pipeline/
        graph.py               # LangGraph StateGraph definition + routing
        checkpoints.py         # Human checkpoint implementations
      services/
        llm_service.py         # OpenRouter LLM wrapper
        chroma_service.py      # ChromaDB operations (4 collections)
        session_service.py     # Session management + file serving
        docker_service.py      # Docker container management
      tool_library/
        pdf_parser_pymupdf.json
        csv_parser.json
        xml_parser.json
        data_transformer.json
        financial_calculator.json
        rule_engine.json
        scoring_engine.json
        report_generator.json
        email_sender.json
        database_writer.json
        ... (18 tools total)
      config.py                # Settings, model routing, pipeline constants
      main.py                  # FastAPI app, WebSocket handlers, endpoints
    tests/
      test_main.py
      test_elicitor.py
      test_chroma_service.py
      test_session_service.py
    docker/
      Dockerfile.runner        # Pre-built base image for agent execution
    chroma_data/               # Persisted ChromaDB collections
    generated_agents/          # Output directory for built agents
    requirements.txt
    .env.example

  frontend/
    src/
      chat-components/
        ChatThread.tsx         # Main chat conversation thread
        QuestionGroupCard.tsx  # Elicitor Q&A interface with confidence indicators
        RequirementsCard.tsx   # Requirements review + approval checkpoint
        SpecReviewCard.tsx     # Spec + critique review + approval checkpoint
        CompletionCard.tsx     # Build results + download + code preview
        CodePreview.tsx        # Syntax-highlighted file browser
        CodingScreen.tsx       # Build phase live coding animation
        PipelineGraph.tsx      # SVG pipeline visualization with animations
        PipelineSidebar.tsx    # Stage status sidebar
        PromptInput.tsx        # User input with submit gating
        TypingIndicator.tsx    # Stage-aware typing animation
        ActivityPill.tsx       # Inline agent activity messages
        ErrorCard.tsx          # Error display with retry/restart
        FlowDiagram.tsx        # Agent flow visualization
        CritiqueFindingList.tsx # Critique findings display
        StageIndicator.tsx     # Per-stage status indicator
      components/
        hero/                  # Landing page hero section
        three/                 # Three.js 3D components (WireframeHeart)
        cta/                   # Call-to-action components
        demo/                  # Demo section
        social/                # Social proof section
        pipeline/              # Pipeline visualization components
      context/
        pipelineReducer.ts     # Pipeline state management
      hooks/
        useWebSocket.ts        # WebSocket connection management
        useAudio.ts            # Audio system (Web Audio API)
      api/
        sessions.ts            # Backend API client
      App.tsx                  # Root component with routing
      index.css                # Global styles (dark laboratory theme)
    package.json
    vite.config.ts
    tsconfig.json

  docs/
    Frankenstein_Solution_Approach.md    # Full architecture document
    Frankenstein_Justification_Document.md  # Why this problem matters
    Frankenstein_Product_Description.md  # Business-side overview
    HANDOFF.md                           # Dev team build plan
```

---

## Setup & Installation

### Prerequisites

- Python 3.11+ (backend)
- Node.js 18+ (frontend)
- Docker (for agent testing sandbox)
- OpenRouter API key

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# Seed the tool library into ChromaDB
python -c "from app.services.chroma_service import ChromaService; ChromaService().seed_tool_library()"

# Start the backend
uvicorn app.main:app --host 0.0.0.0 --port 7749 --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
# Frontend runs on http://localhost:7751
```

### Docker Runner (for agent testing)

```bash
cd backend/docker
docker build -t frankenstein-runner -f Dockerfile.runner .
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes | OpenRouter API key for LLM access |
| `BACKEND_HOST` | No | Backend host (default: `0.0.0.0`) |
| `BACKEND_PORT` | No | Backend port (default: `7749`) |
| `CORS_ORIGINS` | No | Allowed CORS origins (default: `http://localhost:7751`) |
| `CHROMA_PERSIST_DIR` | No | ChromaDB storage path (default: `./chroma_data`) |
| `GENERATED_AGENTS_DIR` | No | Output directory (default: `./generated_agents`) |
| `MAX_SPEC_ITERATIONS` | No | Architect-Critic loop cap (default: `3`) |
| `MAX_BUILD_ITERATIONS` | No | Builder-Tester loop cap (default: `3`) |
| `MAX_ELICITOR_ROUNDS` | No | Q&A round cap (default: `3`) |
| `COMPLETENESS_THRESHOLD` | No | Elicitor confidence threshold (default: `0.7`) |
| `DOCKER_TIMEOUT` | No | Container execution timeout in seconds (default: `60`) |
| `TESTER_LIVE_EXECUTION` | No | Enable Docker sandbox testing (default: `true`) |

---

## Running the Application

### Full Stack (Development)

```bash
# Terminal 1: Backend
cd backend && source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 7749 --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

Open `http://localhost:7751` in your browser.

### Using the Chat Interface

1. **Enter your prompt** - Describe the agent you want to build in plain English
2. **Answer questions** - The Elicitor asks 12-15 targeted questions across 6 categories. Answer them to refine requirements
3. **Review requirements** - Approve or edit the extracted requirements document
4. **Review blueprint** - See the generated spec + critique findings. Approve to proceed to building
5. **Watch it build** - Live coding animation shows file generation. Pipeline graph shows stage progress
6. **Download your agent** - Get a zip file with the complete, runnable agent project

---

## Demo: Loan Underwriting Co-Pilot

**Problem Statement:** PS-08 - Build an AI co-pilot that assists loan underwriters by extracting financial data, calculating risk ratios, and generating assessment reports.

**One prompt to Frankenstein:**
> "I need an AI agent that reviews loan applications, pulls data from bank statements and credit reports, calculates risk ratios like DTI and LTV, evaluates underwriting rules, scores risk, and generates a comprehensive risk assessment report."

**What Frankenstein built:**

| Component | Details |
|-----------|---------|
| **Agents** | 5 (Data Extractor, Financial Calculator, Rules Evaluator, Report Generator, Report Deliverer) |
| **Tools** | 10 (PDF parser, CSV parser, XML parser, Data transformer, Financial calculator, Rule engine, Scoring engine, Report generator, Email sender, Database writer) |
| **Framework** | CrewAI with sequential process |
| **Pipeline** | Sequential: Extract -> Calculate -> Evaluate -> Report -> Deliver |

**Actual output from the generated pipeline:**

```json
{
  "applicant_information": {"name": "John Doe", "monthly_income": 4500},
  "financial_data_summary": {"DTI": 27.78, "LTV": 80.0, "income_stability": "insufficient_data"},
  "credit_score_analysis": {"credit_score": 720, "risk_score": 0.3546, "risk_level": "Medium"},
  "underwriting_rules_applied": [
    {"rule": "DTI_threshold", "passed": true, "value": 27.78, "threshold": 36},
    {"rule": "LTV_threshold", "passed": false, "value": 80.0, "threshold": 80},
    {"rule": "credit_score_minimum", "passed": true, "value": 720, "threshold": 620}
  ],
  "recommendation": "refer",
  "notes": "Risk assessment completed for John Doe. Overall risk level: Medium."
}
```

The generated agent is fully runnable: `pip install -r requirements.txt && python main.py`. It also includes a Streamlit UI (`streamlit run app.py`).

---

## Configuration

### Pipeline Constants

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_spec_iterations` | 3 | Maximum Architect-Critic loop cycles |
| `max_build_iterations` | 3 | Maximum Builder-Tester loop cycles |
| `max_builder_repair_iterations` | 2 | Maximum self-repair attempts per build |
| `max_elicitor_rounds` | 3 | Maximum Q&A rounds with user |
| `completeness_threshold` | 0.7 | Minimum confidence per category to proceed |
| `docker_timeout` | 60 | Container execution timeout (seconds) |
| `pipeline_timeout` | 300 | Total pipeline timeout (seconds) |
| `session_max_age_hours` | 24 | Session expiry time |

### Ports

| Service | Port |
|---------|------|
| Backend (FastAPI) | 7749 |
| Frontend (Vite) | 7751 |

---

## What Frankenstein Does Not Do

- **Does not understand domains autonomously** - relies on the human for domain knowledge. Frankenstein is the engineering team, not the product manager.
- **Does not replace prompt engineering entirely** - the Elicitor improves input quality, but garbage domain knowledge in still produces garbage agents out.
- **Does not guarantee perfect agents on first pass** - the test-and-fix loop exists because first builds will have issues. The system's strength is autonomous correction, not perfection.
- **Does not work without a Tool Schema Library** - the Architect can only select tools it knows about. An empty library means no useful output.

---

## Documentation

| Document | Description |
|----------|-------------|
| [Solution Approach](docs/Frankenstein_Solution_Approach.md) | Full architecture, data models, agent engineering, stack decisions |
| [Justification](docs/Frankenstein_Justification_Document.md) | Why this problem matters, what makes Frankenstein different |
| [Product Description](docs/Frankenstein_Product_Description.md) | Business-side overview for non-technical readers |
| [Dev Handoff](docs/HANDOFF.md) | Build plan with task breakdown for dev team |
| [Problem Statement](docs/69fe33f7e77b5_Problem_statement.docx) | Original PS-03 problem statement |

---

**PS-03 | Meta-Agentic Systems | Team: Aarya Srivastava, Ved Pawar, Bhawana**
