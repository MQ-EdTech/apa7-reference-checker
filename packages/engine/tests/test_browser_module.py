"""Exercise the browser entrypoint under regular CPython."""

import asyncio
import io
import json
import zipfile

from apa7_validator.browser import _REPORT_CACHE, annotate, run


def _reset_cache():
    _REPORT_CACHE.clear()


def test_run_returns_job_id_and_report_json():
    _reset_cache()
    text = "Climate is warming (Smith, 2020)."
    result_str = asyncio.run(run(text, "text"))
    result = json.loads(result_str)
    assert "job_id" in result
    assert "report" in result
    assert isinstance(result["report"], dict)
    # The cache should now contain the job.
    assert result["job_id"] in _REPORT_CACHE


def test_annotate_returns_docx_bytes_for_text_input():
    _reset_cache()
    text = "Climate is warming (Smith, 2020)."
    result_str = asyncio.run(run(text, "text"))
    job_id = json.loads(result_str)["job_id"]
    docx_bytes = annotate(job_id)
    # DOCX is a zip — magic bytes 'PK'.
    assert docx_bytes.startswith(b"PK")
    # And contains word/comments.xml or at least word/document.xml.
    with zipfile.ZipFile(io.BytesIO(docx_bytes)) as z:
        names = z.namelist()
        assert "word/document.xml" in names


def test_annotate_raises_for_unknown_job_id():
    _reset_cache()
    try:
        annotate("not-a-real-uuid")
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError for unknown job_id")


def test_run_clears_previous_cache_entries():
    _reset_cache()
    asyncio.run(run("First essay (Smith, 2020).", "text"))
    first_keys = set(_REPORT_CACHE.keys())
    asyncio.run(run("Second essay (Jones, 2021).", "text"))
    second_keys = set(_REPORT_CACHE.keys())
    # The cache should now have only the second job's entry.
    assert first_keys.isdisjoint(second_keys)
    assert len(second_keys) == 1


def test_run_includes_line_numbers_on_issues():
    _reset_cache()
    # Three lines; the orphan citation is on line 1.
    text = "Climate is warming (Jones, 2099).\n\nReferences\n\nSmith, J. (2020). Foundations of climate research. Earth Press."
    result_str = asyncio.run(run(text, "text"))
    result = json.loads(result_str)
    # The orphan citation_without_reference issue should be on line 1.
    orphan = next(
        i for i in result["report"]["issues"] if i["code"] == "citation_without_reference"
    )
    assert orphan["line"] == 1


def test_run_includes_tier_on_each_reference():
    _reset_cache()
    text = (
        "Climate is warming (Smith, 2020).\n\n"
        "References\n\n"
        "Smith, J. (2020). Foundations of climate research. Earth Press."
    )
    result_str = asyncio.run(run(text, "text"))
    result = json.loads(result_str)
    refs = result["report"]["references"]
    assert all("tier" in r for r in refs)
    assert all(r["tier"] in (1, 3) for r in refs)
