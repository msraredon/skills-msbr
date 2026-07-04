# CLAUDE.md — reference-check

Skill-specific working notes. For repo-wide conventions see the
[root CLAUDE.md](../../CLAUDE.md). For usage see [README.md](README.md); for the
skill contract see [SKILL.md](SKILL.md).

## What this skill does
Extract → verify → tabulate references in a scholarly document, and judge
whether each reference supports the sentence citing it. Deterministic Python does
parsing/verification/exports; the model does the appropriateness judgment.

## Maturity scorecard

> A candid self-assessment for advanced technical/scientific users, kept here so
> it can be revisited and driven upward. **Update the date/version and re-score
> whenever the skill materially changes.** Scores are /10; be honest, not kind —
> an inflated score hides the next improvement.

**Last scored: 2026-07-04 · v0.3.0 · Overall 7.5 / 10**

Frame of reference: well above a typical "prompt + helper script" skill (real
domain logic, external-API verification, a genuine refuse-to-guess correctness
stance). Narrower and less battle-tested than mature general-purpose skills
(`docx`/`pdf`/`xlsx`): higher domain rigor, lower breadth and automation.

| Dimension | Score | Why / what would raise it |
|-----------|:----:|---------------------------|
| Problem value / impact | 9 | Citation integrity is high-stakes and underserved. Ceiling only if it spans more of the writing workflow. |
| Correctness & scientific rigor | 8.5 | Precision-first, year-gated, cross-verified, refuses to guess; caught a real mis-citation. Held back: appropriateness accuracy is **unbenchmarked**; ~8% of refs are text-less (title-only judgment). |
| Input coverage / robustness | 5 | **.docx only**, numbered styles only, one EndNote flavor truly tested. No LaTeX/PDF/Markdown, no author-year, reverse mode unwired, thin non-journal (book/preprint/dataset/software) handling. This is the biggest gap. |
| Automation / workflow UX | 6 | One-command deterministic pipeline is smooth; appropriateness is a 3-step prepare→judge→apply loop needing the model each run, and it's slow-ish at grant scale (100s of refs). |
| Architecture & maintainability | 8.5 | Clean CSL-JSON canonical model, layered modules, standards-as-source-of-truth, easy to extend. |
| Testing & validation | 6.5 | Good unit tests for the tricky logic + real-manuscript validation, but **no eval harness for appropriateness accuracy**, no CI, single test corpus. |
| Documentation | 8.5 | Nested README/CLAUDE/SKILL + editable standard; thorough. |

**Top levers to raise the overall score (highest-ROI first):**
1. **LaTeX + PDF ingest** (coverage 5→8): unlocks most technical users; biggest single lever.
2. **An appropriateness eval harness** (rigor + testing): a labeled set of (sentence, reference, verdict) to measure precision/recall of the judgment and catch regressions — turns "trust me" into a number.
3. **Fully automated appropriateness** in one command (UX 6→8), with OA full text used by default for specific claims.
4. **Reverse mode + library dedup/merge** (coverage): library-in → table-out, and cross-document de-duplication for lab-wide use.
5. **Broaden reference types & citation styles** (author-year, books, preprints, datasets, software).

A realistic ceiling with 1–3 done is ~9/10 for this niche; 8.5+ overall once coverage and a measured appropriateness accuracy exist.

## Roadmap: toward a general, trustworthy, lab-wide tool

Ideas for evolving this from "excellent for numbered-citation Word docs" into a
tool the whole lab — including naive users — can trust on any document. Grouped
by goal; the scorecard's "top levers" are the near-term subset of this.

### A. Truly general (ingest & reference types)
- **LaTeX ingest** — parse `.tex` + `.bib`/`.bbl`; handle `\cite/\citep/\citet/
  \autocite/\footcite` and biblatex; sentence = text around the cite. *(Flagship;
  most technical users write here.)*
- **PDF ingest** — extract text + reference list; use GROBID for structured
  reference parsing (the scholarly-PDF gold standard); OCR fallback for scans.
  Lets us check *other* labs' published papers, not just our own drafts.
