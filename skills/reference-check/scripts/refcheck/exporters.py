"""Export canonical works to reference-manager formats.

One canonical work list -> many files, no lossy round-trips:
  * CSL-JSON  (.json)  – canonical master; imports into Zotero, pandoc, etc.
  * BibTeX    (.bib)   – LaTeX, and every manager
  * RIS       (.ris)   – EndNote, Zotero, Mendeley (universal tagged format)
  * EndNote   (.enw)   – EndNote's own tagged import format
  * Zotero    (.rdf)   – Zotero legacy native import

RIS and CSL-JSON both import cleanly into Zotero and EndNote, so those two are
the safe defaults; .enw and .rdf are provided for maximum native fidelity.
"""
from __future__ import annotations

import json
import re
from typing import Any, Iterable
from xml.sax.saxutils import escape


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _year(work: dict) -> str:
    dp = work.get("issued", {}).get("date-parts")
    if dp and dp[0]:
        return str(dp[0][0])
    return ""


def _authors(work: dict) -> list[str]:
    out = []
    for a in work.get("author", []):
        if a.get("literal"):
            out.append(a["literal"])
        else:
            fam, giv = a.get("family", ""), a.get("given", "")
            out.append(f"{fam}, {giv}".strip().rstrip(","))
    return out


def _pages(work: dict) -> tuple[str, str]:
    page = work.get("page", "")
    if not page:
        return "", ""
    m = re.match(r"\s*(\S+?)\s*[-–]+\s*(\S+)\s*$", page)
    return (m.group(1), m.group(2)) if m else (page, "")


