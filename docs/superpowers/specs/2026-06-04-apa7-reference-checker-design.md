# APA 7 Reference Checker — Design

**Date:** 2026-06-04
**Status:** Draft, awaiting user review
**Owner:** Aaron Chakerian (`achakerian@gmail.com`)
**Destination repo:** `MQ-EdTech/apa7-reference-checker` (not yet created — confirm before push)

---

## 1. Overview

An open-source tool that validates academic essays for compliance with APA 7th edition referencing rules. It checks three things:

1. **Formatting** — Is each reference list entry formatted correctly per APA 7 rules (author order, italics, year placement, DOI format, et al. threshold, etc.)?
2. **Existence** — Does the cited work actually exist? (DOI lookup via CrossRef, ISBN via Open Library, URL resolution)
3. **Cross-matching** — Does every in-text citation have a matching reference list entry, and is every listed reference cited at least once?

The product is delivered as:
- A **web upload portal** (paste / drop `.docx` / `.pdf`) with inline-annotated results.
- A **downloadable annotated DOCX** with Word-native comments anchored to each citation/reference.
- A **REST API** for headless integrations.
- **LTI 1.3** endpoints for native embedding in Canvas, Moodle, and other LMSs.
- A **CLI** for local use, CI integration, and scripting.

Stretch goal — semantic claim-evidence validation (does the cited source support the claim being made?) — is explicitly **deferred to v2**.

---

## 2. Goals & non-goals

### Goals (v1)
- Validate APA 7 references and in-text citations across the top 5 reference types (journal article, book, book chapter, website/webpage, report) plus AI-generated sources and secondary/indirect citations.
- Accept paste text, `.docx`, and `.pdf` inputs (text-extractable PDFs only; scanned PDFs flagged, not silently failed).
- Produce both interactive (web) and portable (DOCX) feedback artifacts.
- Be embeddable in Canvas and Moodle via LTI 1.3 with no per-LMS plugin code.
- Be runnable locally via `docker compose up`.
- Maintain a strong privacy posture suitable for processing student work (see §9).

### Non-goals (v1)
- Other citation styles (MLA, Chicago, Harvard, Vancouver, etc.).
- Semantic claim-evidence validation (deferred to v2).
- OCR for scanned PDFs.
- Multi-tenant admin UI (single self-hosted deployment per instance).
- Persistent user submission history.
- Non-English references.
- Production deployment to MQ infrastructure (self-hosted demo only for now).

---

## 3. Audience & use cases

| Audience | Use case | Surface |
|---|---|---|
| **Students** | Check own draft before submitting | Web portal, LTI embed |
| **Markers / tutors** | Bulk-check submitted assignments, return annotated DOCX | Web portal, LTI embed |
| **LMS integrators** | Embed checker in Canvas/Moodle assignment workflow | LTI 1.3 |
| **Headless integrators** | Build other MQ-EdTech tools on top of the engine | REST API, Python library |

---

## 4. Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   docker-compose                             │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌────────────────────────┐  │
│  │ frontend │ ─► │   api    │ ─► │       postgres         │  │
│  │  (SPA)   │    │ FastAPI  │    │  (jobs, LTI registry)  │  │
│  └──────────┘    └────┬─────┘    └────────────────────────┘  │
│                       │                                       │
│                       ▼                                       │
│                  ┌──────────┐    ┌─────────┐                  │
│                  │  redis   │ ◄─►│ worker  │                  │
│                  │ (queue)  │    │  (arq)  │                  │
│                  └──────────┘    └────┬────┘                  │
│                                       │                       │
│                                       ▼                       │
│                              ┌────────────────────┐           │
│                              │  apa7_validator    │           │
│                              │  (Python package)  │           │
│                              │  pure logic        │           │
│                              └────────────────────┘           │
└──────────────────────────────────────────────────────────────┘
                                  ▲
                                  │ also embedded by
                  ┌───────────────┼────────────────┐
                  │               │                │
            ┌──────────┐    ┌──────────┐     ┌──────────┐
            │   CLI    │    │  tests   │     │ future   │
            │  (typer) │    │ (pytest) │     │ tools    │
            └──────────┘    └──────────┘     └──────────┘