- **Markdown / plain text** — pandoc `[@key]` + CSL-JSON/bib, or a numbered /
  author-year reference list.
- **More citation managers** — Zotero (`ZOTERO_ITEM` CSL-JSON) and Mendeley
  (`MENDELEY_CITATION`) Word field codes; direct readers for the Zotero and
  EndNote SQLite libraries. Google Docs (export/API) — increasingly common.
- **Citation styles** — author-year and footnote styles, not only numbered.
- **Reference types beyond journal articles** — books (ISBN → OpenLibrary/Google
  Books), chapters, preprints (bioRxiv/medRxiv/arXiv), datasets (DataCite),
  software (Zenodo/CITATION.cff), clinical trials (NCT), patents, web pages
  (with archived snapshot + accessed date).
- **Reverse mode, fully wired** — library in (`.bib`/`.ris`/`.enw`/CSL-JSON/
  EndNote XML/Zotero) → verified table out.

### B. Widely applicable (beyond one lab's conventions)
- **Any output CSL style** — use a CSL processor to emit/reformat the
  bibliography in any journal style (APA, Vancouver, Nature, Cell…). Turns the
  skill into a *reformatter*, not just a checker — "convert my refs to Cell style."
- **Journal-requirement presets** — per-target rules (PMIDs required? DOIs?
  max authors? abbreviated journals?) checked before submission.
- **Broader identifier coverage** — add OpenAlex (huge, free), Semantic Scholar,
  DataCite, arXiv, and ADS (astro) so non-PubMed/Crossref fields resolve too.
- **Scale** — async/batched lookups and NCBI-key rate limits for 300+-reference
  grants; a batch mode over a whole folder / the lab's back-catalog.

### C. Trustworthy (verifiability & measured accuracy)
- **Appropriateness eval harness** — a labeled gold set of (sentence, reference,
  verdict); report precision/recall and guard against regressions. *(Flagship;
  turns "trust me" into a number.)*
- **Retraction & correction checks** — flag cited works that are retracted or
  under an expression of concern (Crossref update-to / Retraction Watch). High
  scientific-integrity value; naive users especially benefit.
- **Quote-grounded support** — for a specific/quantitative claim, locate and
  quote the supporting passage from OA full text, rather than just a verdict.
  Reduces hallucinated "support" and gives the author receipts.
- **Venue-quality flags** — predatory/questionable venues (DOAJ membership,
  journal metrics) so weak sources surface.
- **Bibliometric hygiene** — self-citation rate, reference-age distribution,
  possible missing seminal works, over-reliance on one group.
- **Provenance & reproducibility** — every field shows its source and which match
  signals fired; a run manifest (timestamps, API versions) for auditability.
- **Judgment robustness** — two independent appropriateness passes with
  disagreement flagged, and explicit abstention when evidence is thin.

### D. Lab-wide & naive-user-ready (UX, safety, distribution)
- **One command, end to end** — `refcheck <doc>` runs ingest → verify → *and* the
  appropriateness judgment automatically (model via API/SDK), so no one
  orchestrates a prepare→judge→apply loop.
