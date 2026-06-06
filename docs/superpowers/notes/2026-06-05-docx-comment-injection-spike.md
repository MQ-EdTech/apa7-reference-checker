# DOCX comment injection — spike outcome (2026-06-05)

**Question:** Can we inject Word-native comments into a `.docx` produced by
`python-docx` without losing fidelity?

**Answer:** Yes, via direct OOXML manipulation. `python-docx` does not expose
comments through its high-level API, but we can:

1. Read the `.docx` as a ZIP.
2. Build `word/comments.xml` (a new part).
3. Inject `<w:commentRangeStart/>`, `<w:commentRangeEnd/>`, `<w:commentReference/>`
   markers into the relevant paragraphs in `word/document.xml`.
4. Add an `Override` to `[Content_Types].xml` for the comments part.
5. Add a `Relationship` to `word/_rels/document.xml.rels` pointing to the comments
   part.

**Result:** Word and LibreOffice both render comments correctly. Formatting is
preserved; the spike test exercises the round-trip.

**Caveat:** Position anchoring is by substring match within a paragraph. For
overlapping or repeated anchor texts, we'll need to use the `position_map` from
the DOCX extractor (paragraph_index + run_index) — addressed in Task 35.

**Decision:** Use `lxml` directly. Do not pull in a higher-level docx-comment
library (none of the available options were recently maintained as of this
spike).
