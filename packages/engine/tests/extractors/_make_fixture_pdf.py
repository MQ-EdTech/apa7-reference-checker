"""One-shot generator for tests/fixtures/pdf/sample_essay.pdf.

Run via: uv run python -m tests.extractors._make_fixture_pdf
"""

from pathlib import Path

import pymupdf

OUT = Path(__file__).parent.parent / "fixtures" / "pdf" / "sample_essay.pdf"


def main() -> None:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "Climate change is well documented (Smith, 2020).\n"
        "Recent work extends this (Jones & Lee, 2021).\n\n"
        "References\n"
        "Jones, A., & Lee, B. (2021). New analyses of climate data.\n"
        "    Climate Journal, 5(2), 100-120.\n"
        "Smith, J. (2020). Foundations of climate research. Earth Press.\n",
        fontsize=11,
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
