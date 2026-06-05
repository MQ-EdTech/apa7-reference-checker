from __future__ import annotations

import json as _json
from dataclasses import asdict

from apa7_validator.models import Report, Severity

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
    payload = {
        "references": [asdict(r) for r in report.references],
        "citations": [asdict(c) for c in report.citations],
        "issues": [{**asdict(i), "severity": i.severity.value} for i in report.issues],
        "warnings": report.warnings,
        "degraded_checks": report.degraded_checks,
    }
    # `ref_type` is an Enum; convert.
    for r in payload["references"]:
        r["ref_type"] = r["ref_type"].name if hasattr(r["ref_type"], "name") else str(r["ref_type"])
    return _json.dumps(payload, indent=2) + "\n"