def _ascii(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", s or "")


def citekeys(works: Iterable[dict]) -> dict[str, str]:
    """Stable, unique BibTeX/citekeys mapped by work id."""
    keys: dict[str, str] = {}
    used: set[str] = set()
    for w in works:
        auth = _authors(w)
        fam = _ascii(auth[0].split(",")[0]) if auth else "Anon"
        yr = _year(w) or "n.d."
        first_word = ""
        for tok in re.findall(r"[A-Za-z]+", w.get("title", "")):
            if tok.lower() not in {"the", "a", "an", "of", "on", "in", "and"}:
                first_word = tok.capitalize()
                break
        base = f"{fam}{yr}{first_word}" or "ref"
        key, n = base, 1
        while key in used:
            n += 1
            key = f"{base}{chr(ord('a') + n - 2)}"
        used.add(key)
        keys[w["id"]] = key
    return keys


# --------------------------------------------------------------------------- #
# CSL-JSON
# --------------------------------------------------------------------------- #
def to_csl_json(works: list[dict]) -> str:
    return json.dumps(works, indent=2, ensure_ascii=False)


# --------------------------------------------------------------------------- #
# BibTeX
# --------------------------------------------------------------------------- #
_BIB_ESC = {"&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_"}


def _bib_val(s: str) -> str:
    return "".join(_BIB_ESC.get(c, c) for c in str(s))


def to_bibtex(works: list[dict], keys: dict[str, str] | None = None) -> str:
    keys = keys or citekeys(works)
    out = []
    for w in works:
        custom = w.get("custom", {})
        fields = []

        def add(k, v):
            if v:
                fields.append(f"  {k} = {{{_bib_val(v)}}}")

        add("author", " and ".join(_authors(w)))
        add("title", w.get("title"))
        add("journal", w.get("container-title"))
        add("year", _year(w))
        add("volume", w.get("volume"))
        add("number", w.get("issue"))
        add("pages", w.get("page"))
        add("doi", w.get("DOI"))
        if custom.get("pmid"):
            add("pmid", custom["pmid"])
        add("url", (custom.get("links", {}) or {}).get("doi_url") or w.get("URL"))
        add("abstract", w.get("abstract"))
        out.append("@article{" + keys[w["id"]] + ",\n" + ",\n".join(fields) + "\n}")
    return "\n\n".join(out) + "\n"


# --------------------------------------------------------------------------- #
# RIS
# --------------------------------------------------------------------------- #
def to_ris(works: list[dict]) -> str:
    lines: list[str] = []
    for w in works:
        custom = w.get("custom", {})
        sp, ep = _pages(w)
        lines.append("TY  - JOUR")
        for a in _authors(w):
            lines.append(f"AU  - {a}")
        if w.get("title"):
            lines.append(f"TI  - {w['title']}")
        if w.get("container-title"):
            lines.append(f"JO  - {w['container-title']}")
        if _year(w):
            lines.append(f"PY  - {_year(w)}")
        if w.get("volume"):
            lines.append(f"VL  - {w['volume']}")
        if w.get("issue"):
            lines.append(f"IS  - {w['issue']}")
        if sp:
            lines.append(f"SP  - {sp}")
        if ep:
            lines.append(f"EP  - {ep}")
        if w.get("DOI"):
            lines.append(f"DO  - {w['DOI']}")
        if custom.get("pmid"):
            lines.append(f"AN  - {custom['pmid']}")
        url = (custom.get("links", {}) or {}).get("doi_url") or w.get("URL")
        if url:
            lines.append(f"UR  - {url}")
        if w.get("abstract"):
            lines.append(f"AB  - {w['abstract']}")
        lines.append("ER  - ")
        lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# EndNote .enw
# --------------------------------------------------------------------------- #
def to_enw(works: list[dict]) -> str:
    lines: list[str] = []
    for w in works:
        custom = w.get("custom", {})
        lines.append("%0 Journal Article")
        for a in _authors(w):
            lines.append(f"%A {a}")
        if w.get("title"):
            lines.append(f"%T {w['title']}")
        if w.get("container-title"):
            lines.append(f"%J {w['container-title']}")
        if _year(w):
            lines.append(f"%D {_year(w)}")
        if w.get("volume"):
            lines.append(f"%V {w['volume']}")
        if w.get("issue"):
            lines.append(f"%N {w['issue']}")
        if w.get("page"):
            lines.append(f"%P {w['page']}")
        if w.get("DOI"):
            lines.append(f"%R {w['DOI']}")
        if custom.get("pmid"):
            lines.append(f"%M {custom['pmid']}")
        url = (custom.get("links", {}) or {}).get("doi_url") or w.get("URL")
        if url:
            lines.append(f"%U {url}")
        if w.get("abstract"):
            lines.append(f"%X {w['abstract']}")
        lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Zotero RDF (legacy native import)
# --------------------------------------------------------------------------- #
_RDF_HEAD = (
    '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"\n'
    ' xmlns:z="http://www.zotero.org/namespaces/export#"\n'
    ' xmlns:dc="http://purl.org/dc/elements/1.1/"\n'
    ' xmlns:bib="http://purl.org/net/biblio#"\n'
    ' xmlns:dcterms="http://purl.org/dc/terms/"\n'
    ' xmlns:prism="http://prismstandard.org/namespaces/1.2/basic/">\n'
)


def to_zotero_rdf(works: list[dict]) -> str:
    out = [_RDF_HEAD]
    for i, w in enumerate(works):
        custom = w.get("custom", {})
        about = (custom.get("links", {}) or {}).get("doi_url") or f"#item_{i}"
        out.append(f'  <bib:Article rdf:about="{escape(about)}">\n')
        out.append('    <z:itemType>journalArticle</z:itemType>\n')
        if w.get("container-title"):
            out.append('    <dcterms:isPartOf>\n      <bib:Journal>\n')
            out.append(f'        <dc:title>{escape(w["container-title"])}</dc:title>\n')
            out.append('      </bib:Journal>\n    </dcterms:isPartOf>\n')
        if w.get("author"):
            out.append('    <bib:authors>\n      <rdf:Seq>\n')
            for a in _authors(w):
                out.append('        <rdf:li>\n          <foaf:Person '
                           'xmlns:foaf="http://xmlns.com/foaf/0.1/">\n')
                fam = a.split(",")[0].strip()
                giv = a.split(",", 1)[1].strip() if "," in a else ""
                out.append(f'            <foaf:surname>{escape(fam)}</foaf:surname>\n')
                if giv:
                    out.append(f'            <foaf:givenName>{escape(giv)}</foaf:givenName>\n')
                out.append('          </foaf:Person>\n        </rdf:li>\n')
            out.append('      </rdf:Seq>\n    </bib:authors>\n')
        if w.get("title"):
            out.append(f'    <dc:title>{escape(w["title"])}</dc:title>\n')
        if _year(w):
            out.append(f'    <dc:date>{_year(w)}</dc:date>\n')
        if w.get("volume"):
            out.append(f'    <prism:volume>{escape(w["volume"])}</prism:volume>\n')
        if w.get("page"):
            out.append(f'    <bib:pages>{escape(w["page"])}</bib:pages>\n')
        if w.get("DOI"):
            out.append(f'    <dc:identifier>DOI {escape(w["DOI"])}</dc:identifier>\n')
        if custom.get("pmid"):
            out.append(f'    <dc:identifier>PMID {escape(custom["pmid"])}</dc:identifier>\n')
        if w.get("abstract"):
            out.append(f'    <dcterms:abstract>{escape(w["abstract"])}</dcterms:abstract>\n')
        out.append('  </bib:Article>\n')
    out.append("</rdf:RDF>\n")
    return "".join(out)


EXPORTERS = {
    "csl.json": to_csl_json,
    "bib": to_bibtex,
    "ris": to_ris,
    "enw": to_enw,
    "rdf": to_zotero_rdf,
}


def write_library(works: list[dict], out_stem: str) -> dict[str, str]:
    """Write all five formats; return {format: path}. ``out_stem`` has no ext."""
    keys = citekeys(works)
    paths = {}
    for ext, fn in EXPORTERS.items():
        path = f"{out_stem}.{ext}"
        content = fn(works, keys) if ext == "bib" else fn(works)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        paths[ext] = path
    return paths