```

### Key principles
- **Library-first.** The validation engine (`apa7_validator`) is a standalone Python package with no HTTP, no database, no LMS knowledge. The API, worker, CLI, and any future tool are thin wrappers around it.
- **API + worker split.** Validation jobs run asynchronously; the HTTP service stays responsive under load.
- **Stateless engine, ephemeral state services.** All persistent state lives in Postgres (job records, LTI registrations); Redis is purely the job queue.

### Deployable services (`docker-compose.yml`)
| Service | Image | Purpose |
|---|---|---|
| `frontend` | Built from `apps/frontend` | SPA upload portal + report viewer |
| `api` | Built from `packages/api` | FastAPI: REST + LTI 1.3 endpoints |
| `worker` | Built from `packages/worker` | arq worker: consumes validation jobs |
| `postgres` | `postgres:16-alpine` | Jobs, LTI registrations, sessions |
| `redis` | `redis:7-alpine` | arq queue |
| `caddy` | `caddy:2-alpine` | TLS termination + reverse proxy at the edge |

---

## 5. Components

### 5.1 `apa7_validator` (engine library)
Pure Python package, no IO except via injected clients.

```
apa7_validator/
├── models.py            # Reference, Citation, Issue, Report (dataclasses)
├── extractors/          # bytes/path → text + position_map
│   ├── text.py
│   ├── docx.py          # python-docx
│   └── pdf.py           # pymupdf; flags scanned PDFs
├── parser/
│   ├── reference_list.py  # finds & splits reference list from body
│   ├── references.py      # parses each reference → typed Reference
│   └── citations.py       # extracts in-text citations from body
├── validators/
│   ├── formatting.py    # APA 7 rules per reference type
│   ├── cross_matching.py # in-text ↔ reference list bidirectional
│   └── existence.py     # uses pluggable lookup clients
├── clients/             # injectable; dry-run mode for tests
│   ├── crossref.py      # DOI lookup
│   ├── unpaywall.py     # OA full-text availability
│   └── openlibrary.py   # ISBN lookup
├── annotators/
│   ├── docx.py          # Word-native comments on the .docx
│   └── web.py           # structured annotations for the SPA
└── reporter.py          # assembles final Report
```

**Public API surface (small):**
```python
def validate(
    source: bytes | str,
    format: Literal["text", "docx", "pdf"],
    *,
    clients: Clients | None = None,
) -> Report: ...

def annotate_docx(
    source: bytes,
    report: Report,
    position_map: PositionMap,
) -> bytes: ...
```

**The `position_map` concept** is first-class. Each extracted text span knows where it came from (DOCX paragraph + run + offset; PDF page + offset; raw char offset). Both annotators consume the same map. This is what allows Word comments to land on the right span when the input is a richly-formatted DOCX.

**Caveat to verify at implementation time:** `python-docx` has historically had limited comment-injection support. Likely path is direct OOXML manipulation via `lxml` on `comments.xml` + `document.xml`. A short library-choice spike before committing to an approach.

### 5.2 `api/` (FastAPI service)
- `routes/v1/` — REST endpoints: `POST /validate`, `GET /jobs/{id}`, `GET /jobs/{id}/annotated.docx`, `DELETE /jobs/{id}`, `GET /reports/{id}`.
- `lti/` — LTI 1.3 launch, JWKS, deep-linking, AGS (Assignment & Grade Services) grade-passback.
- `db/` — SQLAlchemy models: `Job`, `LtiPlatform`, `LtiDeployment`, `LtiSession`.
- `queue.py` — arq enqueue helpers.
- `auth/` — API-key auth for REST consumers; session auth for SPA; LTI session validation.

### 5.3 `worker/` (arq worker)
- `tasks.validate_essay(job_id)` — runs the engine, persists `Report` + annotated DOCX to Postgres, optionally calls LTI grade-passback.
- `tasks.cleanup_expired_jobs()` — periodic cron task (every 15 minutes) that hard-deletes jobs past their TTL.

### 5.4 `frontend/` (SPA)
- Upload portal: paste / drop `.docx` / `.pdf`.
- Results view: inline-annotated text + issue sidebar grouped by severity + "Download annotated DOCX" + "Export JSON/CSV report".
- Privacy notice page (linked from every upload screen).
- **Framework choice deferred** — does not block the engine work; will be decided when frontend implementation starts.

### 5.5 `cli/`
- `apa7-check <file>` — calls the library directly (no API/worker/DB), prints human-readable report.
- `apa7-check <file> --json` — structured output for CI / scripting.
- `apa7-check <file> --annotate output.docx` — writes annotated DOCX locally.

---

## 6. Data flow

### 6.1 Primary flow (web upload)

```
1. POST /v1/validate
   { file: <docx/pdf>, format: "docx" }   OR   { text: "...", format: "text" }
   ↓
