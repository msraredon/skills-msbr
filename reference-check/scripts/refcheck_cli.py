#!/usr/bin/env python3
"""refcheck command-line pipeline.

    python3 refcheck_cli.py DOCUMENT [-o OUTDIR] [--no-resolve]

Runs: ingest -> (verify/enrich online) -> emit reference library (5 formats),
audit table (per-citation) and library table (per-work) as CSV + XLSX, plus a
machine-readable JSON artifact and a human 'needs review' report.

Only the .docx path is wired up in Phase 1; other formats raise a clear error.
The ``summary`` / ``connection`` / ``appropriateness`` columns are intentionally
left blank here — they are filled by the model in the hybrid workflow.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

# allow running from anywhere: put this file's dir on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from refcheck.docx_ingest import ingest_docx           # noqa: E402
from refcheck.resolve import Resolver                    # noqa: E402
from refcheck import exporters, tabulate                 # noqa: E402


def ingest_any(path: str):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        return ingest_docx(path)
    raise SystemExit(
        f"Phase 1 supports .docx only; got '{ext}'. "
        "LaTeX/Markdown/PDF/plain-text ingest are planned (see SKILL.md)."
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract, verify, and tabulate references.")
    ap.add_argument("document", help="Input document (.docx in Phase 1)")
    ap.add_argument("-o", "--outdir", default=None, help="Output directory")
    ap.add_argument("--no-resolve", action="store_true",
                    help="Skip online verification/enrichment (offline, embedded data only)")
    ap.add_argument("--cache", default=None, help="Path to HTTP cache JSON")
    args = ap.parse_args()

    doc = os.path.abspath(args.document)
    if not os.path.exists(doc):
        raise SystemExit(f"No such file: {doc}")
    stem = os.path.splitext(os.path.basename(doc))[0]
    outdir = os.path.abspath(args.outdir or (os.path.dirname(doc) + f"/{stem}_references"))
    os.makedirs(outdir, exist_ok=True)
    cache = args.cache or os.path.join(outdir, ".http_cache.json")

    print(f"[1/4] Ingesting {os.path.basename(doc)} ...")
    ing = ingest_any(doc)
    references = ing.references
    st = ing.to_dict()["stats"]
    print(f"      {st['n_citations']} citations, {st['n_references']} unique references "
          f"({st['n_refs_cited']} cited), {st['n_unresolved_citations']} citations unlinked")

    if not args.no_resolve and references:
        n = len(references)
        print(f"[2/4] Verifying {n} references online (Crossref + PubMed) ...")
        R = Resolver(cache_path=cache)
        for i, num in enumerate(sorted(k for k in references if k >= 0), 1):
            references[num] = R.resolve_work(references[num])
            print(f"      ({i}/{n}) ref {num}   ", end="\r")
        R.save()
        print()
    else:
        print("[2/4] Skipping online verification (--no-resolve).")

    print("[3/4] Writing reference library (CSL-JSON, BibTeX, RIS, .enw, Zotero RDF) ...")
    work_list = [references[n] for n in sorted(references) if n >= 0]
    lib_paths = exporters.write_library(work_list, os.path.join(outdir, f"{stem}_library"))

    print("[4/4] Writing tables and review report ...")
    audit = tabulate.build_audit_rows(ing.citations, references)
    library = tabulate.build_library_rows(references, ing.citations)
    tabulate.write_csv(audit, tabulate.AUDIT_COLUMNS, os.path.join(outdir, f"{stem}_audit.csv"))
    tabulate.write_csv(library, tabulate.LIBRARY_COLUMNS, os.path.join(outdir, f"{stem}_references_table.csv"))
    xlsx = os.path.join(outdir, f"{stem}_references.xlsx")
    tabulate.write_xlsx(audit, library, xlsx)

    # machine-readable artifact for the model / resumability
    with open(os.path.join(outdir, f"{stem}_refcheck.json"), "w", encoding="utf-8") as fh:
        json.dump(ing.to_dict(), fh, indent=2, ensure_ascii=False)

    _write_report(ing, references, outdir, stem)

    print(f"\nDone. Outputs in: {outdir}")
    for k, p in lib_paths.items():
        print(f"  library.{k:8s} {os.path.basename(p)}")
    print(f"  table (xlsx)   {os.path.basename(xlsx)}")
    print(f"  audit  (csv)   {stem}_audit.csv")
    print(f"  review report  {stem}_REVIEW.md")
    return 0


def _write_report(ing, references, outdir, stem) -> None:
    refs = {n: w for n, w in references.items() if n >= 0}
    unlinked = [c for c in ing.citations if not c.ref_numbers]
    unverified = [
        (n, w) for n, w in sorted(refs.items())
        if w.get("custom", {}).get("verification", {}).get("status") != "verified"
    ]
    lines = [f"# Reference review — {stem}", ""]
    lines.append(f"- Citations found: **{len(ing.citations)}**")
    lines.append(f"- Unique references: **{len(refs)}**")
    lines.append(f"- References verified online: **{len(refs) - len(unverified)}**")
    lines.append(f"- References needing human review: **{len(unverified)}**")
    lines.append(f"- Citations with no reference link: **{len(unlinked)}**")
    lines.append("")
    if unverified:
        lines.append("## References flagged for human review")
        lines.append("")
        lines.append("Could not be confidently verified online (check the original "
                     "citation, or add a DOI/PMID by hand).\n")
        for n, w in unverified:
            v = w.get("custom", {}).get("verification", {})
            raw = w.get("custom", {}).get("bib_raw", "")
            title = w.get("title") or raw[:90] or "(no title)"
            lines.append(f"- **[{n}]** {title} — score={v.get('match_score')} "
                         f"DOI={w.get('DOI')} PMID={w.get('custom',{}).get('pmid')}")
        lines.append("")
    if unlinked:
        lines.append("## Citations with no reference link")
        lines.append("")
        for c in unlinked:
            snip = (c.sentence[:140] + "…") if len(c.sentence) > 140 else c.sentence
            lines.append(f"- `[{c.marker}]` ({c.note or ''}) — {snip}")
        lines.append("")
    with open(os.path.join(outdir, f"{stem}_REVIEW.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


if __name__ == "__main__":
    raise SystemExit(main())
