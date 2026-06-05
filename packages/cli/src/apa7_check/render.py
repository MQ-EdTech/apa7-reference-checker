from __future__ import annotations

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