2. API:
   - Verify auth (session cookie OR API key OR LTI session)
   - Reject if size > limit (10 MB default)
   - Persist essay blob to job-scoped Postgres storage
   - INSERT Job row (status=pending, expires_at=now+TTL)
   - enqueue arq task: validate_essay(job_id)
   ↓
3. API returns 202 { job_id, status_url }
   ↓
4. Frontend polls GET /v1/jobs/{job_id} every 1–2s
   ↓
5. Worker picks up task:
   a. extractors.<format>.extract(blob) → text + position_map
   b. parser.reference_list.split(text) → (body, references_section)
   c. parser.references.parse_all(references_section) → list[Reference]
   d. parser.citations.parse_all(body) → list[Citation]
   e. Run validators concurrently:
      - validators.formatting.check(references)
      - validators.existence.check(references, clients=...)
      - validators.cross_matching.check(citations, references)
   f. reporter.assemble(...) → Report
   g. annotators.docx.write(input_blob_or_extracted, report, position_map)
        → annotated.docx (stored alongside Report)
   h. UPDATE Job: status=complete, report=<json>, has_annotated_docx=true
   ↓
6. GET /v1/jobs/{id} returns Job + Report
   ↓
7. Frontend renders:
   - Annotated text view (uses position_map to overlay issues)
   - Issue sidebar grouped by severity (error / warning / info)
   - Download annotated DOCX button
   - Export report buttons (JSON, CSV)
   ↓
8. Cron task (every 15 min): DELETE FROM jobs WHERE expires_at < now
   - Cascades essay blob + annotated DOCX + report
