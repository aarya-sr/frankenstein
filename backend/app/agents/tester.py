"""Tester agent — runs generated code against real LLM, traces failures.

Hardened pipeline:
  1. Generate test cases (LLM, for the report only — actual execution uses sample_input).
  2. Static validation via _validation.run_all (same checks the Builder uses).
  3. LIVE execution: write sample_data.json + .env into the runner image,
     inject OPENROUTER_API_KEY → OPENAI_API_KEY, enable network, run main.py.
  4. Output validation: parse stdout JSON, flag known failure signatures.
  5. Rule-based failure classification (regex) for common error patterns;
     LLM only handles what the rules don't catch.
"""

import json
import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path

from app.agents import _validation
from app.config import settings
from app.models.code import CodeBundle
from app.models.spec import AgentSpec
from app.models.state import FrankensteinState
from app.models.testing import FailureTrace, TestCase, TestReport, TestResult
from app.services.docker_service import DockerService, ExecutionResult
from app.services.llm_service import LLMService, extract_json

logger = logging.getLogger(__name__)

AGENT_NAME = "tester"


TEST_GENERATION_SYSTEM = """\
You are the Tester generating test cases. Return JSON: {"test_cases": [...]}
Each: name, description, input_data, expected_output_schema, quality_checks, timeout.
"""

FAILURE_ANALYSIS_SYSTEM = """\
You are the Tester analysing failures the rule-based classifier could not categorize.

For each failure, determine:
- test_name
- error_type: crash | wrong_output | missing_field | quality_fail
- raw_error
- failing_agent
- root_cause_level: "code" (loop to Builder) | "spec" (loop to Architect)
- root_cause_analysis (1-2 sentences)
- spec_decision_responsible
- suggested_fix

Return JSON: {"failure_traces": [...]}"""


# ── Public entry point ────────────────────────────────────────────────


def tester_agent(
    state: FrankensteinState,
    *,
    llm: LLMService | None = None,
    docker: DockerService | None = None,
) -> dict:
    from app.services.llm_service import LLMService as _LS
    if llm is None:
        llm = _LS()
    if docker is None:
        docker = DockerService()

    spec: AgentSpec = state["spec"]
    code: CodeBundle = state["generated_code"]
    session_id = state.get("session_id", "?")
    logger.info("[%s] Tester: START — validating '%s' (%d files: %s)",
                session_id, spec.metadata.name, len(code.files), list(code.files.keys()))

    logger.info("[%s] Tester: generating test cases...", session_id)
    test_cases = _generate_test_cases(llm, spec, code)
    logger.info("[%s] Tester: generated %d test cases", session_id, len(test_cases))

    # Static validation (same as Builder's)
    logger.info("[%s] Tester: running static validation...", session_id)
    static_errors = _validation.run_all(code.files, spec=spec, framework=spec.metadata.framework_target)
    syntax_errors = [e for e in static_errors if e.get("code") == "SYNTAX_ERROR"]
    other_static = [e for e in static_errors if e.get("code") != "SYNTAX_ERROR"]
    logger.info("[%s] Tester: static validation — %d syntax errors, %d other issues",
                session_id, len(syntax_errors), len(other_static))

    # Execute live
    exec_result: ExecutionResult | None = None
    if syntax_errors:
        logger.info("[%s] Tester: SKIPPING execution — syntax errors found", session_id)
    else:
        env = _build_env(spec)
        live = settings.tester_live_execution and bool(os.getenv("OPENROUTER_API_KEY"))
        if docker.available and docker.image_exists():
            logger.info("[%s] Tester: running in Docker (live=%s, network=%s)", session_id, live, live)
            exec_result = docker.run_code_bundle(
                code,
                env=env,
                network_disabled=not live,
                timeout=settings.docker_timeout * 2 if live else settings.docker_timeout,
            )
            logger.info("[%s] Tester: Docker execution done — exit_code=%s, timed_out=%s",
                        session_id,
                        exec_result.exit_code if exec_result else "N/A",
                        exec_result.timed_out if exec_result else "N/A")
        else:
            logger.info("[%s] Tester: Docker unavailable — subprocess fallback (live=%s)", session_id, live)
            exec_result = _run_subprocess(code, env, settings.docker_timeout * 2 if live else settings.docker_timeout)
            logger.info("[%s] Tester: subprocess done — exit_code=%s", session_id, exec_result.exit_code if exec_result else "N/A")

    # Build results
    results: list[TestResult] = []
    all_errors: list[dict] = list(other_static)
    failed_files: set[str] = set()
    for err in syntax_errors:
        failed_files.add(err.get("file", ""))
        all_errors.append(err)
        results.append(TestResult(
            test_name=f"syntax_{err.get('file', '?')}",
            status="failed",
            stderr=err.get("message", ""),
            validation_details=err.get("fix", ""),
        ))

    for issue in other_static:
        sev = issue.get("severity", "warning")
        status = "failed" if sev == "error" else "passed"
        results.append(TestResult(
            test_name=f"{issue.get('code', 'static')}_{issue.get('file', '?')}",
            status=status,
            stderr=issue.get("message", ""),
            validation_details=issue.get("fix", ""),
        ))

    if exec_result is not None:
        _evaluate_execution(exec_result, spec, results, all_errors, code)

    # Pass-through for clean files
    for fname in code.files:
        if fname.endswith(".py") and fname not in failed_files:
            results.append(TestResult(test_name=f"syntax_{fname}", status="passed"))

    n_failed = sum(1 for r in results if r.status == "failed")
    n_errors = sum(1 for r in results if r.status == "error")
    all_passed = n_failed == 0 and n_errors == 0

    report = TestReport(
        total=len(results),
        passed=sum(1 for r in results if r.status == "passed"),
        failed=n_failed,
        errors=n_errors,
        all_passed=all_passed,
        results=results,
    )

    logger.info("[%s] Tester: results — total=%d, passed=%d, failed=%d, errors=%d, all_passed=%s",
                session_id, len(results), sum(1 for r in results if r.status == "passed"),
                n_failed, n_errors, all_passed)

    # Failure tracing
    failure_traces: list[FailureTrace] = []
    if not all_passed:
        logger.info("[%s] Tester: classifying failures...", session_id)
        rule_traces, unclassified = _classify_failures_rules(all_errors, exec_result, spec)
        failure_traces.extend(rule_traces)
        if unclassified:
            logger.info("[%s] Tester: %d unclassified errors, using LLM fallback", session_id, len(unclassified))
            failure_traces.extend(_trace_failures_llm(llm, spec, code, unclassified))
        logger.info("[%s] Tester: %d failure traces (%d rule-based)", session_id, len(failure_traces), len(rule_traces))
    else:
        logger.info("[%s] Tester: ALL CHECKS PASSED", session_id)

    logger.info("[%s] Tester: DONE", session_id)
    return {
        "test_cases": test_cases,
        "test_results": report,
        "failure_traces": failure_traces,
        "build_iteration": state.get("build_iteration", 0) + 1,
    }


