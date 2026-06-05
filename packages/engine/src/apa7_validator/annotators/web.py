from __future__ import annotations

from typing import Any

from ..models import Report


def build_web_annotation(report: Report, source_text: str) -> dict[str, Any]:
    annotations: list[dict[str, Any]] = []
    for iss in report.issues:
        start, end = iss.position.start, iss.position.end
        annotations.append(
            {
                "code": iss.code,
                "severity": iss.severity.value,
                "message": iss.message,
                "suggestion": iss.suggestion,
                "target_kind": iss.target_kind,
                "span": [start, end],
                "span_text": source_text[start:end],
            }
        )
    return {
        "annotations": annotations,
        "warnings": report.warnings,
        "degraded_checks": report.degraded_checks,
        "reference_count": len(report.references),
        "citation_count": len(report.citations),
    }
