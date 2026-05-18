"""Shared validators for generated code bundles.

Used by Builder (self-repair loop) and Tester (sanity checks).
All validators take a `files: dict[str, str]` mapping filename → source code
and return a list of error dicts:

    {"file": str, "severity": "error"|"warning", "code": str, "message": str, "fix": str}

`code` is a stable identifier (e.g. ``UNRESOLVED_SYMBOL``) the repair loop can
match on. `fix` is a one-line, actionable hint the repair LLM can act on.
"""

from __future__ import annotations

import ast
import keyword
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


# ── Names that break CrewAI/pydantic tool wrappers when used as parameters ──
PYDANTIC_RESERVED = {
    "schema",
    "dict",
    "json",
    "copy",
    "parse_obj",
    "parse_raw",
    "validate",
    "construct",
    "fields",
    "model_dump",
    "model_dump_json",
    "model_fields",
    "model_config",
    "model_validate",
    "model_construct",
    "model_copy",
}


def _make(file: str, code: str, message: str, *, fix: str = "", severity: str = "error") -> dict:
    return {
        "file": file,
        "severity": severity,
        "code": code,
        "message": message,
        "fix": fix or message,
    }


# ── Helpers ─────────────────────────────────────────────────────────────────


def _parse(file: str, source: str) -> ast.Module | None:
    """Parse a python source file, returning None on syntax error."""
    try:
        return ast.parse(source, filename=file)
    except SyntaxError:
        return None


def _top_level_names(tree: ast.Module) -> set[str]:
    """Collect names defined at module top level (functions, classes, assignments)."""
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    names.add(t.id)
                elif isinstance(t, ast.Tuple):
                    for elt in t.elts:
                        if isinstance(elt, ast.Name):
                            names.add(elt.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname or alias.name)
    return names


# ── Validator 1: import & symbol resolution ─────────────────────────────────


def validate_imports_ast(files: dict[str, str]) -> list[dict]:
    """Verify every ``from <local_module> import <symbol>`` resolves.

    Catches the failure mode where Builder references a tool symbol in agents.py
    but never generates a corresponding function in tools.py.
    """
    errors: list[dict] = []

    # Build map of local module → set of top-level names defined.
    local_modules: dict[str, set[str]] = {}
    for fname, src in files.items():
        if not fname.endswith(".py"):
            continue
        mod_name = fname.removesuffix(".py").replace("/", ".")
        tree = _parse(fname, src)
        if tree is None:
            continue
        local_modules[mod_name] = _top_level_names(tree)

    for fname, src in files.items():
        if not fname.endswith(".py"):
            continue
        tree = _parse(fname, src)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.module is None or node.level:
                continue
            top = node.module.split(".")[0]
            if top not in local_modules:
                continue
            available = local_modules[top]
            for alias in node.names:
                if alias.name == "*":
                    continue
                if alias.name not in available:
                    errors.append(
                        _make(
                            fname,
                            "UNRESOLVED_SYMBOL",
                            f"'{alias.name}' is imported from '{node.module}' but not defined there",
                            fix=(
                                f"Either define '{alias.name}' in {node.module}.py "
                                f"or remove the import from {fname}"
                            ),
                        )
                    )
    return errors


# ── Validator 2: tool parameter safety ──────────────────────────────────────


_TOOL_DECORATORS = {"tool"}  # CrewAI: @tool("Name")


