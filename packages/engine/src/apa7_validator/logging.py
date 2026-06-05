# packages/engine/src/apa7_validator/logging.py
from __future__ import annotations

import json
import sys
from typing import Any

SAFE_FIELDS: frozenset[str] = frozenset(
    {
        "job_id",
        "status",
        "duration_ms",
        "error_code",
        "reference_count",
        "issue_count",
        "degraded_checks",
        "ref_type",
        "severity",
        "rule_code",
    }
)


def safe_log(message: str, **fields: Any) -> None:
    bad = set(fields) - SAFE_FIELDS
    if bad:
        raise ValueError(
            f"safe_log refuses field(s) not on the allowlist: {sorted(bad)}. "
            "If you must log a new field, add it to SAFE_FIELDS after privacy review."
        )
    payload = {"msg": message, **fields}
    print(json.dumps(payload), file=sys.stdout)
