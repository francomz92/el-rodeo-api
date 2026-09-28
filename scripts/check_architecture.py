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

# Exact, reviewed composition and presentation seams. Keep both the source path
# and target module explicit; this is not a context-wide exception mechanism.
ALLOWED_CROSS_CONTEXT_SEAMS: dict[str, frozenset[str]] = {
    "src/common/infrastructure/persistence/repositories/_registry.py": frozenset(
        {
            "src.auth.infrastructure.persistence.repositories._registry",
            "src.billing.infrastructure.persistence.repositories._registry",
            "src.calendar.infrastructure.persistence.repositories._registry",
            "src.cattle.infrastructure.persistence.repositories._registry",
            "src.finance.infrastructure.persistence.repositories._registry",
            "src.market.infrastructure.persistence.repositories._registry",
            "src.reports.infrastructure.persistence.repositories._registry",
        }
    ),
    "src/common/infrastructure/presentation/routers/__init__.py": frozenset(
        {
            "src.auth.infrastructure.presentation.routers",
            "src.billing.infrastructure.presentation.routers",
            "src.calendar.infrastructure.presentation.routers",
            "src.cattle.infrastructure.presentation.routers",
            "src.finance.infrastructure.presentation.routers",
            "src.market.infrastructure.presentation.routers",
            "src.reports.infrastructure.presentation.routers.reports",
        }
    ),
    "src/common/infrastructure/workers/cron_tasks_register.py": frozenset(
        {
            "src.billing.infrastructure.workers._expire_trials_task",
            "src.billing.infrastructure.workers._monthly_billing_task",
            "src.calendar.infrastructure.workers.upcoming_events_tasks",
        }
    ),
    "src/auth/infrastructure/composition.py": frozenset({"src.billing.infrastructure.adapters.trial_provisioner"}),
    "src/billing/infrastructure/presentation/routers/_payment_router.py": frozenset(
        {"src.auth.infrastructure.presentation.dependencies.auth_dependencies"}
    ),
    "src/billing/infrastructure/presentation/routers/_subscription_router.py": frozenset(
        {"src.auth.infrastructure.presentation.dependencies.auth_dependencies"}
    ),
    "src/calendar/infrastructure/presentation/routers/_calendar_events.py": frozenset(
        {"src.auth.infrastructure.presentation.dependencies.auth_dependencies"}
    ),
    "src/cattle/infrastructure/presentation/routers/_animal_protocols.py": frozenset(
        {"src.auth.infrastructure.presentation.dependencies.auth_dependencies"}
    ),
    "src/cattle/infrastructure/presentation/routers/_animal_types.py": frozenset(
        {"src.auth.infrastructure.presentation.dependencies.auth_dependencies"}
    ),
    "src/cattle/infrastructure/presentation/routers/_animals.py": frozenset(
        {"src.auth.infrastructure.presentation.dependencies.auth_dependencies"}
    ),
    "src/common/infrastructure/presentation/routers/webhook_subscriptions.py": frozenset(
        {"src.auth.infrastructure.presentation.dependencies.auth_dependencies"}
    ),
    "src/finance/infrastructure/presentation/routers/_animal_supplies.py": frozenset(
        {"src.auth.infrastructure.presentation.dependencies.auth_dependencies"}
    ),
    "src/finance/infrastructure/presentation/routers/_animal_supply_types.py": frozenset(
        {"src.auth.infrastructure.presentation.dependencies.auth_dependencies"}
    ),
    "src/finance/infrastructure/presentation/routers/_purchases.py": frozenset(
        {"src.auth.infrastructure.presentation.dependencies.auth_dependencies"}
    ),
    "src/market/infrastructure/presentation/routers/_buyers.py": frozenset(
        {"src.auth.infrastructure.presentation.dependencies.auth_dependencies"}
    ),
    "src/market/infrastructure/presentation/routers/_sales.py": frozenset(
        {"src.auth.infrastructure.presentation.dependencies.auth_dependencies"}
    ),
    "src/reports/infrastructure/presentation/routers/reports.py": frozenset(
        {"src.auth.infrastructure.presentation.dependencies.auth_dependencies"}
    ),
}


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
) -> tuple[set[Finding], set[Finding]]:
    findings: set[Finding] = set()
    allowed_seams: set[Finding] = set()
    relative_path = path.relative_to(ROOT).as_posix()

    for candidate in _import_candidates(node, path):
        target = _normalized_target(candidate, contexts)
        if target is None:
            continue
        target_context, target_parts = target
        target_text = ".".join(candidate)
        canonical_target = "src." + ".".join((target_context, *target_parts))
        imports_infrastructure = "infrastructure" in target_parts
        imports_persistence = "persistence" in target_parts
        rules: set[str] = set()

        if source_layer == "domain" and imports_infrastructure:
            rules.add("domain-imports-infrastructure")
        if source_layer == "application" and imports_infrastructure:
            rules.add("application-imports-infrastructure")
        if source_context != target_context and target_context != "common" and (imports_infrastructure or imports_persistence):
            seam_targets = ALLOWED_CROSS_CONTEXT_SEAMS.get(relative_path, frozenset())
            if canonical_target in seam_targets:
                allowed_seams.add(Finding(relative_path, node.lineno, "allowed-cross-context-seam", target_text))
            else:
                rules.add("cross-context-infrastructure-import")

        findings.update(Finding(relative_path, node.lineno, rule, target_text) for rule in rules)
    return findings, allowed_seams


def scan() -> tuple[list[Finding], list[Finding], list[Finding]]:
    """Return sorted violations, allowed seams, and parser/read diagnostics."""
    if not SRC_ROOT.is_dir():
        return [], [], [Finding("src", 1, "scan-error", "src/ directory not found")]

    contexts = _context_names()
    architecture_findings: set[Finding] = set()
    allowed_seams: set[Finding] = set()
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
                findings, seams = _findings_for_import(
                    node,
                    path,
                    source_context,
                    source_layer,
                    contexts,
                )
                architecture_findings.update(findings)
                allowed_seams.update(seams)

    return sorted(architecture_findings), sorted(allowed_seams), sorted(diagnostics)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report architecture dependency violations in src/")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit nonzero when architecture violations or parse errors are found",
    )
    args = parser.parse_args(argv)

    violations, allowed_seams, diagnostics = scan()
    print(f"Architecture check: {len(violations)} violation(s), {len(allowed_seams)} allowed seam(s), {len(diagnostics)} diagnostic(s).")
    for finding in sorted(violations + diagnostics):
        print(f"{finding.path}:{finding.line}: {finding.rule}: {finding.target}")

    if args.strict and (violations or diagnostics):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
