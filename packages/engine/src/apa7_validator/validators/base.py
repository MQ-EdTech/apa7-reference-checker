from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..models import Issue, Position, Reference, Severity


@dataclass(frozen=True, slots=True)
class IssueBuilder:
    target_kind: str  # "reference" | "citation" | "global"

    def error(
        self,
        code: str,
        message: str,
        position: Position,
        suggestion: str | None = None,
    ) -> Issue:
        return Issue(
            code=code,
            severity=Severity.ERROR,
            message=message,
            position=position,
            suggestion=suggestion,
            target_kind=self.target_kind,  # type: ignore[arg-type]
        )

    def warning(
        self,
        code: str,
        message: str,
        position: Position,
        suggestion: str | None = None,
    ) -> Issue:
        return Issue(
            code=code,
            severity=Severity.WARNING,
            message=message,
            position=position,
            suggestion=suggestion,
            target_kind=self.target_kind,  # type: ignore[arg-type]
        )

    def info(
        self,
        code: str,
        message: str,
        position: Position,
        suggestion: str | None = None,
    ) -> Issue:
        return Issue(
            code=code,
            severity=Severity.INFO,
            message=message,
            position=position,
            suggestion=suggestion,
            target_kind=self.target_kind,  # type: ignore[arg-type]
        )


class Rule(Protocol):
    def __call__(self, ref: Reference) -> list[Issue]: ...
