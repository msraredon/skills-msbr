#!/usr/bin/env python3
"""Appropriateness appraisal: the hybrid (model-in-the-loop) step.

    # 1. assemble each citation with its references' abstracts to judge:
    python3 refcheck_appraise.py prepare <stem>_refcheck.json -o appraise_input.json

    # 2. (the model reads appraise_input.json and writes judgments.json)

    # 3. write judgments back into the tables and refcheck.json:
    python3 refcheck_appraise.py apply <stem>_refcheck.json judgments.json -o <outdir>

judgments.json schema:
    {
      "references": { "16": {"summary": "<1-2 sentences on the ref's main point>"} },
      "pairs": {
        "C1|16": {"connection": "<how ref 16 relates to C1's sentence>",
                   "appropriateness": "Supports|Partial|Unclear|Mismatch",
                   "notes": "<optional>"}
      }
    }
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from refcheck import tabulate, exporters   # noqa: E402


def _short_abstract(w: dict, limit: int = 900) -> str:
    ab = w.get("abstract") or ""
    ab = ab.replace("\n", " ")
    return ab[:limit] + ("…" if len(ab) > limit else "")


def prepare(refcheck_json: str, out: str) -> None:
    d = json.load(open(refcheck_json, encoding="utf-8"))
    refs = {int(k): v for k, v in d["references"].items() if int(k) >= 0}
    citations = []
    for c in d["citations"]:
        entry = {
            "id": c["id"], "marker": c["marker"], "section": c.get("section"),
            "sentence": c["sentence"], "refs": [],
        }
        for n in c.get("ref_numbers", []):
            w = refs.get(n, {})
            entry["refs"].append({
                "n": n,
                "title": w.get("title") or w.get("custom", {}).get("bib_raw", ""),
                "journal": w.get("container-title", ""),
                "year": (w.get("issued", {}).get("date-parts", [[None]])[0][0]),
                "has_abstract": bool(w.get("abstract")),
                "abstract": _short_abstract(w),
            })
        citations.append(entry)
    payload = {
        "instructions": (
            "For each citation, write a 1-2 sentence 'summary' per referenced work "
            "(references[str(n)].summary) and, per (citation,ref) pair "
            "(pairs['<cid>|<n>']), a one-sentence 'connection' and an "
            "'appropriateness' of Supports/Partial/Unclear/Mismatch. Judge only "
            "from the abstract; if no abstract, use Unclear."
        ),
        "citations": citations,
    }
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    n_pairs = sum(len(c["refs"]) for c in citations)
    n_noabs = sum(1 for c in citations for r in c["refs"] if not r["has_abstract"])
    print(f"Wrote {out}: {len(citations)} citations, {n_pairs} (citation,ref) pairs "
          f"to judge ({n_noabs} without an abstract).")


def apply(refcheck_json: str, judgments_json: str, outdir: str) -> None:
    from refcheck.model import Citation
    d = json.load(open(refcheck_json, encoding="utf-8"))
    judgments = json.load(open(judgments_json, encoding="utf-8"))
    references = {int(k): v for k, v in d["references"].items()}
    citations = [Citation(**{k: c.get(k) for k in
                 ("id", "marker", "sentence", "ref_numbers", "work_ids",
                  "paragraph_index", "section", "resolved", "note")})
                 for c in d["citations"]]

    os.makedirs(outdir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(refcheck_json))[0].replace("_refcheck", "")

    audit = tabulate.build_audit_rows(citations, references, judgments)
    library = tabulate.build_library_rows(references, citations, judgments)
    tabulate.write_csv(audit, tabulate.AUDIT_COLUMNS, os.path.join(outdir, f"{stem}_audit.csv"))
    tabulate.write_csv(library, tabulate.LIBRARY_COLUMNS,
                       os.path.join(outdir, f"{stem}_references_table.csv"))
    xlsx = os.path.join(outdir, f"{stem}_references.xlsx")
    tabulate.write_xlsx(audit, library, xlsx)

    # embed judgments into the artifact so a re-run is idempotent
    d["judgments"] = judgments
    with open(os.path.join(outdir, f"{stem}_refcheck.json"), "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=2, ensure_ascii=False)

    # appropriateness summary
    verdicts = {}
    for c in citations:
        for n in c.ref_numbers:
            a = judgments.get("pairs", {}).get(f"{c.id}|{n}", {}).get("appropriateness", "—")
            verdicts[a] = verdicts.get(a, 0) + 1
    print(f"Applied judgments -> {xlsx}")
    print("Appropriateness tallies:", dict(sorted(verdicts.items())))


def main() -> int:
    ap = argparse.ArgumentParser(description="Appropriateness appraisal for reference-check.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare"); p.add_argument("refcheck_json"); p.add_argument("-o", "--out", required=True)
    a = sub.add_parser("apply"); a.add_argument("refcheck_json"); a.add_argument("judgments_json")
    a.add_argument("-o", "--outdir", required=True)
    args = ap.parse_args()
    if args.cmd == "prepare":
        prepare(args.refcheck_json, args.out)
    else:
        apply(args.refcheck_json, args.judgments_json, args.outdir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
