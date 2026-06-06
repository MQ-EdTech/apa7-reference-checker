from __future__ import annotations

import json as _json
from dataclasses import asdict
from typing import Any

from .models import Report, Severity

_ICON = {Severity.ERROR: "[ERROR]", Severity.WARNING: "[WARN] ", Severity.INFO: "[INFO] "}


def render_human(report: Report) -> str:
    lines: list[str] = []
    lines.append(f"References found: {len(report.references)}")
    lines.append(f"Citations found: {len(report.citations)}")
    if report.warnings:
        lines.append("Warnings: " + ", ".join(report.warnings))
    if report.degraded_checks:
        lines.append("Degraded checks: " + ", ".join(report.degraded_checks))
    if report.issues:
        lines.append("")
        lines.append("Issues:")
        for iss in report.issues:
            lines.append(f"  {_ICON[iss.severity]} {iss.code}: {iss.message}")
            if iss.suggestion:
                lines.append(f"           -> {iss.suggestion}")
    else:
        lines.append("No issues found.")
    return "\n".join(lines) + "\n"


def render_json(report: Report) -> str:
    references: list[dict[str, Any]] = [asdict(r) for r in report.references]
    citations: list[dict[str, Any]] = [asdict(c) for c in report.citations]
    issues: list[dict[str, Any]] = [
        {**asdict(i), "severity": i.severity.value} for i in report.issues
    ]
    # `ref_type` is an Enum; convert to its name string.
    for r in references:
        ref_type = r["ref_type"]
        r["ref_type"] = ref_type.name if hasattr(ref_type, "name") else str(ref_type)
    payload: dict[str, Any] = {
        "references": references,
        "citations": citations,
        "issues": issues,
        "warnings": report.warnings,
        "degraded_checks": report.degraded_checks,
    }
    return _json.dumps(payload, indent=2) + "\n"
