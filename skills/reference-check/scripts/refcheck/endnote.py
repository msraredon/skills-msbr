"""Parse EndNote 'Traveling Library' record XML into canonical works.

EndNote embeds one ``<record>`` per cited work inside the Word field code
(``ADDIN EN.CITE`` / ``EN.CITE.DATA``). When present this is authoritative
metadata we can trust with high confidence, including the DOI
(``<electronic-resource-num>``) and usually the PMID (``<accession-num>`` and/or
a PubMed URL). We still verify identifiers online later, but this avoids any
lossy re-parsing of formatted citation text.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any

from .model import make_work, normalize_pmid, parse_author


def _text(node, path: str):
    el = node.find(path)
    if el is not None and el.text:
        return el.text
    return None


def _pmid_from_record(rec) -> str | None:
    """PMID from an EndNote record: prefer a PubMed URL, else accession-num.

    ``<accession-num>`` is *usually* the PMID for PubMed-sourced references, but
    not always, so we only trust a bare-digit accession as a *candidate* to be
    verified online. A pubmed.gov URL is unambiguous.
    """
    for url_el in rec.findall(".//related-urls/url"):
        if url_el.text:
            m = re.search(r"pubmed(?:\.ncbi\.nlm\.nih\.gov)?/(\d+)", url_el.text)
            if m:
                return m.group(1)
    return normalize_pmid(_text(rec, "accession-num"))


def record_to_work(rec) -> dict[str, Any]:
    """Convert one EndNote ``<record>`` element to a canonical work dict."""
    authors = [
        parse_author(a.text)
        for a in rec.findall(".//contributors/authors/author")
        if a.text
    ]
    title = _text(rec, "titles/title")
    journal = (
        _text(rec, "periodical/full-title")
        or _text(rec, "titles/secondary-title")
    )
    year = _text(rec, "dates/year") or _text(rec, "Year")
    url_el = rec.find(".//related-urls/url")
    return make_work(
        title=title,
        authors=authors or None,
        year=year,
        container_title=journal,
        volume=_text(rec, "volume"),
        issue=_text(rec, "number"),
        page=_text(rec, "pages"),
        doi=_text(rec, "electronic-resource-num"),
        pmid=_pmid_from_record(rec),
        url=url_el.text if url_el is not None else None,
        source="endnote-embedded",
    )


def records_from_fieldcode(code: str) -> list[dict[str, Any]]:
    """Extract every work from one Word field code's text.

    ``code`` is the concatenated ``w:instrText`` of an EndNote citation field
    (already XML-unescaped). It may contain one ``<EndNote>`` block with one or
    more ``<Cite><record>`` entries (grouped citations).
    """
    works: list[dict[str, Any]] = []
    for block in re.findall(r"<EndNote>.*?</EndNote>", code, re.S):
        try:
            root = ET.fromstring(block)
        except ET.ParseError:
            continue
        for rec in root.findall(".//record"):
            works.append(record_to_work(rec))
    return works
