# APA 7 Rule Catalogue (v1)

Each rule has a stable machine-readable code. The implementation lives under
`packages/engine/src/apa7_validator/validators/`.

## Cross-cutting

| Code | Severity | Description |
|------|----------|-------------|
| `references_not_alphabetised` | warning | Reference list out of order |
| `doi_malformed` | error | DOI does not match `10.<reg>/<suffix>` |
| `doi_surface_form_deprecated` | warning | DOI uses the deprecated `doi:` prefix instead of the APA 7-canonical `https://doi.org/` URL |
| `year_malformed` | error | Year is not 4 digits or `n.d.` |
| `title_not_sentence_case` | warning | Title appears to use title case |

## Journal article

| Code | Severity | Description |
|------|----------|-------------|
| `journal_missing_volume` | error | Volume number is missing |
| `journal_missing_pages` | warning | Page range is missing |
| `journal_missing_doi` | info | DOI is missing |

## Book

| Code | Severity | Description |
|------|----------|-------------|
| `book_missing_publisher` | error | Publisher is missing |

## Book chapter

| Code | Severity | Description |
|------|----------|-------------|
| `chapter_missing_editor` | error | Editor missing |
| `chapter_missing_book_title` | error | Containing book title missing |
| `chapter_missing_pages` | error | Page range missing |
| `chapter_missing_publisher` | error | Publisher missing |

## Website

| Code | Severity | Description |
|------|----------|-------------|
| `website_missing_url` | error | URL missing |
| `website_consider_retrieval_date` | info | n.d. and non-archived; consider retrieval date |

## Report

| Code | Severity | Description |
|------|----------|-------------|
| `report_missing_publisher` | error | Issuing body missing |

## AI source

| Code | Severity | Description |
|------|----------|-------------|
| `ai_missing_model_kind` | error | `[Large language model]` bracket missing |
| `ai_missing_url` | error | URL missing |
| `ai_author_should_be_developer` | warning | Author looks like a personal name |

## Cross-matching

| Code | Severity | Description |
|------|----------|-------------|
| `citation_without_reference` | error | In-text citation has no reference list entry |
| `reference_uncited` | warning | Reference list entry is never cited |
| `ambiguous_match` | warning | Citation matches multiple references |

## Existence

| Code | Severity | Description |
|------|----------|-------------|
| `doi_not_found` | error | CrossRef returned 404 for the DOI |
| `isbn_not_found` | error | OpenLibrary returned 404 for the ISBN |
| `url_not_found` | error | URL returned 404 or 410 |
| `existence_check_unavailable` | info | Lookup service unreachable / rate-limited |

## Styling (DOCX-aware)

These rules require DOCX input — they're skipped for `.pdf` and plain-text.

| Code | Severity | Description |
|------|----------|-------------|
| `hanging_indent_missing` | warning | Reference paragraph lacks the APA 7 hanging indent (~0.5 inch) |
| `journal_italics_missing` | warning | Journal name should be italicised but isn't |
| `book_title_italics_missing` | warning | Book or containing-book title should be italicised but isn't |

## Known gaps — not implemented in this plan (planned for v1.x)

These APA 7 rules are mentioned in the spec but require either DOCX-aware
extraction (which loses formatting through plain-text extraction) or
non-trivial parser changes. They are explicitly out of scope for the
engine+CLI plan and slated for a follow-up.

| Code | Why deferred |
|------|-------------|
| `author_ellipsis_missing` | Requires the parser to detect and preserve `...` / `…` between authors and the 21+ author count rule. |
| `citation_et_al_threshold` | Requires cross-checking citation form against the parsed reference's author count (a citation-reference relational rule). |
