# Frankenstein — Demo Guide

## Prerequisites

### 1. OpenRouter API Key

Get one from [openrouter.ai](https://openrouter.ai). You need credits for:
- `openai/gpt-4o-mini` (elicitor, tester, learner)
- `openai/gpt-4o` (architect, critic, builder)

### 2. Environment Setup

```bash
# Backend
cd backend
cp .env.example .env   # or create manually:
echo "OPENROUTER_API_KEY=sk-or-..." > .env

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 3. Docker (optional — for live agent testing)

```bash
# Build the runner base image
docker build -t frankenstein-runner -f runner/Dockerfile .
```

If Docker isn't available, Frankenstein still works — the Tester agent runs in simulation mode.

---

## Starting the App

Open **two terminals**:

**Terminal 1 — Backend** (port 7749):
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 7749 --reload
```

**Terminal 2 — Frontend** (port 7751):
```bash
cd frontend
npm run dev
```

Open your browser to **http://localhost:7751**.

---

## App Structure

| URL | What It Is |
|-----|-----------|
| `http://localhost:7751/` | Landing page — Frankenstein-themed marketing site with lab aesthetic |
| `http://localhost:7751/chat` | Chat app — the actual pipeline interface |

The landing page has a CTA that navigates to `/chat`. You can also go directly to `/chat`.

---

## Demo Flow

### Act 1: The Prompt

1. Navigate to **http://localhost:7751/chat**
2. You see the entry screen: "Describe your workflow. Get working AI agents."
3. Type your prompt and click **Assemble** (or press Enter)

**Recommended demo prompts:**

> **PS-08 (Loan Underwriting):**
> "Build me a loan underwriting co-pilot that reads bank statements and credit reports, extracts financial data, calculates risk ratios like DTI and LTV, applies underwriting rules, and generates a structured risk assessment report with approve/deny recommendation."

> **PS-06 (Supplier Scoring):**
> "Build an agent that ingests supplier delivery data from CSV files, analyzes reliability metrics like on-time delivery rate and defect rates, scores each supplier on a weighted scale, and produces a ranked report with visualizations."

> **Simple starter prompt (if short on time):**
> "Build me an agent that reads PDF invoices, extracts line items and totals, and outputs a structured JSON summary."

### Act 2: Elicitor Q&A

After submitting, the pipeline starts. The **Elicitor** (gpt-4o-mini) analyzes your prompt against five categories:
- Input/Output specs
- Process steps
- Data requirements
- Edge cases
- Quality criteria

It sends back **grouped questions** for gaps it found. Answer them naturally — full sentences work best. The Elicitor runs up to 3 rounds, asking fewer questions each time as gaps fill.

**Demo talking points during Q&A:**
- "Notice it's asking domain-specific questions — not generic ones"
- "It identified what's missing from the prompt automatically"
- "The human provides domain knowledge, Frankenstein provides engineering"

### Act 3: Requirements Review (Checkpoint 1)

After Q&A, the Elicitor compiles a **RequirementsDoc** — structured extraction of:
- Domain classification
- Input/output data specs
- Process steps with dependencies
- Edge cases and handling
- Quality criteria

You see a **RequirementsCard** with two options:
- **Approve** — proceeds to architecture design
- **Request Changes** — sends corrections back to the Elicitor

**For the demo: Approve.** You can mention that corrections loop back for revision.

### Act 4: Architecture Design (runs automatically)

After approval, three things happen in sequence:

1. **Architect** (gpt-4o) designs the agent spec:
   - Queries Chroma for similar past specs and matching tools
   - Decomposes requirements into tasks
   - Groups tasks into agents
   - Selects framework (CrewAI or LangGraph)
   - Designs execution flow and memory strategy

2. **Critic** (gpt-4o) attacks the spec across 6 vectors:
   - Format compatibility between agents
   - Tool validation
   - Dead-end analysis
   - Dependency completeness
   - Resource conflicts
   - Circular dependencies

3. If **critical findings** exist, the Architect revises and the Critic re-checks (up to 3 iterations).

The **sidebar** shows pipeline progress — stages light up as they complete.

### Act 5: Spec Review (Checkpoint 2)

You receive a **SpecReviewCard** showing:
- Agent roles and responsibilities
- Tools selected from the library
- Execution flow pattern
- Critique findings with severity ratings
- A flow diagram of the agent pipeline

Two options:
- **Approve** — proceeds to code generation
- **Request Changes** — sends feedback, Architect revises

**For the demo: Approve.** Point out the critique findings — "a separate AI model reviewed this design for failure modes."

### Act 6: Build, Test, Learn (runs automatically)

After spec approval, the remaining pipeline runs in background:

1. **Builder** (gpt-4o) compiles the spec into working code:
   - Generates `main.py`, `agents.py`, `tools.py`, `orchestration.py`
   - Framework-specific (CrewAI or LangGraph)
   - Includes `requirements.txt` and test stubs

2. **Tester** (gpt-4o-mini) validates the generated code:
   - Generates test cases from I/O contracts
   - Runs in Docker sandbox (or simulation)
   - If tests fail: traces root cause to code-level or spec-level
   - Code failures → loop back to Builder (up to 10 iterations)
   - Spec failures → loop back to Architect

3. **Learner** (gpt-4o-mini) stores the build outcome in Chroma:
   - Success/failure patterns
   - Anti-patterns to avoid
   - Spec snapshots for future RAG retrieval

### Act 7: Delivery

A **CompletionCard** appears with:
- Framework used
- Number of agents built
- Test results (passed/total)
- File count
- **Download** button — downloads a `.zip` of the complete agent project

**Demo finale:** Click download. Unzip. Show the generated code structure. Highlight that it's real, runnable code — not pseudocode.

---

## Sidebar Pipeline Visualization

The right sidebar shows all six stages plus two checkpoints:

```
  Elicitor           ← Q&A with human
  Requirements Review ← Checkpoint 1
  Architect          ← Spec design
  Critic             ← Adversarial review
  Spec Review        ← Checkpoint 2
  Builder            ← Code generation
  Tester             ← Validation
  Learner            ← Memory storage
```

Stages show status: idle → active → done. Checkpoints pause for human input.

---

## Key Talking Points

### Why Six Agents, Not One LLM Call?

A single prompt can generate agent code. But it can't:
- Ask what's missing from requirements
- Validate tool compatibility before building
- Attack its own design for failure modes
- Run the code and trace failures to architectural decisions
- Learn from past builds

Each stage exists because it solves a failure mode one-shot generation can't.

### Cross-Model Adversarial Review

The Architect and Critic deliberately use **different model families**. Same-model review has blind spots — the model won't catch its own systematic biases. Cross-model review catches more.

### Human-in-the-Loop, Not Human-in-the-Way

Two checkpoints. Not twelve. The human validates requirements and architecture — the two decisions that matter most. Everything after that is autonomous.

### Template-Driven, Not Free-Form

The Builder doesn't freestyle code. It compiles from validated specs using framework-specific templates. This is why the code actually works — it's deterministic compilation, not generation.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Frontend shows blank page | Check backend is running on port 7749 |
| "unknown session" on WebSocket | Session expired (24h max). Start a new chat |
| Pipeline hangs | Check backend logs for LLM errors. Usually an API key or rate limit issue |
| No tools found by Architect | Tool library not seeded. Check `backend/app/tool_library/` has JSON files and backend startup logs show "Seeded N tools" |
| Download returns 404 | Builder didn't generate files. Check backend logs for builder errors |

### Checking Backend Logs

Backend logs every stage transition:
```
[session-id] Pipeline initial run complete
[session-id] Routing: critic → architect (criticals=2, iteration=1/3)
[session-id] Spec feedback sent — architect revising
```

### Resetting State

```bash
# Clear all sessions and checkpoints
rm -f backend/checkpoints.sqlite3*
rm -rf backend/generated_agents/*
# Restart backend
```

---

## Docker Compose (Alternative Setup)

For a containerized demo:

```bash
# Set your API key
export OPENROUTER_API_KEY=sk-or-...

# Start backend + Chroma
docker compose up --build

# Frontend still runs locally
cd frontend && npm run dev
```

Backend runs on port 7749, Chroma on 7753.

---

## Demo Timing

| Section | Duration |
|---------|----------|
| Intro + prompt entry | 1 min |
| Elicitor Q&A (1-3 rounds) | 2-3 min |
| Requirements review | 1 min |
| Architect + Critic (automatic) | 1-2 min |
| Spec review | 1-2 min |
| Build + Test + Learn | 1-2 min |
| Download + show code | 1 min |
| **Total** | **~8-12 min** |

If pressed for time, use the simple invoice prompt. If demonstrating depth, use the loan underwriting prompt and engage with the Elicitor questions thoroughly.

---

## Landing Page Demo (Optional)

If presenting the product story before the live demo:

1. Start at `http://localhost:7751/` (landing page)
2. Scroll through the lab-themed sections:
   - **Hero** — "Describe your workflow. Get working AI agents."
   - **Pipeline visualization** — six-stage dissection table
   - **Comparison** — Frankenstein vs traditional agent building
   - **Specimen cabinet** — example use cases
   - **Social proof / research notes**
   - **CTA** — leads to `/chat`
3. Hidden feature: `Ctrl+Shift+L` opens lab controls (dev mode only) — adjusts visual parameters like voltage intensity and assembly speed

Then transition to the live chat demo.
