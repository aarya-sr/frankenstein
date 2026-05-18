#!/usr/bin/env python3
"""Generate Frankenstein Project Report PDF."""

from fpdf import FPDF
import os

class ReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 8, "Frankenstein - Meta-Agentic System for Autonomous Agent Construction", align="R")
            self.ln(4)
            self.set_draw_color(200, 200, 200)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def cover_page(self):
        self.add_page()
        self.ln(50)
        self.set_font("Helvetica", "B", 36)
        self.set_text_color(30, 30, 30)
        self.cell(0, 20, "FRANKENSTEIN", align="C")
        self.ln(16)
        self.set_font("Helvetica", "", 16)
        self.set_text_color(80, 80, 80)
        self.cell(0, 10, "Meta-Agentic System for", align="C")
        self.ln(10)
        self.cell(0, 10, "Autonomous Agent Construction", align="C")
        self.ln(30)

        self.set_draw_color(60, 60, 60)
        self.line(60, self.get_y(), 150, self.get_y())
        self.ln(20)

        self.set_font("Helvetica", "", 12)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "PS-03 Hackathon Project Report", align="C")
        self.ln(8)
        self.cell(0, 8, "May 2026", align="C")
        self.ln(30)

        self.set_font("Helvetica", "I", 10)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, "One conversation. Working agents. Tested and ready.", align="C")

    def section_title(self, num, title):
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(30, 30, 30)
        self.ln(6)
        self.cell(0, 12, f"{num}. {title}")
        self.ln(4)
        self.set_draw_color(60, 60, 60)
        self.line(10, self.get_y(), 80, self.get_y())
        self.ln(8)

    def sub_title(self, title):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(50, 50, 50)
        self.cell(0, 10, title)
        self.ln(8)

    def sub_sub_title(self, title):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(60, 60, 60)
        self.cell(0, 8, title)
        self.ln(6)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5.5, text)
        self.ln(3)

    def bullet(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        x = self.get_x()
        self.cell(8, 5.5, "-")
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def table_header(self, cols, widths):
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(45, 45, 45)
        self.set_text_color(255, 255, 255)
        for col, w in zip(cols, widths):
            self.cell(w, 7, f" {col}", border=1, fill=True)
        self.ln()

    def table_row(self, cols, widths, fill=False):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(40, 40, 40)
        if fill:
            self.set_fill_color(245, 245, 245)
        else:
            self.set_fill_color(255, 255, 255)
        max_h = 7
        for col, w in zip(cols, widths):
            self.cell(w, max_h, f" {col}", border=1, fill=True)
        self.ln()

    def key_value(self, key, value):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(50, 50, 50)
        self.cell(50, 6, key + ":")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.cell(0, 6, value)
        self.ln(7)

    def code_block(self, text):
        self.set_font("Courier", "", 8)
        self.set_fill_color(240, 240, 240)
        self.set_text_color(30, 30, 30)
        self.set_draw_color(200, 200, 200)
        x = self.get_x()
        y = self.get_y()
        self.multi_cell(190, 4.5, text, border=1, fill=True)
        self.ln(4)


def build_report():
    pdf = ReportPDF()
    pdf.alias_nb_pages()

    # ========== COVER PAGE ==========
    pdf.cover_page()

    # ========== TABLE OF CONTENTS ==========
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 12, "Table of Contents")
    pdf.ln(14)
    toc = [
        ("1", "Problem Statement", 3),
        ("2", "Solution Overview", 4),
        ("3", "Unique Selling Proposition (USP)", 5),
        ("4", "System Architecture", 6),
        ("5", "Pipeline Deep Dive", 8),
        ("6", "Technology Stack", 12),
        ("7", "Data Models & State Management", 13),
        ("8", "Chroma Vector Memory Architecture", 14),
        ("9", "Frontend Architecture", 15),
        ("10", "Real-Time Streaming Architecture", 16),
        ("11", "Demo Targets & Validation", 17),
        ("12", "Challenges Solved", 18),
        ("13", "Scope & Limitations", 19),
        ("14", "Conclusion", 19),
    ]
    for num, title, pg in toc:
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(40, 40, 40)
        label = f"  {num}.  {title}"
        pdf.cell(160, 7, label)
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 7, str(pg), align="R")
        pdf.ln(7)

    # ========== 1. PROBLEM STATEMENT ==========
    pdf.add_page()
    pdf.section_title("1", "Problem Statement")
    pdf.body_text(
        "Building AI agents is not a coding problem -- it is a decision problem. "
        "For every natural-language requirement, an engineer must make fifty or more "
        "interdependent technical decisions: how many sub-agents, what roles each plays, "
        "which tools to bind, what reasoning strategy to use, how to structure memory, "
        "how to handle failures, what architecture pattern fits the workflow."
    )
    pdf.body_text(
        "The tools and LLMs exist. The gap is not technology -- it is the translation layer "
        "between human intent and working agent architecture."
    )
    pdf.body_text(
        "Today, that translation is done manually by engineers who understand prompt design, "
        "tool orchestration, and agentic patterns. This concentrates AI agent development among "
        "a small number of practitioners and makes every new agent a weeks-long engineering effort."
    )
    pdf.sub_title("The Core Bottleneck")
    pdf.body_text(
        "There are more AI agent use cases than there are engineers to build them. A loan officer "
        "who wants an AI assistant to review applications must explain the process to an engineering "
        "team. That team spends weeks learning the domain, picking tools, writing code, testing, and "
        "fixing. A procurement manager wanting AI to score suppliers goes through the same cycle. "
        "Every new agent is a custom engineering project. It takes too long, costs too much, and most "
        "teams don't have the engineers to spare."
    )
    pdf.sub_title("The Question")
    pdf.body_text(
        "Can an AI system take over that translation entirely -- not by simplifying it, "
        "but by automating the decision-making itself?"
    )

    # ========== 2. SOLUTION OVERVIEW ==========
    pdf.add_page()
    pdf.section_title("2", "Solution Overview")
    pdf.body_text(
        "Frankenstein is a meta-agentic system: an AI system that builds other AI agent systems. "
        "The human describes a problem in plain language. Frankenstein asks the right questions to "
        "extract what it needs, designs the architecture, stress-tests it, builds it, runs it, "
        "and fixes what breaks."
    )
    pdf.body_text(
        "Building an agent requires two kinds of knowledge: domain knowledge (what the agent should do) "
        "and engineering knowledge (how to build it). Today, one person needs both. Frankenstein splits "
        "that burden -- the human provides domain expertise, Frankenstein provides the engineering."
    )
    pdf.sub_title("Six-Stage Pipeline")
    pdf.body_text("Frankenstein runs a six-stage LangGraph StateGraph pipeline:")
    stages = [
        ("Elicitor (gpt-4o-mini)", "Extracts domain knowledge from human via structured Q&A across 5 categories"),
        ("Architect (claude-sonnet-4-5)", "Generates framework-agnostic specification with agent roles, tools, memory, and flow"),
        ("Critic (gpt-4o)", "Adversarial spec review using 6 attack vectors; different model family on purpose"),
        ("Builder (claude-sonnet-4-5)", "Compiles validated spec into CrewAI or LangGraph code via plan-generate-validate-repair"),
        ("Tester (gpt-4o-mini)", "Runs agents in Docker sandbox, traces failures to spec-level root causes"),
        ("Learner (gpt-4o-mini)", "Stores build outcomes, patterns, and anti-patterns in Chroma for future RAG"),
    ]
    for i, (name, desc) in enumerate(stages, 1):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(8, 6, f"{i}.")
        pdf.cell(60, 6, name)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, f"- {desc}")
        pdf.ln(2)

    pdf.sub_title("Human-in-the-Loop")
    pdf.body_text(
        "Two human checkpoints: after requirements extraction (\"Is this what you meant?\") and "
        "after spec + critique review (\"Approve the blueprint?\"). The human validates, never writes code. "
        "Implemented via LangGraph's native interrupt() mechanism -- the graph pauses, WebSocket pushes "
        "the payload to the frontend, human reviews, and Command(resume=...) continues."
    )

    # ========== 3. USP ==========
    pdf.add_page()
    pdf.section_title("3", "Unique Selling Proposition (USP)")

    pdf.sub_title("Not One-Shot Generation")
    pdf.body_text(
        "Most approaches pass a prompt to an LLM and generate framework code. Frankenstein does not "
        "work this way. It runs the same process a senior engineering team would -- compressed into a "
        "multi-agent pipeline. A single LLM prompt can generate agent code, but it cannot:"
    )
    usps = [
        "Ask the human what's missing from their requirements",
        "Validate that selected tools actually support the required data formats",
        "Attack its own design for failure modes before building",
        "Run the generated code and trace failures back to architectural decisions",
        "Learn from previous builds to improve future ones",
    ]
    for u in usps:
        pdf.bullet(u)

    pdf.ln(3)
    pdf.sub_title("The Specification Layer")
    pdf.body_text(
        "The specification layer is the core innovation. It serves as both a trust mechanism -- "
        "users can inspect and validate the blueprint before anything is built -- and a quality gate "
        "that ensures depth in the output. Frankenstein does not trade power for ease. The interface "
        "is simple, but the output matches what an experienced engineer would produce."
    )

    pdf.sub_title("Cross-Model Adversarial Review")
    pdf.body_text(
        "The Architect (Claude Sonnet) and Critic (GPT-4o) deliberately use different model families. "
        "Cross-model adversarial review catches flaws that same-model review misses -- shared blind "
        "spots in one model family are exposed by the other."
    )

    pdf.sub_title("Self-Improving System")
    pdf.body_text(
        "The Learner agent stores success patterns, failure patterns, and anti-patterns after every "
        "build. Future builds query this memory via RAG. The system literally gets smarter with every build."
    )

    pdf.sub_title("Self-Healing Feedback Loops")
    pdf.body_text(
        "Three feedback loops enable autonomous correction: "
        "Architect <-> Critic (spec revisions until no critical findings), "
        "Builder -> Validate -> Repair (AST/import validation with up to 3 repair cycles), and "
        "Tester -> Builder or Architect (failure traces classify root cause level -- code bugs go "
        "back to Builder, spec bugs go back to Architect)."
    )

    # ========== 4. SYSTEM ARCHITECTURE ==========
    pdf.add_page()
    pdf.section_title("4", "System Architecture")

    pdf.sub_title("High-Level Architecture Diagram")
    pdf.code_block(
        "  Human                          Frankenstein\n"
        "  ------                         ------------\n"
        "\n"
        "  Fuzzy prompt ----------------> [1. ELICITOR AGENT]\n"
        "                                  Structured domain extraction\n"
        "                                  5 categories of targeted questions\n"
        "                                         |\n"
        "                                         v\n"
        "                                  Requirements Document\n"
        "                                         |\n"
        "  Human validates <------------- \"Is this what you meant?\"\n"
        "                                         |\n"
        "                                         v\n"
        "                                 [2. ARCHITECT AGENT]\n"
        "                                  RAG: past specs, tools, anti-patterns\n"
        "                                  8-step design process\n"
        "                                         |\n"
        "                                         v\n"
        "                                 [3. CRITIC AGENT]  <-- different model family\n"
        "                                  6 attack vectors\n"
        "                                  <-> loops to Architect until no criticals\n"
        "                                         |\n"
        "                                         v\n"
        "                                  Validated Spec + Critique Report\n"
        "                                         |\n"
        "  Human reviews <-------------- \"Approve blueprint?\"\n"
        "                                         |\n"
        "                                         v\n"
        "                                 [4. BUILDER AGENT]\n"
        "                                  Plan -> Generate -> Validate -> Repair\n"
        "                                         |\n"
        "                                         v\n"
        "                                 [5. TESTER AGENT]\n"
        "                                  Docker sandbox execution\n"
        "                                  root_cause: code -> Builder, spec -> Architect\n"
        "                                         |\n"
        "                                         v\n"
        "                                 [6. LEARNER AGENT]\n"
        "                                  Stores patterns in Chroma\n"
        "                                         |\n"
        "                                         v\n"
        "                                  END -- downloadable agent + Streamlit app"
    )

    pdf.ln(2)
    pdf.sub_title("Pipeline Orchestration")
    pdf.body_text(
        "Frankenstein itself is a LangGraph StateGraph. Each stage is a node. Edges define transitions. "
        "Conditional edges implement feedback loops. A single state object flows through the entire graph -- "
        "every node reads from it, does its work, writes back."
    )

    pdf.sub_title("Conditional Routing")
    pdf.body_text(
        "After Critique: if critical findings > 0 AND spec_iteration < max, route back to Architect. "
        "Otherwise, route to human review."
    )
    pdf.body_text(
        "After Testing: if all tests pass, route to Learner. If failure is code-level, route to Builder. "
        "If failure is spec-level, route to Architect. If max iterations reached, route to Learner with "
        "partial success flag."
    )

    # ========== 5. PIPELINE DEEP DIVE ==========
    pdf.add_page()
    pdf.section_title("5", "Pipeline Deep Dive")

    pdf.sub_title("5.1 Elicitor Agent")
    pdf.body_text(
        "Implementation: LangGraph subgraph with a loop. Runs gap analysis against 5 categories: "
        "Input/Output, Process, Data, Edge Cases, Quality Bar. Each category has a confidence score "
        "(0-1), loops until all >= 0.85. Maximum 3 rounds of questions -- flags remaining gaps as "
        "assumptions. Uses gpt-4o-mini for fast, interactive Q&A."
    )
    pdf.body_text(
        "Output: structured RequirementsDoc with typed fields including domain, inputs/outputs "
        "(DataSpec), process steps (ProcessStep), edge cases, quality criteria, and constraints."
    )

    pdf.sub_title("5.2 Architect Agent")
    pdf.body_text("8-step process using claude-sonnet-4-5:")
    arch_steps = [
        "RAG Query -- query Chroma for similar past specs, tools, and anti-patterns",
        "Task Decomposition -- break requirements into discrete computational tasks, tag each with capability type",
        "Tool Selection -- match each task to a tool from the library by format compatibility",
        "Agent Grouping -- related tasks grouped into same agent, independent chains become separate agents",
        "Execution Flow -- analyze dependencies, pick pattern (sequential/parallel/hierarchical/graph)",
        "Memory Design -- shared keys, strategy, persistence",
        "I/O Contracts -- per-agent input/output schemas with typed fields",
        "Pipeline I/O Contract -- how data enters and leaves the entire pipeline",
    ]
    for i, step in enumerate(arch_steps, 1):
        pdf.bullet(f"Step {i}: {step}")

    pdf.body_text(
        "The framework target is determined by flow design: graph patterns map to LangGraph, "
        "role delegation maps to CrewAI."
    )

    pdf.sub_title("5.3 Critic Agent")
    pdf.body_text(
        "Runs 6 attack vectors in parallel (5 programmatic + 1 LLM semantic), using gpt-4o:"
    )

    cols = ["Attack Vector", "What It Checks"]
    widths = [55, 135]
    pdf.table_header(cols, widths)
    rows = [
        ("Circular Dependencies", "Cycles in execution graph via topological sort"),
        ("Format Compatibility", "Agent A output matches Agent B input format"),
        ("Dependency Completeness", "Every agent receives all required fields from upstream"),
        ("Dead-End Analysis", "Agents that can fail without being caught"),
        ("Resource Conflicts", "Parallel agents writing same shared memory keys"),
        ("Tool + Semantic Review", "Tool capability match, coherence, reasoning strategy fit (LLM)"),
    ]
    for i, (v, c) in enumerate(rows):
        pdf.table_row([v, c], widths, fill=(i % 2 == 0))

    pdf.ln(4)
    pdf.body_text(
        "Output: CritiqueReport with findings scored as critical/warning/suggestion. "
        "Critical findings force Architect revision. Loop continues until no criticals remain (max 3 iterations)."
    )

    pdf.add_page()
    pdf.sub_title("5.4 Builder Agent")
    pdf.body_text("Multi-pass architecture using claude-sonnet-4-5:")
    builder_steps = [
        "PLAN -- LLM produces a BuildPlan (tool signatures, agent task templates, kickoff inputs) before writing code",
        "GENERATE -- code conforming to the plan, framework-specific (CrewAI or LangGraph)",
        "VALIDATE -- _validation.run_all() with 8+ AST-level checks",
        "REPAIR -- if validation fails, send errors + RAG-retrieved past repair patterns to LLM for targeted fix (up to 3 cycles)",
    ]
    for step in builder_steps:
        pdf.bullet(step)

    pdf.ln(2)
    pdf.sub_sub_title("Validation System (8+ AST-Level Checks)")
    cols2 = ["Code", "What It Catches"]
    widths2 = [55, 135]
    pdf.table_header(cols2, widths2)
    val_rows = [
        ("SYNTAX_ERROR", "File won't parse"),
        ("UNRESOLVED_SYMBOL", "Imports that don't exist"),
        ("PARAM_SHADOWS_PYDANTIC", "Params named schema, dict, json that break CrewAI"),
        ("TOOL_WRONG_ARITY", "Tool function doesn't follow def fn(data: dict) -> dict"),
        ("TOOL_HAS_DEFAULTS", "Default params break OpenAI strict schema"),
        ("KICKOFF_EMPTY_INPUTS", "crew.kickoff(inputs={}) guaranteed to fail"),
        ("ENTRY_POINT_MISSING_FIELD", "pipeline_input_schema fields not wired"),
        ("TOOL_NOT_DEFINED", "Referenced in agents.py but never implemented"),
    ]
    for i, (c, d) in enumerate(val_rows):
        pdf.table_row([c, d], widths2, fill=(i % 2 == 0))

    pdf.ln(4)
    pdf.sub_sub_title("Generated Project Structure")
    pdf.code_block(
        "generated_agent/\n"
        "+-- main.py              # entry point with env injection\n"
        "+-- agents.py            # agent definitions (roles, goals, backstories)\n"
        "+-- tools.py             # tool implementations (strict def fn(data:dict)->dict)\n"
        "+-- orchestration.py     # CrewAI crew or LangGraph graph definition\n"
        "+-- app.py               # Streamlit web UI\n"
        "+-- sample_data.json     # concrete test data matching pipeline_input_schema\n"
        "+-- requirements.txt     # Python dependencies\n"
        "+-- .env.example         # OPENROUTER_API_KEY=...\n"
        "+-- README.md            # prerequisites, setup, run command, I/O shape"
    )

    pdf.sub_title("5.5 Tester Agent")
    pdf.body_text("Execution pipeline using gpt-4o-mini:")
    tester_steps = [
        "Generate test cases from spec I/O contracts",
        "Static validation via _validation.run_all() (same checks as Builder)",
        "Live execution in Docker sandbox with real LLM calls via OpenRouter",
        "Output validation: parse stdout JSON, flag known failure signatures",
        "Rule-based failure classification (regex) for common patterns; LLM handles the rest",
    ]
    for step in tester_steps:
        pdf.bullet(step)

    pdf.ln(2)
    pdf.body_text(
        "Failure signatures detected: EMPTY_INPUTS, MISSING_API_KEY, STRICT_SCHEMA, IMPORT_ERROR, KEY_ERROR. "
        "Root cause routing: code-level loops to Builder, spec-level loops to Architect."
    )

    pdf.sub_title("5.6 Learner Agent")
    pdf.body_text("Stores after every build:")
    learner_items = [
        "BuildOutcome with requirements hash, spec snapshot, framework, tools used, test results",
        "success_patterns -- what worked well",
        "failure_patterns -- what went wrong this build",
        "anti_patterns -- generalized patterns to avoid",
        "lessons_learned -- domain-specific takeaways",
        "repair_patterns -- error->fix pairs from Builder repair history",
    ]
    for item in learner_items:
        pdf.bullet(item)
    pdf.body_text("Updates tool compatible_with/incompatible_with from real build results.")

    # ========== 6. TECHNOLOGY STACK ==========
    pdf.add_page()
    pdf.section_title("6", "Technology Stack")

    pdf.sub_title("Full Stack Overview")
    cols3 = ["Layer", "Technology", "Role"]
    widths3 = [40, 55, 95]
    pdf.table_header(cols3, widths3)
    stack_rows = [
        ("Pipeline", "LangGraph StateGraph", "Internal pipeline with conditional edges + SqliteSaver"),
        ("Backend", "FastAPI + Uvicorn", "API server, WebSocket management, Docker orchestration"),
        ("Frontend", "React + Vite + Tailwind", "Chat interface, spec review, code preview"),
        ("3D Graphics", "React Three Fiber", "Landing page with custom GLSL shaders + bloom"),
        ("LLM Routing", "OpenRouter", "Single API for all model access, model-per-agent"),
        ("Vector DB", "ChromaDB", "5 collections, persistent, RAG retrieval"),
        ("Execution", "Docker", "Pre-built base image, streaming execution"),
        ("State Mgmt", "Zustand", "Frontend state management"),
        ("Communication", "WebSockets", "3 channels: chat, status, preview"),
        ("Generated Output", "CrewAI / LangGraph", "Framework-specific agent projects + Streamlit app"),
    ]
    for i, (l, t, r) in enumerate(stack_rows):
        pdf.table_row([l, t, r], widths3, fill=(i % 2 == 0))

    pdf.ln(6)
    pdf.sub_title("Model-per-Agent Strategy")
    cols4 = ["Agent", "Model", "Reasoning"]
    widths4 = [35, 45, 110]
    pdf.table_header(cols4, widths4)
    model_rows = [
        ("Elicitor", "gpt-4o-mini", "Fast, cheap, good at structured Q&A"),
        ("Architect", "claude-sonnet-4-5", "Best at complex structured generation"),
        ("Critic", "gpt-4o", "Different family -- cross-model review catches blind spots"),
        ("Builder", "claude-sonnet-4-5", "Best at code generation with constraints"),
        ("Tester", "gpt-4o-mini", "Fast analysis, rule-based does heavy lifting"),
        ("Learner", "gpt-4o-mini", "Pattern extraction doesn't need frontier model"),
    ]
    for i, (a, m, r) in enumerate(model_rows):
        pdf.table_row([a, m, r], widths4, fill=(i % 2 == 0))

    # ========== 7. DATA MODELS ==========
    pdf.add_page()
    pdf.section_title("7", "Data Models & State Management")

    pdf.sub_title("Pipeline State Object")
    pdf.body_text(
        "A single FrankensteinState (TypedDict) flows through the entire graph. Every node reads "
        "from it, does its work, writes back. Key fields include:"
    )
    state_groups = [
        ("Elicitor Stage", "raw_prompt, session_id, elicitor_questions, human_answers, requirements (RequirementsDoc), requirements_approved"),
        ("Architect + Critic", "tool_library_matches, past_spec_matches, spec (AgentSpec), architect_reasoning, critique (CritiqueReport), spec_iteration, spec_approved"),
        ("Builder + Tester", "generated_code (CodeBundle), test_cases, test_results (TestReport), failure_traces, build_iteration, build_attempts, repair_history"),
        ("Learner", "build_outcome (BuildOutcome)"),
    ]
    for group, fields in state_groups:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 6, group)
        pdf.ln(6)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(0, 5, f"  {fields}")
        pdf.ln(3)

    pdf.sub_title("Key Pydantic Models")
    models_list = [
        "RequirementsDoc -- domain, inputs/outputs (DataSpec), process_steps, edge_cases, quality_criteria, constraints",
        "AgentSpec -- metadata, agents (with roles/goals/tools/reasoning_strategy), tools, memory, execution_flow, error_handling, io_contracts",
        "CritiqueReport -- findings (vector, severity, description, location, evidence, suggested_fix), summary",
        "CodeBundle -- generated project files with agents.py, tools.py, orchestration.py, main.py",
        "TestReport -- test results with pass/fail status per test case",
        "FailureTrace -- test_name, error_type, raw_error, failing_agent, root_cause_level, root_cause_analysis",
        "BuildOutcome -- requirements_hash, spec_snapshot, framework_used, success/failure/anti patterns",
    ]
    for m in models_list:
        pdf.bullet(m)

    # ========== 8. CHROMA ==========
    pdf.add_page()
    pdf.section_title("8", "Chroma Vector Memory Architecture")

    pdf.sub_title("5 Collections")
    cols5 = ["Collection", "Content", "Used By"]
    widths5 = [50, 80, 60]
    pdf.table_header(cols5, widths5)
    chroma_rows = [
        ("tool_schemas", "14 pre-seeded validated tool definitions", "Architect"),
        ("spec_patterns", "Past validated specs + outcomes", "Architect"),
        ("anti_patterns", "Patterns that caused failures", "Architect"),
        ("domain_insights", "Domain-specific learnings", "Elicitor"),
        ("builder_repair_patterns", "Error->fix pairs from past repairs", "Builder"),
    ]
    for i, (c, co, u) in enumerate(chroma_rows):
        pdf.table_row([c, co, u], widths5, fill=(i % 2 == 0))

    pdf.ln(6)
    pdf.sub_title("14 Pre-Seeded Tool Schemas")
    pdf.body_text(
        "Each tool schema includes: id, name, description, category, accepts/outputs formats, "
        "limitations, dependencies, code_template, and compatibility info."
    )
    cols6 = ["Tool", "Category"]
    widths6 = [70, 60]
    pdf.table_header(cols6, widths6)
    tool_rows = [
        ("pdf_parser_pymupdf", "Document extraction"),
        ("ocr_tesseract", "Document extraction"),
        ("csv_parser", "Data processing"),
        ("json_transformer", "Data processing"),
        ("file_reader", "Data processing"),
        ("financial_calculator", "Calculation"),
        ("statistical_analyzer", "Analysis"),
        ("scoring_engine", "Analysis"),
        ("rule_engine", "Reasoning"),
        ("llm_reasoner", "Reasoning"),
        ("report_generator", "Generation"),
        ("data_visualizer", "Generation"),
        ("web_search", "API call"),
        ("code_executor", "Execution"),
    ]
    for i, (t, c) in enumerate(tool_rows):
        pdf.table_row([t, c], widths6, fill=(i % 2 == 0))

    pdf.ln(4)
    pdf.sub_title("RAG Query Flow")
    pdf.body_text(
        "When Architect receives requirements: (1) Query spec_patterns for similar past specs -- "
        "use successful ones as structural reference. (2) For each task, query tool_schemas -- "
        "select based on format chain compatibility. (3) Query anti_patterns to avoid known failure modes."
    )

    # ========== 9. FRONTEND ==========
    pdf.add_page()
    pdf.section_title("9", "Frontend Architecture")

    pdf.sub_title("Landing Page (React Three Fiber + Custom GLSL)")
    landing_features = [
        "LaboratoryVoid: custom GLSL shader background with biological noise patterns",
        "OrganismFragments: 6 3D shapes representing agents with custom vertex displacement shaders, per-fragment particle trails, and assembly animation",
        "EnergyConnections: animated THREE.Line objects connecting agents with traveling pulse dots",
        "AssemblyAnimation: fragments pull -> stitch -> lightning -> heartbeat sequence (Zustand-driven)",
        "Bloom post-processing via @react-three/postprocessing",
        "TypewriterHeadline: animated text reveal",
    ]
    for f in landing_features:
        pdf.bullet(f)

    pdf.ln(2)
    pdf.sub_title("Chat Interface Components")
    chat_features = [
        "Real-time dual WebSocket (chat + status channels)",
        "QuestionGroupCard: renders elicitor questions with per-category grouping, AI-assist button",
        "RequirementsCard: human checkpoint 1 -- approve/edit requirements",
        "SpecReviewCard: human checkpoint 2 -- approve/feedback on blueprint with critique findings",
        "TypingIndicator: 18 shuffled cycling facts about architecture while pipeline runs",
        "PipelineSidebar: live stage tracker with active/done/pending states",
        "ActivityPill: real-time sub-step updates",
        "CodingScreen: animated terminal showing build progress",
        "CompletionCard: download button + build stats (time, files, tests, agents)",
    ]
    for f in chat_features:
        pdf.bullet(f)

    pdf.ln(2)
    pdf.sub_title("Preview System")
    preview_features = [
        "CodeViewer: syntax-highlighted file explorer for generated code",
        "ExecutionPanel: Docker streaming execution with agent trace log",
        "StreamlitPreview: embedded iframe for generated Streamlit app (live preview)",
        "SplitPane: resizable panels for code + execution side-by-side",
    ]
    for f in preview_features:
        pdf.bullet(f)

    # ========== 10. STREAMING ==========
    pdf.add_page()
    pdf.section_title("10", "Real-Time Streaming Architecture")

    pdf.sub_title("Queue-Based Node Streaming")
    pdf.body_text(
        "Post-approval pipeline (builder->tester->learner) runs graph.stream() in a thread. A queue "
        "bridge forwards node events to the async WebSocket consumer in real-time. Supports cycling -- "
        "Builder appearing multiple times in repair loops gets retry-specific activity messages."
    )

    pdf.sub_title("WebSocket Channels")
    cols7 = ["Path", "Purpose"]
    widths7 = [60, 130]
    pdf.table_header(cols7, widths7)
    ws_rows = [
        ("/ws/chat/{session_id}", "Bidirectional: user input, system messages, checkpoints"),
        ("/ws/status/{session_id}", "Server->client: stage updates, activity feed"),
        ("/ws/preview/{session_id}", "Server->client: Docker execution trace, run status"),
    ]
    for i, (p, pu) in enumerate(ws_rows):
        pdf.table_row([p, pu], widths7, fill=(i % 2 == 0))

    pdf.ln(4)
    pdf.sub_title("Docker Execution Environment")
    pdf.body_text(
        "Pre-built base image (frankenstein-runner) with Python 3.11 + CrewAI + LangGraph + common "
        "packages pre-installed. Generated code mounted at runtime. Container killed after timeout "
        "(60s default). Output captured via Docker SDK for validation."
    )

    # ========== 11. DEMO TARGETS ==========
    pdf.add_page()
    pdf.section_title("11", "Demo Targets & Validation")

    pdf.sub_title("PS-08: Loan Underwriting Co-Pilot")
    pdf.body_text(
        "Multi-agent pipeline for document extraction, financial ratio calculation, risk scoring, "
        "compliance checking, and report generation. Tools: pdf_parser_pymupdf, ocr_tesseract, "
        "financial_calculator, rule_engine, report_generator, web_search."
    )

    pdf.sub_title("PS-06: Supplier Reliability Scoring Agent")
    pdf.body_text(
        "Data aggregation, statistical analysis, scoring, and ranking pipeline. Tools: csv_parser, "
        "statistical_analyzer, scoring_engine, data_visualizer, report_generator."
    )

    pdf.sub_title("End-to-End Demo Flow")
    demo_steps = [
        "Open Frankenstein web app",
        "Type prompt describing the desired agent system",
        "Elicitor asks 3-5 targeted questions",
        "Review and approve generated requirements (Checkpoint 1)",
        "Review spec + critique report, approve blueprint (Checkpoint 2)",
        "Watch build + test happen with real-time progress",
        "Download working agent code + Streamlit app",
        "Run it. It works.",
    ]
    for i, step in enumerate(demo_steps, 1):
        pdf.bullet(f"{i}. {step}")

    pdf.body_text(
        "\nBoth demo targets run end-to-end: prompt -> elicitor questions -> requirements -> "
        "architect design -> critic review -> builder code -> tester execution -> learner storage -> "
        "downloadable project + Streamlit app."
    )

    # ========== 12. CHALLENGES ==========
    pdf.add_page()
    pdf.section_title("12", "Challenges Solved")

    challenges = [
        ("Empty Elicitor Interrupt (Dead State Bug)",
         "Elicitor round 2 generated 0 questions (all gaps scored >= 0.85) but still called interrupt() "
         "with empty payload. Frontend got empty question group, set isWorking=false, no loader, dead state. "
         "Fix: added early return with elicitor_all_complete=True when no questions generated."),
        ("WebSocket Disconnection at Builder Stage",
         "Builder writes files to generated_agents/, uvicorn's --reload file watcher detects changes, "
         "restarts server, kills all WebSocket connections mid-pipeline. "
         "Fix: --reload-exclude 'generated_agents/*' --reload-exclude 'chroma_data/*'"),
        ("Vite HMR WebSocket Collision",
         "Broad /ws proxy in vite.config.ts caught Vite's own HMR WebSocket -> 'send before connect' errors. "
         "Fix: narrowed proxy to specific paths: /ws/chat, /ws/status, /ws/preview"),
        ("Real-Time Streaming for Post-Approval Pipeline",
         "Original implementation collected all stream events after completion, so no real-time updates "
         "during the longest part. Fix: queue-based bridge so graph.stream() pushes node events to async "
         "consumer for immediate WebSocket dispatch."),
        ("Builder Targeted Repair from Test Failures",
         "Rebuilding after test failures regenerated everything from scratch, hitting the same validation "
         "errors. Fix: when previous code passed validation, Builder does targeted repair from failure "
         "traces instead of full regeneration."),
        ("Streamlit App Generation + Live Preview",
         "Generated agents were CLI-only with no visual interface. Fix: Builder generates app.py "
         "(Streamlit web UI), StreamlitService launches it in Docker, frontend embeds via iframe."),
    ]
    for title, desc in challenges:
        pdf.sub_sub_title(title)
        pdf.body_text(desc)

    # ========== 13. SCOPE ==========
    pdf.add_page()
    pdf.section_title("13", "Scope & Limitations")

    pdf.body_text("Clarity on what Frankenstein does not do:")
    limitations = [
        "Does not understand domains autonomously -- relies on the human for domain knowledge. Frankenstein is the engineering team, not the product manager.",
        "Does not replace prompt engineering entirely -- the Elicitor improves input quality, but garbage domain knowledge in still produces garbage agents out.",
        "Does not guarantee perfect agents on first pass -- the test-and-fix loop exists because first builds will have issues. The system's strength is autonomous correction, not perfection.",
        "Does not work without a Tool Schema Library -- the Architect can only select tools it knows about. An empty library means no useful output.",
    ]
    for l in limitations:
        pdf.bullet(l)

    # ========== 14. CONCLUSION ==========
    pdf.ln(8)
    pdf.section_title("14", "Conclusion")

    pdf.body_text(
        "Frankenstein demonstrates that the translation from human intent to working AI agent systems "
        "can be fully automated. By splitting the process into specialized agents -- each handling a "
        "distinct phase of the engineering workflow -- the system achieves what no single LLM call can: "
        "iterative requirements extraction, adversarial design review, template-driven code generation, "
        "sandboxed testing with root-cause analysis, and continuous learning."
    )
    pdf.body_text(
        "The system collapses the expertise and time required to deploy agentic solutions from weeks "
        "to minutes. A domain expert in manufacturing, finance, or compliance can describe a workflow "
        "in plain language and receive a production-grade multi-agent system -- tested and ready."
    )
    pdf.body_text(
        "By automating the full arc from intent to tested agents, Frankenstein removes the people "
        "bottleneck that currently limits AI agent adoption across industries."
    )

    # Output
    output_path = os.path.join(os.path.dirname(__file__), "Frankenstein_Project_Report.pdf")
    pdf.output(output_path)
    print(f"Report generated: {output_path}")
    return output_path


if __name__ == "__main__":
    build_report()
