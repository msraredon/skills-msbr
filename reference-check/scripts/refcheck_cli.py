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
    works = ing.works
    st = ing.to_dict()["stats"]
    print(f"      {st['n_citations']} citations, {st['n_works']} unique works, "
          f"{st['n_unresolved_citations']} citations without embedded metadata")

    if not args.no_resolve and works:
        print(f"[2/4] Verifying {len(works)} works online (Crossref + PubMed) ...")
        R = Resolver(cache_path=cache)
        resolved = {}
        for i, (wid, w) in enumerate(works.items(), 1):
            resolved[wid] = R.resolve_work(w)
            print(f"      ({i}/{len(works)}) {wid}", end="\r")
        R.save()
        works = resolved
        print()
    else:
        print("[2/4] Skipping online verification (--no-resolve).")

    print("[3/4] Writing reference library (CSL-JSON, BibTeX, RIS, .enw, Zotero RDF) ...")
    work_list = list(works.values())
    lib_paths = exporters.write_library(work_list, os.path.join(outdir, f"{stem}_library"))

    print("[4/4] Writing tables and review report ...")
    audit = tabulate.build_audit_rows(ing.citations, works)
    library = tabulate.build_library_rows(works, ing.citations)
    tabulate.write_csv(audit, tabulate.AUDIT_COLUMNS, os.path.join(outdir, f"{stem}_audit.csv"))
    tabulate.write_csv(library, tabulate.LIBRARY_COLUMNS, os.path.join(outdir, f"{stem}_library.csv"))
    xlsx = os.path.join(outdir, f"{stem}_references.xlsx")
    tabulate.write_xlsx(
        {"Audit (per citation)": (audit, tabulate.AUDIT_COLUMNS),
         "Library (per work)": (library, tabulate.LIBRARY_COLUMNS)},
        xlsx,
    )

    # machine-readable artifact for the model / resumability
    with open(os.path.join(outdir, f"{stem}_refcheck.json"), "w", encoding="utf-8") as fh:
        json.dump({"stats": st, "citations": [c.to_dict() for c in ing.citations],
                   "works": work_list}, fh, indent=2, ensure_ascii=False)

    _write_report(ing, works, outdir, stem)

    print(f"\nDone. Outputs in: {outdir}")
    for k, p in lib_paths.items():
        print(f"  library.{k:8s} {os.path.basename(p)}")
    print(f"  table (xlsx)   {os.path.basename(xlsx)}")
    print(f"  audit  (csv)   {stem}_audit.csv")
    print(f"  review report  {stem}_REVIEW.md")
    return 0


def _write_report(ing, works, outdir, stem) -> None:
    unresolved = [c for c in ing.citations if not c.work_ids]
    unverified = [
        w for w in works.values()
        if w.get("custom", {}).get("verification", {}).get("status") != "verified"
    ]
    lines = [f"# Reference review — {stem}", ""]
    lines.append(f"- Citations found: **{len(ing.citations)}**")
    lines.append(f"- Unique works with embedded metadata: **{len(works)}**")
    lines.append(f"- Citations lacking embedded metadata: **{len(unresolved)}**")
    lines.append(f"- Works that could not be verified online: **{len(unverified)}**")
    lines.append("")
    if unresolved:
        lines.append("## Citations needing a reference library or manual resolution")
        lines.append("")
        lines.append("These in-text citations carry no embedded record in the document "
                     "(and no bibliography was present to parse). Supply the source "
                     "reference-manager library, or a document version with the "
                     "bibliography generated, to resolve them.\n")
        for c in unresolved:
            snippet = (c.sentence[:140] + "…") if len(c.sentence) > 140 else c.sentence
            lines.append(f"- `[{c.marker}]` — {snippet}")
        lines.append("")
    if unverified:
        lines.append("## Works flagged for human review (unverified online)")
        lines.append("")
        for w in unverified:
            lines.append(f"- {w.get('title','(no title)')} — DOI={w.get('DOI')} "
                         f"PMID={w.get('custom',{}).get('pmid')}")
        lines.append("")
    with open(os.path.join(outdir, f"{stem}_REVIEW.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


if __name__ == "__main__":
    raise SystemExit(main())
