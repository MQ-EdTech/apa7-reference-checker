# packages/engine/src/apa7_validator/reporter.py
from __future__ import annotations

from .models import Citation, Issue, Reference, Report, Severity

_SEVERITY_ORDER = {Severity.ERROR: 0, Severity.WARNING: 1, Severity.INFO: 2}


def assemble(
    *,
    references: list[Reference],
    citations: list[Citation],
    formatting_issues: list[Issue],
    cross_matching_issues: list[Issue],
    existence_issues: list[Issue],
    warnings: list[str],
    degraded_checks: list[str],
) -> Report:
    issues = formatting_issues + cross_matching_issues + existence_issues
    issues.sort(key=lambda i: (_SEVERITY_ORDER[i.severity], i.position.start))
    return Report(
        references=references,
        citations=citations,
        issues=issues,
        warnings=warnings,
        degraded_checks=degraded_checks,
    )
