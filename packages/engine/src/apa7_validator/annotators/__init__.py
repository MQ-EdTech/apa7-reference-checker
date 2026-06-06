from .docx import annotate_docx_from_source, annotate_docx_from_text, inject_comment_xml
from .web import build_web_annotation

__all__ = [
    "annotate_docx_from_source",
    "annotate_docx_from_text",
    "build_web_annotation",
    "inject_comment_xml",
]
