import io
import zipfile

import docx as pythondocx
from apa7_validator.annotators.docx import inject_comment_xml


def _make_minimal_docx() -> bytes:
    doc = pythondocx.Document()
    doc.add_paragraph("Hello world.")
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_inject_replaces_existing_comments_part():
    src = _make_minimal_docx()
    first = inject_comment_xml(
        src,
        comments=[
            {
                "id": "0",
                "author": "first",
                "initials": "F",
                "date": "2026-06-05T00:00:00Z",
                "text": "FIRST_COMMENT",
                "anchor_paragraph_idx": 0,
                "anchor_text": "Hello",
            }
        ],
    )
    second = inject_comment_xml(
        first,
        comments=[
            {
                "id": "0",
                "author": "second",
                "initials": "S",
                "date": "2026-06-05T00:00:00Z",
                "text": "SECOND_COMMENT",
                "anchor_paragraph_idx": 0,
                "anchor_text": "world",
            }
        ],
    )
    with zipfile.ZipFile(io.BytesIO(second)) as z:
        comments_xml = z.read("word/comments.xml").decode()
        assert "SECOND_COMMENT" in comments_xml
        assert "FIRST_COMMENT" not in comments_xml
