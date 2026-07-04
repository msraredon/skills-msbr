"""Canonical data model.

A *work* is one cited reference, held as a CSL-JSON-compatible dict so it can be
exported to BibTeX / RIS / EndNote / Zotero without lossy re-parsing. Fields that
CSL does not define natively (PMID, PMCID, provenance, verification status) live
under the ``custom`` key, which CSL processors ignore but our exporters read.

A *citation* is one in-text occurrence: a marker (e.g. superscript "16"), the
sentence it sits in, and the id(s) of the work(s) it points to. One work may be
cited by many citations; the auditing table is per-citation, the library is
per-work.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Optional


def _clean(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s = re.sub(r"\s+", " ", s).strip()
    return s or None


def normalize_doi(doi: Optional[str]) -> Optional[str]:
    """Return a bare lower-case DOI (no scheme/host, no trailing punctuation)."""
    doi = _clean(doi)
    if not doi:
        return None
    doi = re.sub(r"^\s*(?:https?://)?(?:dx\.)?doi\.org/", "", doi, flags=re.I)
    doi = re.sub(r"^\s*doi:\s*", "", doi, flags=re.I)
    doi = doi.strip().rstrip(".,;)")
    m = re.search(r"10\.\d{4,9}/\S+", doi)
    return m.group(0).lower() if m else None


def normalize_pmid(pmid: Optional[str]) -> Optional[str]:
    """Return a bare numeric PMID, or None if the value isn't a plausible PMID."""
    pmid = _clean(pmid)
    if not pmid:
        return None
    m = re.search(r"\b(\d{1,9})\b", pmid)
    return m.group(1) if m else None


def make_work(
    *,
    csl_type: str = "article-journal",
    title: Optional[str] = None,
    authors: Optional[list[dict]] = None,
    year: Optional[str] = None,
    container_title: Optional[str] = None,
    volume: Optional[str] = None,
    issue: Optional[str] = None,
    page: Optional[str] = None,
    doi: Optional[str] = None,
    pmid: Optional[str] = None,
    pmcid: Optional[str] = None,
    url: Optional[str] = None,
    abstract: Optional[str] = None,
    source: str = "unknown",
) -> dict[str, Any]:
    """Build a canonical CSL-JSON work dict with a stable id."""
    work: dict[str, Any] = {"type": csl_type}
    if title:
        work["title"] = _clean(title)
    if authors:
        work["author"] = authors
    if container_title:
        work["container-title"] = _clean(container_title)
    if volume:
        work["volume"] = _clean(volume)
    if issue:
        work["issue"] = _clean(issue)
    if page:
        work["page"] = _clean(page)
    year = _clean(year)
    if year and re.match(r"\d{4}", year):
        work["issued"] = {"date-parts": [[int(year[:4])]]}
    doi = normalize_doi(doi)
    if doi:
        work["DOI"] = doi
    if url:
        work["URL"] = _clean(url)
    if abstract:
        work["abstract"] = _clean(abstract)

    custom: dict[str, Any] = {"source": source}
    pmid = normalize_pmid(pmid)
    if pmid:
        custom["pmid"] = pmid
    if pmcid:
        custom["pmcid"] = _clean(pmcid)
    work["custom"] = custom

    work["id"] = work_key(work)
    return work


def work_key(work: dict[str, Any]) -> str:
    """Deterministic id: prefer DOI, then PMID, else a hash of title+year.

    Used for de-duplication (per-work library) and to link citations to works.
    """
    if work.get("DOI"):
        return "doi:" + work["DOI"]
    pmid = work.get("custom", {}).get("pmid")
    if pmid:
        return "pmid:" + pmid
    basis = (work.get("title") or "").lower()
    year = ""
    if work.get("issued", {}).get("date-parts"):
        year = str(work["issued"]["date-parts"][0][0])
    h = hashlib.sha1(f"{basis}|{year}".encode("utf-8")).hexdigest()[:12]
    return "key:" + h


def parse_author(raw: str) -> dict[str, str]:
    """Parse an EndNote-style 'Family, Given I.' author string into CSL parts."""
    raw = _clean(raw) or ""
    if "," in raw:
        family, given = raw.split(",", 1)
        return {"family": _clean(family) or "", "given": _clean(given) or ""}
    # Fallback: treat the last whitespace token as the family name.
    parts = raw.split()
    if len(parts) >= 2:
        return {"family": parts[-1], "given": " ".join(parts[:-1])}
    return {"literal": raw}


@dataclass
class Citation:
    """One in-text citation occurrence: a marker + sentence linked to references.

    ``ref_numbers`` are the bibliography reference numbers this marker points at
    (e.g. marker "8-10" -> [8, 9, 10]); they key into the reference registry.
    ``work_ids`` mirror those as canonical work ids for convenience.
    """

    id: str
    marker: str                 # rendered in-text text, e.g. "16" or "8-10"
    sentence: str               # the sentence the marker sits in
    ref_numbers: list[int] = field(default_factory=list)
    work_ids: list[str] = field(default_factory=list)
    paragraph_index: int = -1
    section: Optional[str] = None
    resolved: bool = False      # True if every referenced work carries usable data
    note: Optional[str] = None  # e.g. "reference not found in bibliography"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "marker": self.marker,
            "sentence": self.sentence,
            "ref_numbers": self.ref_numbers,
            "work_ids": self.work_ids,
            "paragraph_index": self.paragraph_index,
            "section": self.section,
            "resolved": self.resolved,
            "note": self.note,
        }
