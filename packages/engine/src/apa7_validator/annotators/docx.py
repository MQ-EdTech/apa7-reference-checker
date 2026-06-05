from __future__ import annotations

import io
import re
import zipfile
from datetime import UTC, datetime
from typing import TypedDict

from lxml import etree

from ..extractors.base import PositionMap
from ..models import Report

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS_MAP = {"w": W_NS}
COMMENTS_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"


class CommentSpec(TypedDict):
    id: str
    author: str
    initials: str
    date: str  # ISO-8601
    text: str
    anchor_paragraph_idx: int
    anchor_text: str  # substring within the paragraph to anchor on


def _qn(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def _build_comments_xml(comments: list[CommentSpec]) -> bytes:
    root = etree.Element(_qn("comments"), nsmap={"w": W_NS})
    for c in comments:
        comment = etree.SubElement(
            root,
            _qn("comment"),
            {
                _qn("id"): c["id"],
                _qn("author"): c["author"],
                _qn("initials"): c["initials"],
                _qn("date"): c["date"],
            },
        )
        p = etree.SubElement(comment, _qn("p"))
        r = etree.SubElement(p, _qn("r"))
        t = etree.SubElement(r, _qn("t"))
        t.text = c["text"]
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def _inject_markers_in_document(document_xml: bytes, comments: list[CommentSpec]) -> bytes:
    tree = etree.fromstring(document_xml)
    paragraphs = tree.findall(".//w:p", NS_MAP)
    for c in comments:
        idx = c["anchor_paragraph_idx"]
        if idx >= len(paragraphs):
            continue
        para = paragraphs[idx]
        anchor = c["anchor_text"]
        for r in para.findall("w:r", NS_MAP):
            t = r.find("w:t", NS_MAP)
            if t is None or t.text is None or anchor not in t.text:
                continue
            before, _, after = t.text.partition(anchor)
            t.text = before
            start = etree.Element(_qn("commentRangeStart"), {_qn("id"): c["id"]})
            anchor_r = etree.Element(_qn("r"))
            anchor_t = etree.SubElement(anchor_r, _qn("t"))
            anchor_t.text = anchor
            end = etree.Element(_qn("commentRangeEnd"), {_qn("id"): c["id"]})
            ref_r = etree.Element(_qn("r"))
            etree.SubElement(ref_r, _qn("commentReference"), {_qn("id"): c["id"]})
            after_r = etree.Element(_qn("r"))
            after_t = etree.SubElement(after_r, _qn("t"))
            after_t.text = after
            parent = r.getparent()
            if parent is None:
                break
            insert_idx = list(parent).index(r) + 1
            for el in (start, anchor_r, end, ref_r, after_r):
                parent.insert(insert_idx, el)
                insert_idx += 1
            break
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)


def _patch_content_types(content_types_xml: bytes) -> bytes:
    tree = etree.fromstring(content_types_xml)
    ns = "http://schemas.openxmlformats.org/package/2006/content-types"
    existing = tree.findall(f"{{{ns}}}Override")
    if any(o.get("PartName") == "/word/comments.xml" for o in existing):
        return content_types_xml
    override = etree.SubElement(tree, f"{{{ns}}}Override")
    override.set("PartName", "/word/comments.xml")
    override.set(
        "ContentType",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml",
    )
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)


def _patch_document_rels(rels_xml: bytes) -> bytes:
    ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    tree = etree.fromstring(rels_xml)
    existing = tree.findall(f"{{{ns}}}Relationship")
    if any(r.get("Target") == "comments.xml" for r in existing):
        return rels_xml
    rel_id = f"rId{max((int(re.sub(r'\D', '', r.get('Id') or '0') or '0') for r in existing), default=0) + 1}"
    rel = etree.SubElement(tree, f"{{{ns}}}Relationship")
    rel.set("Id", rel_id)
    rel.set("Type", COMMENTS_REL_TYPE)
    rel.set("Target", "comments.xml")
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)


def inject_comment_xml(source_bytes: bytes, comments: list[CommentSpec]) -> bytes:
    """Inject Word-native comments into a DOCX via direct OOXML manipulation."""
    src = io.BytesIO(source_bytes)
    out_buf = io.BytesIO()
    with zipfile.ZipFile(src, "r") as zin:
        with zipfile.ZipFile(out_buf, "w", zipfile.ZIP_DEFLATED) as zout:
            comments_xml = _build_comments_xml(comments)
            wrote_comments = False
            for item in zin.infolist():
                data: bytes = zin.read(item.filename)
                if item.filename == "word/document.xml":
                    data = _inject_markers_in_document(data, comments)
                elif item.filename == "[Content_Types].xml":
                    data = _patch_content_types(data)
                elif item.filename == "word/_rels/document.xml.rels":
                    data = _patch_document_rels(data)
                zout.writestr(item, data)
                if item.filename == "word/comments.xml":
                    wrote_comments = True
            if not wrote_comments:
                zout.writestr("word/comments.xml", comments_xml)
    return out_buf.getvalue()


def annotate_docx_from_source(
    *,
    source_bytes: bytes,
    report: Report,
    extracted_text: str,
    position_map: PositionMap,
) -> bytes:
    """Annotate a DOCX with one Word comment per issue.

    Uses the DOCX extractor's position_map (`docx_run` kind) to find the
    paragraph index for each issue. Within the paragraph, the anchor text is
    the literal slice of `extracted_text[issue.position.start:issue.position.end]`.
    """
    iso_now = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    specs: list[CommentSpec] = []
    for i, iss in enumerate(report.issues):
        kind, ref = position_map.to_source(iss.position.start)
        if kind != "docx_run":
            continue
        para_idx = ref[0]
        anchor_text = extracted_text[iss.position.start : iss.position.end]
        if not anchor_text.strip():
            continue
        body = iss.message
        if iss.suggestion:
            body = f"{body}\nSuggestion: {iss.suggestion}"
        specs.append(
            CommentSpec(
                id=str(i),
                author="apa7-validator",
                initials="APA7",
                date=iso_now,
                text=body,
                anchor_paragraph_idx=para_idx,
                anchor_text=anchor_text,
            )
        )
    return inject_comment_xml(source_bytes, specs)
