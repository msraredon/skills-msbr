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
| `<stem>_references.xlsx` | two sheets: **Audit (per citation)** and **Library (per work)**, with hyperlinked DOI/PMID/URL |
| `<stem>_audit.csv`, `<stem>_library.csv` | same tables as CSV |
| `<stem>_library.{csl.json,bib,ris,enw,rdf}` | the reference library in five formats |
| `<stem>_refcheck.json` | machine-readable artifact (citations + works) — **your input for step 2** |
| `<stem>_REVIEW.md` | citations lacking metadata + works that failed verification |

The `summary`, `connection`, and `appropriateness` columns are left **blank** by
the script — they are yours to fill.

Flags to know: `--no-resolve` (offline; embedded metadata only),
`--cache PATH` (reuse HTTP responses across runs).

### 2. Fill the judgment columns (your job)
Load `<stem>_refcheck.json`. For each **resolved** citation, read the
`sentence` and the linked work's `abstract` (and title/journal), then produce:

- **summary** — 1–2 sentences on the reference's main point (from the abstract).
- **connection** — one sentence on how the reference relates to the cited
  sentence.
- **appropriateness** — one of `Supports` / `Partial` / `Unclear` / `Mismatch`.
  Flag anything below `Supports` for human review.

When open-access full text is available (PubMed Central / Unpaywall) and the
claim is specific, prefer it over the abstract. If neither abstract nor full
text is obtainable, set appropriateness to `Unclear` and flag it.

Write these back into the CSV/XLSX (or regenerate the table with the values).
Do **not** invent support: if the abstract does not clearly back the claim, say
so — a flagged citation is a useful result, not a failure.

### 3. Handle unresolved citations
`<stem>_REVIEW.md` lists in-text citations with no embedded metadata (common
when a Word doc's EndNote/Zotero bibliography has not been generated, or the
field data was stripped). To resolve them, ask the user for **the source
reference-manager library** (EndNote `.xml`/`.ris`/`.enw`, Zotero, or a `.bib`),
or a version of the document with the **bibliography generated** so the
reference list can be parsed and searched online. Never silently drop them.

### 4. Report
Summarize: N citations, N verified, N flagged for appropriateness, N unresolved.
Point the user at the xlsx and the library files, and list what needs human eyes.

## Reverse mode (library → table)
If given only a reference library (`.bib`/`.ris`/`.enw`/CSL-JSON) and no source
document, produce the library table and verify identifiers, but **omit the
appropriateness column** (there is no citing sentence to judge against).
*(Library ingest is being wired up; until then, convert the library to
CSL-JSON and feed the works through the resolver + tabulate steps.)*

## Input formats
- **.docx** — supported now. Reads Word field codes directly, including EndNote
  "traveling library" records (authoritative DOI/PMID) and the rendered
  in-text marker; maps every citation to its sentence.
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
