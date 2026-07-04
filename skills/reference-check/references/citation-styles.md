# Citation-style & format ingest notes

Reference notes for extending ingest beyond `.docx`. Each format needs two
things: **enumerate citations with their surrounding sentence**, and **recover
reference metadata** (ideally an identifier).

## Word (.docx) — implemented
Citations are Word *fields*. EndNote encodes them as (often nested) fields whose
code text is `ADDIN EN.CITE` / `EN.CITE.DATA`; the code carries a `<record>`
"traveling library" block (authoritative DOI = `electronic-resource-num`,
PMID = `accession-num` and/or a pubmed URL), and the field *result* is the
rendered marker (e.g. superscript `16`). Zotero/Mendeley use different ADDIN
codes (`ZOTERO_ITEM`, `MENDELEY_CITATION`) carrying JSON — add parsers as needed.
**Caveat observed in the wild:** many citations may have no embedded record and
no generated bibliography; those need the source library or a generated
reference list. Never drop them — flag them.

## LaTeX — planned
- Citations: `\cite{key}`, `\citep`, `\citet`, `\autocite`, etc. → keys.
- Metadata: the `.bib` / `.bbl` file (BibTeX/BibLaTeX). Keys map to entries with
  `doi`, `pmid`, `eprint` fields. Sentence = text around the `\cite`.

## Markdown / plain text — planned
- Pandoc-style `[@key]` with a CSL-JSON/BibTeX file, **or**
- a numbered reference list (`1. Author... DOI...`) with `[1]`/superscript
  in-text markers, **or**
- author-year `(Smith et al., 2020)` with an alphabetical list.
Parse the reference list, resolve each entry online, map markers to entries.

## PDF — planned
- Extract text + the reference list (layout-aware; consider GROBID for
  structured reference parsing). Match in-text markers to list entries. Lowest
  fidelity; always verify identifiers online.

## Identifier resolution when only free text is available
1. Look for an explicit DOI / PMID / arXiv id in the reference string.
2. Else query Crossref (`query.bibliographic`) and PubMed (title+author+year);
   accept the top hit only above a similarity threshold, else flag low-confidence.
