# CLAUDE.md — reference-check

Skill-specific working notes. For repo-wide conventions see the
[root CLAUDE.md](../CLAUDE.md). For usage see [README.md](README.md); for the
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