# ── Env injection ─────────────────────────────────────────────────────


def _build_env(spec: AgentSpec) -> dict[str, str]:
    """OPENROUTER_API_KEY → OPENAI_*, plus test model."""
    env: dict[str, str] = {}
    key = os.getenv("OPENROUTER_API_KEY", "")
    if key:
        env["OPENAI_API_KEY"] = key
        env["OPENROUTER_API_KEY"] = key
        env["OPENAI_BASE_URL"] = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        env["OPENAI_MODEL_NAME"] = settings.tester_test_model
    return env


# ── Execution result evaluation ───────────────────────────────────────


def _evaluate_execution(
    exec_result: ExecutionResult,
    spec: AgentSpec,
    results: list[TestResult],
    all_errors: list[dict],
    code: CodeBundle,
) -> None:
    """Inspect exec result; append TestResults + error dicts for classifier."""
    if exec_result.timed_out:
        results.append(TestResult(
            test_name="live_execution",
            status="failed",
            stderr=exec_result.error,
            stdout=exec_result.stdout,
            validation_details=f"Execution timed out: {exec_result.error}",
        ))
        all_errors.append({
            "code": "EXECUTION_TIMEOUT",
            "file": code.entry_point,
            "severity": "error",
            "message": exec_result.error,
            "fix": "Reduce LLM call count, simplify task descriptions, or raise docker_timeout",
        })
        return

    if exec_result.exit_code != 0:
        results.append(TestResult(
            test_name="live_execution",
            status="failed",
            stderr=exec_result.stderr,
            stdout=exec_result.stdout,
            validation_details=f"Exit code {exec_result.exit_code}",
        ))
        all_errors.append({
            "code": "RUNTIME_ERROR",
            "file": code.entry_point,
            "severity": "error",
            "message": exec_result.stderr[-2000:],
            "stdout": exec_result.stdout[-1000:],
            "fix": "Inspect traceback in stderr",
        })
        return

    # Zero exit code — but check for known failure signatures in stdout
    sig_errors = _detect_output_signatures(exec_result.stdout, spec)
    if sig_errors:
        for e in sig_errors:
            results.append(TestResult(
                test_name=f"output_{e['code']}",
                status="failed",
                stdout=exec_result.stdout,
                validation_details=e["message"],
            ))
            all_errors.append(e)
        return

    results.append(TestResult(
        test_name="live_execution",
        status="passed",
        stdout=exec_result.stdout,
        validation_details="Pipeline executed end-to-end and produced output",
    ))