- **A human-readable report** — an HTML/PDF summary with flagged items front and
  center, color-coded, plain-English ("12 citations need your attention, and
  why"), shareable with co-authors — not only a spreadsheet.
- **In-document annotations** — optionally write Word/PDF comments back at each
  flagged citation so the author sees issues *in context*. Big win for novices.
- **Guardrails** — never overwrite the source; clearly named output folder;
  friendly errors; auto-detect format; graceful degradation without `openpyxl`.
- **Privacy-first & explicit** — unpublished manuscripts stay local; state plainly
  what leaves the machine (only identifiers/titles to public APIs), with an
  offline/`--no-resolve` mode for sensitive drafts.
- **Shared lab assets** — a canonical, de-duplicated lab reference library that
  grows across projects, and a shared API cache so refs resolve once for everyone.
- **Onboarding** — `--demo` mode, a 2-minute quickstart, worked examples.
- **Integration** — pre-submission checklist; a CI hook for LaTeX/Overleaf repos
  that checks references on every commit.

### Suggested sequencing
1. LaTeX ingest + reverse mode (unlock the most users and inputs).
2. Appropriateness eval harness + one-command automation (trust + UX together).
3. Retraction checks + quote-grounded support (highest-integrity trust features).
4. HTML report + in-document annotations (naive-user experience).
5. PDF/GROBID ingest, broader identifiers, CSL restyling (breadth).
6. Shared lab library/cache, CI integration (institutionalize it).

## Architecture (`scripts/refcheck/`)
- `model.py` — canonical CSL-JSON work dict; identifier normalization
  (`normalize_doi`, `normalize_pmid`); `Citation` dataclass; `work_key` dedup.
- `endnote.py` — parse EndNote traveling-library `<record>` XML → works.
- `bibliography.py` — parse the rendered numbered bibliography (`EN.REFLIST` /
  `EndNoteBibliography` paragraphs); `expand_marker("8-10") -> [8,9,10]`.
- `docx_ingest.py` — field-aware .docx walker (respects nested `fldChar`
  begin/separate/end); unifies embedded records + bibliography by reference
  number; maps each citation to its sentence.
- `resolve.py` — Crossref (DOI) + NCBI E-utilities (PMID) verification, DOI↔PMID
  cross-fill, abstracts; `best_bibmatch` resolves bibliography-only entries by
  Crossref bibliographic search behind a title-token similarity guard.
- `tabulate.py` — the two tables (grouped audit, per-reference library); merges
  citation cells in xlsx; accepts a `judgments` dict to fill/flag.
- `exporters.py` — CSL-JSON / BibTeX / RIS / .enw / Zotero RDF from the one model.

Entry points: `scripts/refcheck_cli.py` (ingest→verify→tables+library),
`scripts/refcheck_appraise.py` (`prepare` pairs → judge → `apply`).

## Key lessons (don't relearn these)
- **A reference can live in two places**: embedded in the citation field *and* in
  the rendered bibliography. In real EndNote docs many citations are data-less;
  only the bibliography is complete. **Read both, unify by reference number.**
- **Reference number is the linkage key** and matches what the author sees. In-
  text marker → numbers → references; appropriateness is per (citation, ref).
- **EndNote nests fields** (`EN.CITE` wraps `EN.CITE.DATA`); never concatenate all
  `instrText` globally — walk the field stack and bubble child records up.
- **Precision-first matching (v0.3).** Bibliography-only entries resolve by
  searching an *extracted title* (see `bibliography.extract_title`), scoring
  three signals (title tokens, author surnames, year), and accepting only via
  `_accept` — which is **year-gated** (a wrong-year candidate is never accepted,
  ±1 for epub/print). Strategies are tried in order **PubMed-first, then
  Crossref** (biomedical corpus → PMID + abstract + canonical DOI, and avoids
  conference-abstract duplicate DOIs). This eliminated both the earlier false
  flags and the false positives; never loosen the year gate to chase recall.
- **Cache only successes.** `_get` must not cache failed/empty responses, or a
  transient timeout poisons the cache and silently drops abstracts.
- **Never fabricate support.** No abstract → `Unclear` + flag. A `Mismatch` (e.g.
  a mis-numbered citation) is a valuable finding, not a failure.

## Extending
- New ingest format: produce the same `(citations, references)` shape as
  `docx_ingest`. LaTeX = `.bib` + `\cite`; Markdown/PDF = parse the reference
  list + markers. See `references/citation-styles.md`.
- New manager format: add an exporter in `exporters.py` deriving from CSL-JSON.
- Reverse mode: feed a library's works through `resolve` + `tabulate` (omit
  appropriateness — there is no citing sentence).

## Tests
`python3 tests/test_core.py` — plain asserts, no pytest. Cover parsers,
normalization, sentence attachment, and bibliography linkage.

## Gotchas
- Uses free/keyless APIs; set `REFCHECK_CONTACT` (Crossref polite pool) and
  optional `NCBI_API_KEY`. HTTP responses cache to `--cache PATH`.
- `openpyxl` is the only non-stdlib dependency (xlsx only).
- Run artifacts and `demo-inputs/` (unpublished manuscripts) are gitignored.
