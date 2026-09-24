#!/usr/bin/env python3
"""Report dependency-boundary violations found in Python imports under src/."""

from __future__ import annotations

import argparse
import ast
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = ROOT / "src"


@dataclass(frozen=True, order=True)
class Finding:
    path: str
    line: int
    rule: str
    target: str


def _context_names() -> set[str]:
    if not SRC_ROOT.is_dir():
        return set()
    return {child.name for child in SRC_ROOT.iterdir() if child.is_dir() and (child / "__init__.py").is_file()}


def _module_parts(path: Path) -> list[str]:
    parts = list(path.relative_to(ROOT).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return parts


def _package_parts(path: Path) -> list[str]:
    parts = _module_parts(path)
    return parts if path.name == "__init__.py" else parts[:-1]


def _import_candidates(node: ast.Import | ast.ImportFrom, path: Path) -> set[tuple[str, ...]]:
    if isinstance(node, ast.Import):
        return {tuple(alias.name.split(".")) for alias in node.names}

    if node.level:
        package = _package_parts(path)
        levels_up = node.level - 1
        if levels_up > len(package):
            return set()
        base = package[: len(package) - levels_up]
        if node.module:
            base.extend(node.module.split("."))
    else:
        base = node.module.split(".") if node.module else []

    candidates = {tuple(base)} if base else set()
    # `from package import infrastructure` names a possible submodule even
    # though AST does not distinguish it from an attribute import.
    if "infrastructure" not in base and "persistence" not in base:
        candidates.update(tuple(base + alias.name.split(".")) for alias in node.names)
    return candidates


def _normalized_target(candidate: tuple[str, ...], contexts: set[str]) -> tuple[str, tuple[str, ...]] | None:
    parts = list(candidate)
    if parts and parts[0] == "src":
        parts.pop(0)
    if len(parts) < 2 or parts[0] not in contexts:
        return None
    return parts[0], tuple(parts[1:])


def _findings_for_import(
    node: ast.Import | ast.ImportFrom,
    path: Path,
    source_context: str,
    source_layer: str,
    contexts: set[str],
) -> set[Finding]:
    findings: set[Finding] = set()
    relative_path = path.relative_to(ROOT).as_posix()

    for candidate in _import_candidates(node, path):
        target = _normalized_target(candidate, contexts)
        if target is None:
            continue
        target_context, target_parts = target
        target_text = ".".join(candidate)
        imports_infrastructure = "infrastructure" in target_parts
        imports_persistence = "persistence" in target_parts
        rules: set[str] = set()

        if source_layer == "domain" and imports_infrastructure:
            rules.add("domain-imports-infrastructure")
        if source_layer == "application" and imports_infrastructure:
            rules.add("application-imports-infrastructure")
        if source_context != target_context and (imports_infrastructure or imports_persistence):
            rules.add("cross-context-infrastructure-import")

        findings.update(Finding(relative_path, node.lineno, rule, target_text) for rule in rules)
    return findings


def scan() -> tuple[list[Finding], list[Finding]]:
    """Return architecture findings and parser/read diagnostics, both sorted."""
    if not SRC_ROOT.is_dir():
        return [], [Finding("src", 1, "scan-error", "src/ directory not found")]

    contexts = _context_names()
    architecture_findings: set[Finding] = set()
    diagnostics: set[Finding] = set()

    for path in sorted(SRC_ROOT.rglob("*.py"), key=lambda item: item.as_posix()):
        relative = path.relative_to(ROOT)
        parts = relative.parts
        if len(parts) < 3:
            continue
        source_context = parts[1]
        source_layer = parts[2]
        if source_layer not in {"domain", "application", "infrastructure"}:
            continue

        try:
            with tokenize.open(path) as source_file:
                source = source_file.read()
            tree = ast.parse(source, filename=relative.as_posix())
        except (OSError, SyntaxError, UnicodeError) as error:
            line = getattr(error, "lineno", None) or 1
            message = getattr(error, "msg", None) or str(error)
            diagnostics.add(Finding(relative.as_posix(), line, "parse-error", message))
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                architecture_findings.update(
                    _findings_for_import(
                        node,
                        path,
                        source_context,
                        source_layer,
                        contexts,
                    )
                )

    return sorted(architecture_findings), sorted(diagnostics)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report architecture dependency violations in src/")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit nonzero when architecture violations or parse errors are found",
    )
    args = parser.parse_args(argv)

    violations, diagnostics = scan()
    if not violations and not diagnostics:
        print("Architecture check: no violations found.")
    else:
        print(f"Architecture check: {len(violations)} violation(s), {len(diagnostics)} diagnostic(s).")
        for finding in sorted(violations + diagnostics):
            print(f"{finding.path}:{finding.line}: {finding.rule}: {finding.target}")

    if args.strict and (violations or diagnostics):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