_FAILURE_SIGNATURES = [
    (re.compile(r"no documents provided", re.I), "EMPTY_INPUTS",
     "Agent ran but received no input data — kickoff(inputs=...) was likely empty"),
    (re.compile(r"OPENAI_API_KEY is required", re.I), "MISSING_API_KEY",
     "Code did not get OPENAI_API_KEY — env injection issue"),
    (re.compile(r"additionalProperties|Invalid schema for function|strict.*True", re.I), "STRICT_SCHEMA",
     "Tool function signature breaks OpenAI strict schema (default params or shadowed names)"),
    (re.compile(r"ImportError: cannot import name '(\w+)'", re.I), "IMPORT_ERROR",
     "Code references a symbol that wasn't generated"),
    (re.compile(r"KeyError: ['\"]([^'\"]+)['\"]", re.I), "KEY_ERROR",
     "Pipeline tried to read a field not present in input dict"),
]


def _detect_output_signatures(stdout: str, spec: AgentSpec) -> list[dict]:
    """Scan stdout for known failure substrings."""
    found: list[dict] = []
    for pattern, code, message in _FAILURE_SIGNATURES:
        if pattern.search(stdout):
            found.append({
                "code": code,
                "file": "<runtime>",
                "severity": "error",
                "message": f"{message}: '{pattern.pattern}' matched in output",
                "stdout_excerpt": stdout[-1000:],
            })
    return found


# ── Rule-based failure classifier ─────────────────────────────────────


_CLASSIFIER_RULES = [
    (
        re.compile(r"ImportError: cannot import name ['\"](\w+)['\"]"),
        lambda m: {
            "error_type": "crash",
            "failing_agent": "builder",
            "root_cause_level": "code",
            "root_cause_analysis": f"Builder imported '{m.group(1)}' but never defined it.",
            "spec_decision_responsible": "tools list incomplete or builder omitted a function",
            "suggested_fix": f"Add `def {m.group(1)}(data: dict) -> dict:` to tools.py",
        },
    ),
    (
        re.compile(r"OPENAI_API_KEY is required", re.I),
        lambda m: {
            "error_type": "crash",
            "failing_agent": "runtime",
            "root_cause_level": "code",
            "root_cause_analysis": "main.py did not propagate OPENROUTER_API_KEY to OPENAI_API_KEY",
            "spec_decision_responsible": "main.py env-injection block missing",
            "suggested_fix": "In main.py, copy OPENROUTER_API_KEY to OPENAI_API_KEY before calling kickoff()",
        },
    ),
    (
        re.compile(r"additionalProperties|Invalid schema for function|'strict':\s*True", re.I),
        lambda m: {
            "error_type": "crash",
            "failing_agent": "tools",
            "root_cause_level": "code",
            "root_cause_analysis": "A tool function has params with defaults or shadowed names — breaks OpenAI strict schema",
            "spec_decision_responsible": "tools.py @tool function signature",
            "suggested_fix": "Refactor all @tool functions to single `data: dict` parameter, return dict",
        },
    ),
    (
        re.compile(r"KeyError: ['\"]([^'\"]+)['\"]"),
        lambda m: {
            "error_type": "missing_field",
            "failing_agent": "pipeline",
            "root_cause_level": "spec",
            "root_cause_analysis": f"Field '{m.group(1)}' missing from pipeline_input_schema or upstream output",
            "spec_decision_responsible": "pipeline_input_schema / agent io_contract",
            "suggested_fix": f"Add '{m.group(1)}' to pipeline_input_schema OR remove the dependency",
        },
    ),
    (
        re.compile(r"no documents provided", re.I),
        lambda m: {
            "error_type": "wrong_output",
            "failing_agent": "first_agent",
            "root_cause_level": "code",
            "root_cause_analysis": "Agents ran but kickoff(inputs=...) was empty — sample data not wired",
            "spec_decision_responsible": "main.py kickoff wiring",
            "suggested_fix": "Load sample_data.json and pass to kickoff(inputs=...)",
        },
    ),
]


