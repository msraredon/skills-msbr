---
name: reference-check
description: >-
  Extract, verify, and tabulate the references in a scholarly document (Word
  .docx now; LaTeX/Markdown/PDF/plain-text planned). Confirms every citation is
  real via DOI/PMID/working URL, builds a per-citation audit table and a
  de-duplicated reference library in five manager formats (CSL-JSON, BibTeX,
  RIS, EndNote .enw, Zotero RDF), and judges whether each reference actually
  supports the sentence that cites it. Use when a user wants to check, validate,
  reformat, or tabulate citations/references/bibliography in a paper, grant,
  or write-up, or to convert a reference library into a summary table.
---

# reference-check

Pick up a document in (nearly) any form and answer three questions for every
citation: **(1)** what is it, **(2)** does it actually exist (verifiable by a
human via DOI / PMID / working URL), and **(3)** does it actually support the
sentence it is attached to. Deliver that as a reviewer-friendly table plus a
clean reference library that imports into EndNote, Zotero, Mendeley, and LaTeX.

This is a **hybrid** skill: deterministic Python scripts do the parsing,
online verification, and file generation; you (the model) do the appropriateness
judgment, because that requires reading the abstract/full text against the
cited claim.

## When to use

- "Check / validate / clean up the references in this paper (grant, write-up)."
- "Make me a reference table / bibliography from this document."
- "Are these citations real? Do they say what we claim they say?"
- "Convert this .bib / EndNote library into a summary table." (reverse mode)

## The lab standard

The definition of a correct, complete reference lives in
[standards/lab-reference-standard.md](standards/lab-reference-standard.md):
required fields, identifier priority (DOI **and** PMID when both exist), the
audit-table columns, the flagging rules, and the library export formats. Read it
before running so outputs match lab convention; edit it to change the standard.

## Workflow

### 0. Locate scripts and dependencies
Scripts are in `scripts/`. Only dependency beyond the standard library is
`openpyxl` (for the .xlsx table); CSV/library outputs work without it. See
`requirements.txt`.

### 1. Run the deterministic pipeline
```bash
python3 scripts/refcheck_cli.py "<document.docx>" -o "<outdir>"
```
This ingests the document, verifies each work online (Crossref + NCBI
E-utilities), and writes into `<outdir>`:

| file | contents |
|------|----------|
| `<stem>_references.xlsx` | two sheets: **Citations (audit)** — a linear list of citations, each expanded to one row per referenced work with the citation cells merged; and **References (library)** — one row per unique reference. DOI/PMID/URL hyperlinked; flagged rows highlighted |
| `<stem>_audit.csv`, `<stem>_references_table.csv` | the two tables as CSV (flat, for filtering) |
| `<stem>_library.{csl.json,bib,ris,enw,rdf}` | the reference library in five formats |
| `<stem>_refcheck.json` | machine-readable artifact (citations + references) — **your input for step 2** |
| `<stem>_REVIEW.md` | references that failed online verification + any unlinked citations |

**Data model:** a *reference* is a unique numbered work (the bibliography number
is its id); a *citation* is one in-text marker tied to one sentence, linking to
one or more references; **appropriateness is judged per (citation, reference)
pair.** References come from two sources unified by number — records embedded in
citation fields (authoritative), and the rendered numbered bibliography (usually
the only complete source). Read both.

The `ref_summary`, `connection`, and `appropriateness` columns are left **blank**
by the script — they are yours to fill.

Flags to know: `--no-resolve` (offline; embedded metadata only),
`--cache PATH` (reuse HTTP responses across runs).

### 2. Fill the judgment columns (your job)
Load `<stem>_refcheck.json`. It has `citations` (each with `ref_numbers` and a
`sentence`) and `references` (keyed by number, each with metadata + `abstract`).
For each (citation, reference) pair, read the sentence and the reference's
abstract (and title/journal), then produce:

- **ref_summary** — 1–2 sentences on the reference's main point (from abstract).
  (Same for every citation of that reference; also fill the library sheet.)
- **connection** — one sentence on how the reference relates to *this* sentence.
- **appropriateness** — one of `Supports` / `Partial` / `Unclear` / `Mismatch`.
  Flag anything below `Supports` for human review.

When open-access full text is available (PubMed Central / Unpaywall) and the
claim is specific, prefer it over the abstract. If neither abstract nor full
text is obtainable, set appropriateness to `Unclear` and flag it.

Write these back into the CSV/XLSX (or regenerate the table with the values).
Do **not** invent support: if the abstract does not clearly back the claim, say
so — a flagged citation is a useful result, not a failure.

### 3. Handle flagged references
`<stem>_REVIEW.md` lists references that could not be confidently verified
online (low bibliographic-match score, or no identifier). These usually need a
human to confirm the DOI/PMID. If **no** bibliography exists in the document and
citations are data-less, ask the user for the source reference-manager library
(EndNote `.xml`/`.ris`/`.enw`, Zotero, `.bib`) or a document version with the
**bibliography generated** (EndNote → "Update Citations and Bibliography"), then
re-run. Never silently drop a citation or reference.

### 4. Report
Summarize: N citations, N references, N verified, N flagged for verification,
N flagged for appropriateness. Point the user at the xlsx and library files, and
list what needs human eyes.

## Reverse mode (library → table)
If given only a reference library (`.bib`/`.ris`/`.enw`/CSL-JSON) and no source
document, produce the library table and verify identifiers, but **omit the
appropriateness column** (there is no citing sentence to judge against).
*(Library ingest is being wired up; until then, convert the library to
CSL-JSON and feed the works through the resolver + tabulate steps.)*

## Input formats
- **.docx** — supported now. Reads Word field codes directly, including EndNote
  "traveling library" records (authoritative DOI/PMID) and the rendered in-text
  marker, **and** the rendered numbered bibliography (`EN.REFLIST` /
  `EndNoteBibliography` paragraphs). Unifies both by reference number and maps
  every citation to its sentence. Bibliography-only references are resolved by
  Crossref bibliographic search with a similarity guard.
- **LaTeX / Markdown / PDF / plain text** — planned. LaTeX will use the `.bib` +
  `\cite` keys; Markdown/text will parse a numbered or author-year reference
  list; PDF will extract text and reference list. See
  [references/citation-styles.md](references/citation-styles.md).

## Design notes
- Canonical model is CSL-JSON; every export derives from it (no lossy
  round-trips). PMID/PMCID/verification live under a `custom` key.
- Works are de-duplicated by DOI, then PMID, then title+year hash.
- All APIs are free/keyless. Set `NCBI_API_KEY` and `REFCHECK_CONTACT` env vars
  to raise rate limits and set the Crossref polite-pool contact.
