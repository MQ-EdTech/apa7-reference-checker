from __future__ import annotations

from ...extractors.base import PositionMap, StyleInfo
from ...models import Issue, Reference, ReferenceType
from ..base import IssueBuilder

_B = IssueBuilder(target_kind="reference")

# APA 7 conventional hanging indent is 0.5 inch = 36 pt.
# We accept >= 18 pt as a reasonable minimum (allows narrower indents).
_MIN_HANGING_PT = 18.0


def _paragraph_for(ref: Reference, position_map: PositionMap) -> int | None:
    kind, src = position_map.to_source(ref.position.start)
    if kind != "docx_run" or src is None:
        return None
    return src[0]


def check_hanging_indent(
    refs: list[Reference],
    style_info: StyleInfo,
    position_map: PositionMap,
) -> list[Issue]:
    issues: list[Issue] = []
    by_para = {p.paragraph_index: p for p in style_info.paragraphs}
    for ref in refs:
        para_idx = _paragraph_for(ref, position_map)
        if para_idx is None:
            continue
        para = by_para.get(para_idx)
        if para is None:
            continue
        if para.indent_hanging_pt is None or para.indent_hanging_pt < _MIN_HANGING_PT:
            issues.append(
                _B.warning(
                    code="hanging_indent_missing",
                    message="Reference paragraph lacks the APA 7 hanging indent",
                    position=ref.position,
                    suggestion="Apply hanging indent (~36pt / 0.5 inch) to each reference list paragraph",
                )
            )
    return issues


def _run_at_offset(
    offset: int,
    position_map: PositionMap,
    style_info: StyleInfo,
) -> tuple[int, int] | None:
    kind, src = position_map.to_source(offset)
    if kind != "docx_run" or src is None:
        return None
    return (src[0], src[1])


def check_journal_italics(
    refs: list[Reference],
    style_info: StyleInfo,
    position_map: PositionMap,
    extracted_text: str,
) -> list[Issue]:
    issues: list[Issue] = []
    by_pr = {(r.paragraph_index, r.run_index): r for r in style_info.runs}
    for ref in refs:
        if ref.ref_type is not ReferenceType.JOURNAL_ARTICLE or not ref.container:
            continue
        # Locate the container substring within the reference's raw span.
        ref_text = extracted_text[ref.position.start : ref.position.end]
        rel = ref_text.find(ref.container)
        if rel < 0:
            continue
        abs_start = ref.position.start + rel
        pr = _run_at_offset(abs_start, position_map, style_info)
        if pr is None:
            continue
        run = by_pr.get(pr)
        if run is None or not run.italic:
            issues.append(
                _B.warning(
                    code="journal_italics_missing",
                    message=f"Journal title '{ref.container}' is not italicised",
                    position=ref.position,
                    suggestion="Italicise the journal name in the reference",
                )
            )
    return issues


def check_book_title_italics(
    refs: list[Reference],
    style_info: StyleInfo,
    position_map: PositionMap,
    extracted_text: str,
) -> list[Issue]:
    issues: list[Issue] = []
    by_pr = {(r.paragraph_index, r.run_index): r for r in style_info.runs}
    for ref in refs:
        if ref.ref_type not in (ReferenceType.BOOK, ReferenceType.BOOK_CHAPTER):
            continue
        # For BOOK: the italicised text is ref.title.
        # For BOOK_CHAPTER: the italicised text is ref.container (the book title).
        target = ref.container if ref.ref_type is ReferenceType.BOOK_CHAPTER else ref.title
        if not target:
            continue
        ref_text = extracted_text[ref.position.start : ref.position.end]
        rel = ref_text.find(target)
        if rel < 0:
            continue
        abs_start = ref.position.start + rel
        pr = _run_at_offset(abs_start, position_map, style_info)
        if pr is None:
            continue
        run = by_pr.get(pr)
        if run is None or not run.italic:
            label = "Book title" if ref.ref_type is ReferenceType.BOOK else "Containing book title"
            issues.append(
                _B.warning(
                    code="book_title_italics_missing",
                    message=f"{label} '{target}' is not italicised",
                    position=ref.position,
                    suggestion="Italicise the book title in the reference",
                )
            )
    return issues
