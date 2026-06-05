import io
import zipfile

import docx as pythondocx
from apa7_validator.annotators.docx import inject_comment_xml


def _make_minimal_docx() -> bytes:
    doc = pythondocx.Document()
    doc.add_paragraph("Climate change is well documented (Smith, 2020).")
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_inject_comment_xml_adds_comments_part():
    src = _make_minimal_docx()
    out = inject_comment_xml(
        src,
        comments=[
            {
                "id": "0",
                "author": "apa7",
                "initials": "apa7",
                "date": "2026-06-05T00:00:00Z",
                "text": "Verify DOI.",
                "anchor_paragraph_idx": 0,
                "anchor_text": "Smith, 2020",
            }
        ],
    )
    with zipfile.ZipFile(io.BytesIO(out)) as z:
        names = set(z.namelist())
        assert "word/comments.xml" in names
        # Confirm document.xml carries comment range markers.
        doc_xml = z.read("word/document.xml").decode()
        assert "commentRangeStart" in doc_xml
        assert "commentReference" in doc_xml