def _is_tool_decorated(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for dec in func.decorator_list:
        # @tool(...)
        if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and dec.func.id in _TOOL_DECORATORS:
            return True
        # @tool
        if isinstance(dec, ast.Name) and dec.id in _TOOL_DECORATORS:
            return True
        # @crewai.tools.tool(...)
        if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr in _TOOL_DECORATORS:
            return True
        if isinstance(dec, ast.Attribute) and dec.attr in _TOOL_DECORATORS:
            return True
    return False


def validate_tool_param_safety(files: dict[str, str]) -> list[dict]:
    """Flag tool function params that shadow pydantic or use Python keywords."""
    errors: list[dict] = []
    for fname, src in files.items():
        if not fname.endswith(".py"):
            continue
        tree = _parse(fname, src)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for arg in [*node.args.args, *node.args.kwonlyargs]:
                name = arg.arg
                if name in PYDANTIC_RESERVED:
                    errors.append(
                        _make(
                            fname,
                            "PARAM_SHADOWS_PYDANTIC",
                            f"Function '{node.name}' parameter '{name}' shadows a pydantic BaseModel attribute",
                            fix=(
                                f"Rename '{name}' (e.g. to '{name}_'). Pydantic-derived schemas "
                                f"break when tool params share names with BaseModel methods."
                            ),
                        )
                    )
                elif keyword.iskeyword(name):
                    errors.append(
                        _make(
                            fname,
                            "PARAM_IS_KEYWORD",
                            f"Function '{node.name}' parameter '{name}' is a Python keyword",
                            fix=f"Rename '{name}'.",
                        )
                    )
    return errors


# ── Validator 3: CrewAI strict-schema convention ────────────────────────────


def validate_crewai_tool_schema(files: dict[str, str]) -> list[dict]:
    """For CrewAI builds, enforce: every @tool fn takes exactly one annotated
    ``data: dict`` parameter and returns a dict-like value. This sidesteps the
    OpenAI strict-schema problems that surface via OpenRouter (defaults stripped,
    additionalProperties=False with required mismatch, etc.).
    """
    errors: list[dict] = []
    for fname, src in files.items():
        if not fname.endswith(".py"):
            continue
        tree = _parse(fname, src)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not _is_tool_decorated(node):
                continue

            args = node.args
            if args.vararg or args.kwarg:
                errors.append(
                    _make(
                        fname,
                        "TOOL_HAS_VARARGS",
                        f"@tool '{node.name}' uses *args/**kwargs",
                        fix="Use a single 'data: dict' parameter instead.",
                    )
                )
            positional = args.args
            if len(positional) != 1 or args.kwonlyargs:
                errors.append(
                    _make(
                        fname,
                        "TOOL_WRONG_ARITY",
                        f"@tool '{node.name}' must take exactly one parameter named 'data'",
                        fix=(
                            "Refactor to `def "
                            f"{node.name}(data: dict) -> dict:` and read sub-fields from `data`."
                        ),
                    )
                )
                continue
            param = positional[0]
            if param.arg != "data":
                errors.append(
                    _make(
                        fname,
                        "TOOL_PARAM_NOT_DATA",
                        f"@tool '{node.name}' parameter is '{param.arg}', expected 'data'",
                        fix=f"Rename the parameter to 'data'.",
                    )
                )
            if args.defaults:
                errors.append(
                    _make(
                        fname,
                        "TOOL_HAS_DEFAULTS",
                        f"@tool '{node.name}' has default parameter values",
                        fix=(
                            "Remove defaults. OpenAI strict schema marks every param required. "
                            "Pull values out of `data` dict inside the function body."
                        ),
                    )
                )
    return errors


# ── Validator 4: entry-point wiring ─────────────────────────────────────────


_KICKOFF_INPUTS_RE = re.compile(r"kickoff\s*\(\s*inputs\s*=\s*(\{[^{}]*\}|[A-Za-z_][\w]*)", re.DOTALL)
_INVOKE_RE = re.compile(r"\.invoke\s*\(\s*([^)]+)\)", re.DOTALL)


def validate_entry_point_wiring(files: dict[str, str], spec: Any) -> list[dict]:
    """Verify ``main.py`` actually passes pipeline inputs to the framework.

    Looks at ``spec.pipeline_input_schema.fields`` (new field) — if any field is
    declared but never referenced in main.py / orchestration.py, flag it.
    """
    errors: list[dict] = []

    pipeline_schema = getattr(spec.metadata, "pipeline_input_schema", None) or getattr(
        spec, "pipeline_input_schema", None
    )
    if not pipeline_schema:
        return errors

    required_fields = [
        f.name for f in getattr(pipeline_schema, "fields", []) if getattr(f, "required", True)
    ]
    if not required_fields:
        return errors

    main = files.get("main.py", "")
    orch = files.get("orchestration.py", "")
    if not main:
        errors.append(
            _make(
                "main.py",
                "MAIN_MISSING",
                "main.py not present in generated bundle",
                fix="Generate a main.py that loads sample input and invokes the pipeline.",
            )
        )
        return errors

    combined = main + "\n" + orch

    if "kickoff(inputs=" in main.replace(" ", "") and "kickoff(inputs={})" in main.replace(" ", ""):
        errors.append(
            _make(
                "main.py",
                "EMPTY_KICKOFF_INPUTS",
                "main.py calls crew.kickoff(inputs={}) with no data",
                fix=(
                    "Load sample_data.json (or spec.sample_input) and pass each pipeline_input_schema "
                    "field as a key in inputs={}."
                ),
            )
        )

    if ".invoke({})" in main.replace(" ", ""):
        errors.append(
            _make(
                "main.py",
                "EMPTY_GRAPH_INVOKE",
                "main.py calls graph.invoke({}) with no input data",
                fix="Pass the sample_input dict to graph.invoke().",
            )
        )

    for field in required_fields:
        if field not in combined:
            errors.append(
                _make(
                    "main.py",
                    "PIPELINE_INPUT_NOT_WIRED",
                    f"Required pipeline input '{field}' is never referenced in main.py/orchestration.py",
                    fix=(
                        f"Reference '{field}' in kickoff(inputs={{...}}) "
                        f"and in the relevant Task description as '{{{field}}}'."
                    ),
                )
            )
    return errors


# ── Validator 5: tool coverage ──────────────────────────────────────────────


def validate_tool_coverage(files: dict[str, str], spec: Any) -> list[dict]:
    """Every tool referenced by an agent must be defined in tools.py."""
    errors: list[dict] = []
    tools_src = files.get("tools.py", "")
    if not tools_src:
        return errors
    tree = _parse("tools.py", tools_src)
    if tree is None:
        return errors

    defined: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined.add(node.name)

    # Check agents.py for symbols imported from tools — these MUST exist
    referenced: set[str] = set()
    agents_src = files.get("agents.py", "")
    if agents_src:
        agents_tree = _parse("agents.py", agents_src)
        if agents_tree is not None:
            for node in ast.walk(agents_tree):
                if isinstance(node, ast.ImportFrom) and (node.module or "") == "tools":
                    for alias in node.names:
                        if alias.name != "*":
                            referenced.add(alias.name)

    for name in sorted(referenced):
        if name not in defined:
            errors.append(
                _make(
                    "tools.py",
                    "TOOL_NOT_DEFINED",
                    f"Tool '{name}' is imported in agents.py but not defined in tools.py",
                    fix=f"Add a `def {name}(data: dict) -> dict:` implementation in tools.py.",
                )
            )

    return errors


# ── Validator 6: syntax (compile) ───────────────────────────────────────────


def validate_syntax(files: dict[str, str]) -> list[dict]:
    """py_compile-style syntax check via ast.parse."""
    errors: list[dict] = []
    for fname, src in files.items():
        if not fname.endswith(".py"):
            continue
        try:
            ast.parse(src, filename=fname)
        except SyntaxError as e:
            errors.append(
                _make(
                    fname,
                    "SYNTAX_ERROR",
                    f"{e.msg} at line {e.lineno}",
                    fix="Fix the syntax error.",
                )
            )
    return errors


# ── Aggregator ──────────────────────────────────────────────────────────────


def run_all(
    files: dict[str, str],
    spec: Any | None = None,
    *,
    framework: str | None = None,
) -> list[dict]:
    """Run every validator applicable to the given framework and return all errors."""
    errors: list[dict] = []
    errors.extend(validate_syntax(files))
    # Skip downstream validators if syntax broken — line numbers etc. would be misleading.
    if any(e["code"] == "SYNTAX_ERROR" for e in errors):
        return errors
    errors.extend(validate_imports_ast(files))
    errors.extend(validate_tool_param_safety(files))
    if framework == "crewai":
        errors.extend(validate_crewai_tool_schema(files))
    if spec is not None:
        errors.extend(validate_entry_point_wiring(files, spec))
        errors.extend(validate_tool_coverage(files, spec))
    return errors