```

### 6.2 LTI 1.3 launch variant
LMS POSTs an LTI launch JWT → API verifies via cached JWKS → creates a short-lived `LtiSession` bound to the LTI context → serves the same frontend with LTI context attached. On job completion, if AGS is configured for that deployment, the worker submits a score line item back to the LMS.

### 6.3 CLI variant
`apa7-check essay.docx` reads the file locally, calls the library directly. No API, worker, DB, or Redis involved.

### 6.4 REST API variant
Same as web upload but with API-key auth. Caller manages polling. Returns the report payload + a presigned-style download URL for the annotated DOCX.

---

## 7. Error handling

### 7.1 Two concepts, kept distinct
- **Issue** — a finding about the user's writing (bad formatting, missing reference, broken DOI). This is the product. Surfaced with severity (`error` / `warning` / `info`), location, explanation, suggested fix.
- **Error** — a system-level failure (couldn't extract text, network down, worker crash). Surfaced as `job.status = failed` with a structured `error.code`, or as per-check degradation notes inside an otherwise-successful report.

### 7.2 Principles
- **Fail-soft per check.** A single unparseable reference becomes an issue, not a job failure.
- **Network checks are best-effort.** If CrossRef is unreachable for one DOI, that reference is marked `existence_check_unavailable`, not falsely flagged as nonexistent.
- **Only catastrophic problems fail the job.** Couldn't extract any text, found zero references AND zero citations, worker crashed mid-run.

### 7.3 Per-category handling

| Category | Failure | Behaviour |
|---|---|---|
| **Extraction** | Encrypted DOCX/PDF | Job fails fast: `error.code = encrypted_input` |
| | Scanned PDF (no extractable text) | Job fails: `error.code = no_extractable_text`, hint to use OCR'd PDF |
| | File > size limit | API rejects with 413 before queuing |
| **Parsing** | No reference list detected | Job succeeds with `report.warnings = ["no_reference_list_found"]`; cross-matching skipped |
| | Single malformed reference | Issue: `severity=error, type=unparseable_reference, span=...` |
| **Validation** | CrossRef 404 | Issue: `severity=error, type=doi_not_found` |
| | CrossRef 429 / timeout / 5xx | Per-reference note `existence_check_unavailable`; retry with exponential backoff (3 tries) before giving up |
| | Total network outage | Existence validator returns degraded report; flagged `degraded_checks: ["existence"]` |
| **Infra** | Worker crash mid-job | arq retries (max 2) with idempotency on `job_id`; if still failing, `status=failed, error.code=internal` |
| **LTI** | Invalid JWT / unknown deployment | 401 with structured `lti_error` |
| | Grade-passback fails | Logged + retried; doesn't fail the validation job |
| **Annotator** | Can't inject DOCX comment for one issue | Comment dropped, logged, job still completes; web view unaffected |

### 7.4 What the user sees
- **Job page**: clear status; if `complete` with degraded checks, banner explaining what couldn't be checked.
- **Issues**: severity-coded, with explanation and fix; never raw stack traces.
- **Errors**: structured `{ code, message, hint }`; never leak internals.

---

## 8. Testing strategy

### 8.1 Where most tests live: `apa7_validator`
The library is pure logic. The validation rules are exactly the kind of bounded, well-specified behaviour that benefits from TDD. Per-rule unit tests will be the bulk of the suite.

- **Per-rule unit tests** — one test (or small group) per APA 7 formatting rule: author order, et al. threshold, italics in journal titles, DOI vs URL, year placement, hanging indent, etc.
- **Parser golden tests** — small text fixtures → expected `Reference` / `Citation` dataclasses.
- **Cross-matching tests** — combinatorial fixtures (citations + references) → expected issue list.
- **Existence client tests** — VCR-style recorded cassettes for CrossRef / Unpaywall / OpenLibrary. **Zero live network in CI.**
- **End-to-end engine tests** — small canonical DOCX and PDF fixtures (3–5 of each) → expected `Report`.

### 8.2 Service-level
- **API tests** — pytest + `httpx.AsyncClient`, engine called with stubbed clients. LTI launch tests use a fake LMS keyset.
- **Worker tests** — call task functions directly. Separate test for the TTL-delete cron.
- **Frontend tests** — component tests for the report renderer + a couple of Playwright smoke tests for upload → annotated DOCX download.

### 8.3 Stack-level
- **One docker-compose smoke test** — boots api + worker + postgres + redis, uploads a known fixture, asserts the annotated DOCX comes back with the expected comment count.

### 8.4 CI (GitHub Actions on MQ-EdTech)
- Lint (ruff) + types (mypy or pyright) + unit + service + smoke.
- Cassettes committed.
- Coverage gate on the engine package (target: high); looser on services.

### 8.5 Test data sourcing
- **Synthetic fixtures only** — references constructed for testing, not real student work. Privacy-safe and deterministic.
- **APA 7 manual examples** — used as canonical "correct" references (short excerpts; fair-use scope).
- **No real student work**, ever, in fixtures or test data.

### 8.6 TDD discipline
Per `superpowers:test-driven-development`: write the failing test before the implementation for every validation rule. APA 7 rules are an excellent fit — bounded, well-specified, individually testable.

---

## 9. Privacy posture

### 9.1 Data categories handled

| Category | Sensitivity | Where it lives |
|---|---|---|
| Essay text (paste / extracted) | **High** | Worker memory + Postgres `job.essay_blob`, TTL 24h |
| Reference list strings | Medium | Same as essay |
| Parsed references (Author, Year, DOI, …) | Low — academic metadata | Postgres `job.report`, TTL 24h |
| DOIs / ISBNs / URLs | None — public identifiers | Sent outbound to lookup APIs |
| Annotated DOCX | **High** — derived from essay | Postgres blob, TTL 24h |
| LTI claims: `sub`, `context`, `roles` | Medium | Postgres `lti_session`, session-lifetime |
| LTI claims: `name`, `email`, `lis_person_sourcedid` | **High** | **Discarded at the LTI handler boundary by default** |
| Job metadata (id, timing, status, error codes) | None | Postgres + structured logs |

### 9.2 Data lifecycle
- **Entry**: upload (REST), LTI launch, or paste. Size capped at the API edge.
- **Processing**: held in worker memory only; never written to disk outside the Postgres-backed job blob.
- **At rest**: essay + annotated DOCX encrypted-at-rest via deployment's disk encryption (documented as a deployment prerequisite — we do not roll our own crypto).
- **Deletion**: hard delete (DELETE, not soft-delete), enforced by a cron task every 15 minutes. Default TTL = 24h, deployment-configurable via `JOB_TTL_HOURS`. Users can immediately delete via `DELETE /v1/jobs/{id}`.

### 9.3 Third-party egress — explicit allowlist
Only these identifiers leave the box, only to these endpoints:

- **CrossRef** (`api.crossref.org`) — DOI strings only.
- **Unpaywall** (`api.unpaywall.org`) — DOI strings + a configured contact email (their API requirement; not the user's email).
- **OpenLibrary** (`openlibrary.org`) — ISBN strings only.

**Essay text never egresses.** No analytics SDK, no Sentry-with-payloads, no LLM API calls in v1. (If v2 stretch goal lands, this section gets revised.) Outbound calls go through a single `clients/` layer; a structural unit test fails CI if any client function accepts a parameter named `text`, `essay`, `body`, or `content`.

### 9.4 Logging policy
- Structured JSON, request IDs propagated API → worker via queue payload.
- **Allowlist, not blocklist** — a `safe_log()` wrapper accepts only known-safe fields (`job_id`, `status`, `duration_ms`, `error_code`, `reference_count`, `issue_count`, etc.). Anything else is dropped at the logger level.
- LTI: log `sub` claim only — not `name`, `email`, or `lis_person_sourcedid`.
- Repo-level test grep-checks for direct `logger.info(essay=…)`-style misuse.

### 9.5 In-transit
- TLS required at the edge (Caddy in front of the API; auto-cert for self-hosted demo).
- All third-party lookups via HTTPS.
- Internal docker network not exposed to the host beyond the frontend/api ports.

### 9.6 AuthZ on jobs
- `GET /v1/jobs/{id}` and `GET /v1/jobs/{id}/annotated.docx` require the same auth context that created the job: session cookie, LTI session, or owning API key. **No anonymous job lookup.** Job IDs are UUIDv4 but treated as secrets regardless.

### 9.7 LTI claim minimisation
At the LTI handler boundary, only `iss`, `sub`, `aud`, `nonce`, `deployment_id`, and `context.id` are persisted by default. `name`, `email`, `picture`, `lis_person_sourcedid` are dropped unless a deployment explicitly opts in via `LTI_PERSIST_PII=true` (e.g., for grade-passback that requires identification). Opt-in is per-deployment, logged at admin level.

### 9.8 User-visible disclosure
A **Privacy notice page** is part of the frontend, linked from every upload screen and LTI launch. Plain English:

> Your essay is processed once and stored for up to 24 hours, then permanently deleted. We send only reference identifiers (DOIs, ISBNs, URLs) to external lookup services to verify they exist. We never share your essay text with any third party. You can delete your submission immediately at any time.

The annotated DOCX download page warns: *"Once you download this file, it's on your device — we no longer control it."*

### 9.9 User controls
- `DELETE /v1/jobs/{id}` — immediate hard delete.
- "Delete my submission" button on the results page, same effect.
- Per-deployment env vars: `JOB_TTL_HOURS` (default 24), `LTI_PERSIST_PII` (default false).

### 9.10 Telemetry
- **Aggregate counters only**: jobs/day, p95 processing time, error-code distribution. Never per-essay payloads.
- No third-party analytics in v1.
- If error tracking is added later (e.g., Sentry), it must use a redaction layer that drops every field not on the safe-log allowlist.

### 9.11 Threat model — what's in scope
- **In scope**: accidental data leakage via logs or error pages, unauthorised job access, third-party egress of sensitive content.
- **Out of scope for v1**: targeted attackers, correlation attacks across multiple submissions, dependency supply-chain attacks (handled by standard CI scans, not deeply analysed). Revisit before any production rollout.

### 9.12 MQ-EdTech repo hygiene
- `.gitignore`: `.env*`, `*.docx`, `*.pdf` except `tests/fixtures/**` (explicitly allowlisted).
- Pre-commit hook: scan staged files for `mq.edu.au` URLs, OneID strings, common student-ID patterns.
- No real student work in fixtures — synthetic only. Documented in `CONTRIBUTING.md`.

---

## 10. Operational considerations

- **Repo layout** — single monorepo (`mq-edtech/apa7-reference-checker`):
  ```
  packages/engine/      # apa7_validator
  packages/api/         # FastAPI service
  packages/worker/      # arq worker
  packages/cli/         # typer CLI
  apps/frontend/        # SPA (framework TBD)
  docker-compose.yml
  docs/
  ```
  Single CI, lockstep versioning. Engine may be published to PyPI later if useful.

- **Versioning** — semver on the engine package. URL-versioned REST (`/v1/...`). LTI under `/lti/v1/...`.

- **Rate limiting** — token-bucket on the API edge. Per-IP for anonymous, per-API-key for authed. Important for the public demo so it doesn't get hammered. Caddy or in-app middleware.

- **Performance budget** — soft target: 5000-word essay with 30 references validated in <30s (dominated by parallel CrossRef calls). Useful as a regression signal.

- **License** — **PLACEHOLDER** — Aaron to choose (MIT vs Apache-2.0 are sensible defaults for an MQ-EdTech tool). Default to MIT unless legal/IP considerations push otherwise.

- **Configuration** — 12-factor: all config via env vars. `.env.example` checked into repo with documented defaults. Secrets (LTI private key, optional Sentry DSN later) loaded from env at startup.

- **Health checks** — `GET /healthz` (liveness) and `GET /readyz` (DB + Redis connectivity) on the API; arq's built-in worker health endpoint exposed.

---

## 11. Out of scope (v1)

Explicitly flagged as v2+ or never:
- Citation styles other than APA 7.
- Semantic claim-evidence validation (the original stretch goal).
- OCR for scanned PDFs.
- Non-English references.
- Multi-tenant admin UI.
- Persistent user submission history.
- Production deployment to MQ infrastructure.
- Accessibility audit beyond basic semantic HTML and ARIA labels in the SPA.
- Frontend framework choice (deferred until frontend implementation starts).

---

## 12. Open questions / deferred decisions

| # | Question | When to resolve |
|---|---|---|
| 1 | License (MIT vs Apache-2.0)? | Before first commit pushed to MQ-EdTech remote |
| 2 | DOCX comment-injection library (python-docx, lxml direct, or a maintained fork)? | Implementation-time spike before committing to an approach |
| 3 | Frontend framework? | Before frontend implementation begins |
| 4 | What does the LTI tool consumer-key registration UX look like for deployers? | LTI implementation phase |
| 5 | Should the CLI support batch mode (a directory of essays)? | After v1 ships, based on marker feedback |

---

## 13. References

- APA Style 7th edition — Publication Manual of the American Psychological Association (2020).
- IMS Global LTI 1.3 Core Specification.
- CrossRef REST API documentation.
- Unpaywall API documentation.
- Open Library API documentation.
