# reference-check

**Version 0.3.0**

Check, verify, and tabulate the references in a scholarly document. For every
citation it answers: **is the reference real** (verifiable by a human via a
working DOI / PMID / URL), **what is it** (clean metadata + summary), and **does
it actually support the sentence that cites it**. Outputs a reviewer-friendly
table plus a reference library that imports into EndNote, Zotero, Mendeley, and
LaTeX.

## Quick start

```bash
python3 scripts/refcheck_cli.py "MyPaper.docx" -o out/
```

Produces in `out/`:

- **`MyPaper_references.xlsx`** — two sheets:
  - **Citations (audit)** — a linear list of citations in document order; each
    claim is shown once and its reference(s) listed beneath it, so you can check
    appropriateness per (sentence, reference) pair. DOI/PMID/URL are clickable;
    flagged rows are highlighted.
  - **References (library)** — one row per unique reference (the numbered list),
    with metadata, verified links, and which citations use it.
- **`MyPaper_library.{csl.json,bib,ris,enw,rdf}`** — the reference library in
  five formats (CSL-JSON, BibTeX, RIS, EndNote, Zotero RDF).
- **`MyPaper_refcheck.json`** — machine-readable citations + references.
- **`MyPaper_REVIEW.md`** — references that need human review.

Options: `--no-resolve` (offline, embedded metadata only), `--cache PATH`
(reuse API responses across runs).

## How it works

A reference lives in up to two places in a Word document: embedded in the
citation field (EndNote "traveling library" records, with authoritative
DOI/PMID) and in the rendered numbered bibliography at the end. **reference-check
reads both** and unifies them by reference number — an in-text marker like
`8-10` links a sentence to references 8, 9 and 10. Each reference is then
verified online (Crossref for DOIs, NCBI E-utilities for PMIDs), with DOI↔PMID
cross-fill and abstract retrieval. Bibliography-only entries are resolved by
Crossref bibliographic search behind a similarity guard, so a weak match is
flagged rather than wrongly accepted.

The `ref_summary`, `connection`, and `appropriateness` columns are filled by
Claude (reading each abstract / open-access full text against the cited claim) —
this is the hybrid step; the scripts handle everything deterministic.

## What "good" looks like

On a real 105-reference manuscript: 75 citations extracted and mapped to
sentences, **all 105 references verified online** (105 DOIs, 103 PMIDs, 96
abstracts, 76 open-access, 61 with PubMed Central full text), **zero false
matches**. Appropriateness across all 124 (citation, reference) pairs: 106
Supports, 8 Partial, 9 Unclear (genuinely text-less), and 1 Mismatch — a
mis-numbered citation the tool caught.

## Data model

| term | meaning |
|------|---------|
| reference | a unique numbered work; the bibliography number is its id |
| citation | one in-text marker tied to one sentence, linking to 1+ references |
| appropriateness | judged per (citation, reference) pair |

## Configuration

- `REFCHECK_CONTACT` — contact email for Crossref's polite pool / NCBI.
- `NCBI_API_KEY` — optional, raises NCBI rate limits.

## The lab standard

[`standards/lab-reference-standard.md`](standards/lab-reference-standard.md)
defines required fields, identifier policy, table columns, flag rules, and
export formats. Edit it to change what the skill produces and flags.

## Dependencies

Standard library only, except `openpyxl` for the `.xlsx` workbook (CSV and
library outputs work without it). See `requirements.txt`.

## Tests

```bash
python3 tests/test_core.py
```

Plain-`assert` tests (no pytest) covering the parsers, identifier normalization,
sentence attachment, and bibliography linkage.

## Roadmap

See the full, prioritized roadmap toward a general, trustworthy, lab-wide tool
(with a maturity scorecard) in [CLAUDE.md](CLAUDE.md). In brief:

- Ingest for LaTeX (`.bib` + `\cite`), Markdown, plain text, and PDF.
- Reverse mode: a reference library in → verified library table out.
- Library de-duplication / merge across documents.
- PDF-text fallback for the ~8% of references with no abstract or PMC full text.

## Changelog

- **0.3.0** — Open-access full text (Unpaywall + PubMed Central); precision-first
  bibliographic matching (title extraction, author+year scoring, year-gated
  acceptance, PubMed-first) that eliminates false matches and false flags;
  appropriateness automated across all pairs.
- **0.2.0** — Parse the rendered bibliography; citation-centric grouped tables.
- **0.1.0** — docx ingest, online verification, five-format library, tables.