def _classify_failures_rules(
    errors: list[dict],
    exec_result: ExecutionResult | None,
    spec: AgentSpec,
) -> tuple[list[FailureTrace], list[dict]]:
    """Apply regex rules to error messages + stderr/stdout. Return (classified, unclassified)."""
    classified: list[FailureTrace] = []
    unclassified: list[dict] = []
    haystack_parts = []
    for e in errors:
        haystack_parts.append(str(e.get("message", "")))
        haystack_parts.append(str(e.get("stdout_excerpt", "")))
    if exec_result:
        haystack_parts.append(exec_result.stdout or "")
        haystack_parts.append(exec_result.stderr or "")
    haystack = "\n".join(haystack_parts)

    matched_codes: set[str] = set()
    for pattern, builder in _CLASSIFIER_RULES:
        m = pattern.search(haystack)
        if m:
            data = builder(m)
            trace_key = f"{data['error_type']}:{data['suggested_fix'][:40]}"
            if trace_key in matched_codes:
                continue
            matched_codes.add(trace_key)
            classified.append(FailureTrace(
                test_name=f"rule_match_{data['error_type']}",
                raw_error=m.group(0),
                **data,
            ))

    # Unclassified = errors we have not produced any trace for
    if not classified and errors:
        unclassified.extend(errors)

    return classified, unclassified


# ── LLM fallback failure tracing ──────────────────────────────────────


def _trace_failures_llm(
    llm: LLMService, spec: AgentSpec, code: CodeBundle, errors: list[dict]
) -> list[FailureTrace]:
    user_msg = (
        f"## AgentSpec\n\n{spec.model_dump_json(indent=2)}"
        f"\n\n## Generated Code\n\n{json.dumps(code.files, indent=2)}"
        f"\n\n## Unclassified Errors\n\n{json.dumps(errors, indent=2)}"
    )
    response = llm.call(
        agent_name=AGENT_NAME,
        system_prompt=FAILURE_ANALYSIS_SYSTEM,
        user_prompt=user_msg,
        json_mode=True,
        temperature=0.1,
    )
    try:
        data = json.loads(extract_json(response))
        return [FailureTrace(**ft) for ft in data.get("failure_traces", [])]
    except (json.JSONDecodeError, Exception) as e:
        logger.error("Tester: LLM failure trace parse failed: %s", e)
        return [FailureTrace(
            test_name="parse_failure",
            error_type="crash",
            raw_error=str(e),
            failing_agent="unknown",
            root_cause_level="code",
            root_cause_analysis="Failure trace generation itself failed",
            spec_decision_responsible="N/A",
            suggested_fix="Inspect logs",
        )]


# ── Test case generation (LLM, report-only) ───────────────────────────


def _generate_test_cases(llm, spec, code):
    code_summary = {}
    for fname, content in code.files.items():
        lines = content.split("\n")
        code_summary[fname] = "\n".join(lines[:30]) + ("\n... (truncated)" if len(lines) > 30 else "")

    user_msg = (
        f"## AgentSpec\n\n{spec.model_dump_json(indent=2)}"
        f"\n\n## Generated Code (summary)\n\n{json.dumps(code_summary, indent=2)}"
    )
    response = llm.call(
        agent_name=AGENT_NAME,
        system_prompt=TEST_GENERATION_SYSTEM,
        user_prompt=user_msg,
        json_mode=True,
        temperature=0.2,
    )
    try:
        data = json.loads(extract_json(response))
        return [TestCase(**tc) for tc in data.get("test_cases", [])]
    except Exception as e:
        logger.error("Tester: test generation parse failed: %s", e)
        return []


# ── Subprocess fallback (with env injection) ──────────────────────────


def _run_subprocess(code: CodeBundle, env: dict[str, str], timeout: int) -> ExecutionResult:
    tmp_dir = None
    try:
        tmp_dir = tempfile.mkdtemp(prefix="frank_test_")
        tmp_path = Path(tmp_dir)
        for fname, content in code.files.items():
            fpath = tmp_path / fname
            fpath.parent.mkdir(parents=True, exist_ok=True)
            fpath.write_text(content, encoding="utf-8")

        # Best-effort: install requirements.txt into current python
        req = tmp_path / "requirements.txt"
        if req.exists():
            try:
                subprocess.run(
                    ["pip", "install", "-q", "-r", str(req)],
                    capture_output=True, text=True, timeout=180,
                )
            except Exception as e:
                logger.warning("Subprocess fallback: pip install failed: %s", e)

        merged_env = dict(os.environ)
        merged_env.update(env or {})

        result = subprocess.run(
            ["python", code.entry_point],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=merged_env,
        )
        return ExecutionResult(
            exit_code=result.returncode,
            stdout=result.stdout[:5000],
            stderr=result.stderr[:5000],
            timed_out=False,
            error="",
        )
    except subprocess.TimeoutExpired:
        return ExecutionResult(exit_code=-1, stdout="", stderr="", timed_out=True,
                               error=f"Subprocess timed out after {timeout}s")
    except Exception as e:
        return ExecutionResult(exit_code=-1, stdout="", stderr="", timed_out=False,
                               error=f"Subprocess error: {e}")
    finally:
        if tmp_dir:
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)
