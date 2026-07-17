"""Fail when application functions exceed length or complexity limits."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from radon.complexity import cc_visit

MAX_FUNCTION_LINES = 40
MAX_COMPLEXITY = 10
APP_ROOT = Path("app")
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".pylint-cache",
    "dist",
    "build",
}


def _is_excluded(path: Path) -> bool:
    """Return True for generated, cache, virtualenv, or third-party paths."""
    return any(part in EXCLUDED_PARTS for part in path.parts)


def _python_files(root: Path):
    """Yield application Python files that must be checked."""
    for path in root.rglob("*.py"):
        if not _is_excluded(path):
            yield path


def _function_lengths(path: Path):
    """Yield function length measurements for one Python file."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node.name, node.end_lineno - node.lineno + 1


def _complexities(path: Path):
    """Yield cyclomatic complexity measurements for one Python file."""
    source = path.read_text(encoding="utf-8")

    for block in cc_visit(source):
        yield block.name, block.complexity


def _collect_violations():
    """Return all function-length and complexity violations."""
    violations = []

    for path in _python_files(APP_ROOT):
        for name, length in _function_lengths(path):
            if length > MAX_FUNCTION_LINES:
                violations.append((path, name, "physical lines", length, MAX_FUNCTION_LINES))

        for name, complexity in _complexities(path):
            if complexity > MAX_COMPLEXITY:
                violations.append((path, name, "cyclomatic complexity", complexity, MAX_COMPLEXITY))

    return violations


def main() -> int:
    """Run the quality gate and return a process exit code."""
    violations = _collect_violations()

    if not violations:
        print("Code quality gate passed.")
        return 0

    print("Code quality gate failed:")
    for path, name, metric, measured, allowed in violations:
        print(f"{path}: {name}: {metric} {measured}; allowed {allowed}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
