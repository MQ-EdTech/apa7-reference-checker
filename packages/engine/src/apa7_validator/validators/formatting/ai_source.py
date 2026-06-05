# packages/engine/src/apa7_validator/validators/formatting/ai_source.py
from __future__ import annotations

from ...models import Issue, Reference, ReferenceType
from ..base import IssueBuilder

_B = IssueBuilder(target_kind="reference")


def check_ai_source(ref: Reference) -> list[Issue]:
    if ref.ref_type is not ReferenceType.AI_SOURCE:
        return []
    issues: list[Issue] = []
    if not ref.extras.get("model_kind"):
        issues.append(
            _B.error(
                code="ai_missing_model_kind",
                message="AI-generated source is missing the bracketed model descriptor",
                position=ref.position,
                suggestion="Add a description in brackets, e.g. '[Large language model]'",
            )
        )
    if not ref.url:
        issues.append(
            _B.error(
                code="ai_missing_url",
                message="AI-generated source is missing the model's URL",
                position=ref.position,
                suggestion="Include the URL where the model is accessed (e.g., https://chat.openai.com)",
            )
        )
    if ref.authors and ref.authors[0].given_initials:
        issues.append(
            _B.warning(
                code="ai_author_should_be_developer",
                message=(
                    "AI-source author looks like a personal name; APA 7 currently treats the "
                    "developer (e.g., OpenAI) as author"
                ),
                position=ref.position,
                suggestion="Use the developing organisation as the author",
            )
        )
    return issues
