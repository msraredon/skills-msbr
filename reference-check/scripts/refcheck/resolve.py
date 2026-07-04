"""Online verification + enrichment of works via Crossref and NCBI E-utilities.

For each work we:
  1. verify at least one identifier actually resolves (existence check),
  2. cross-fill the missing identifier (DOI <-> PMID),
  3. merge authoritative metadata and, where available, an abstract,
  4. attach human-clickable URLs a reviewer can open.

All services used are free and keyless. We pass a contact mailto (Crossref
"polite pool") and an optional NCBI_API_KEY env var to raise rate limits. A
simple on-disk JSON cache keyed by identifier avoids re-querying across runs.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
import urllib.request
from typing import Any, Optional

from .model import normalize_doi, normalize_pmid, parse_author

CONTACT = os.environ.get("REFCHECK_CONTACT", "michasam.raredon@yale.edu")
NCBI_KEY = os.environ.get("NCBI_API_KEY")
USER_AGENT = f"refcheck/0.1 (mailto:{CONTACT})"

CROSSREF = "https://api.crossref.org/works/"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"


class Resolver:
    def __init__(self, cache_path: Optional[str] = None, delay: float = 0.15):
        self.cache_path = cache_path
        self.delay = delay
        self._cache: dict[str, Any] = {}
        if cache_path and os.path.exists(cache_path):
            try:
                self._cache = json.load(open(cache_path))
            except Exception:
                self._cache = {}

    # ---- low-level HTTP -------------------------------------------------
    def _get(self, url: str) -> Optional[bytes]:
        key = "GET " + url
        if key in self._cache:
            return self._cache[key].encode("utf-8") if self._cache[key] else None
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=20) as r:
                body = r.read()
            self._cache[key] = body.decode("utf-8", "replace")
        except Exception:
            self._cache[key] = ""
            body = None
        time.sleep(self.delay)
        return body

    def _eutils(self, endpoint: str, params: dict) -> Optional[bytes]:
        params = dict(params)
        params["tool"] = "refcheck"
        params["email"] = CONTACT
        if NCBI_KEY:
            params["api_key"] = NCBI_KEY
        return self._get(EUTILS + endpoint + "?" + urllib.parse.urlencode(params))

    def save(self) -> None:
        if self.cache_path:
            json.dump(self._cache, open(self.cache_path, "w"))

    # ---- Crossref (DOI) -------------------------------------------------
    def crossref(self, doi: str) -> Optional[dict]:
        body = self._get(CROSSREF + urllib.parse.quote(doi) + f"?mailto={CONTACT}")
        if not body:
            return None
        try:
            return json.loads(body).get("message")
        except Exception:
            return None

    def crossref_biblio(self, query: str, rows: int = 3) -> list[dict]:
        url = CROSSREF[:-1] + "?" + urllib.parse.urlencode(
            {"query.bibliographic": query, "rows": rows, "mailto": CONTACT})
        body = self._get(url)
        if not body:
            return []
        try:
            return json.loads(body).get("message", {}).get("items", [])
        except Exception:
            return []

    def best_bibmatch(self, raw: str, year: Optional[str] = None):
        """Resolve a free-text reference string to a Crossref record.

        Returns (item, score) for the best candidate, or (None, 0.0). Guarded by
        title-token containment so we never silently accept a wrong paper.
        """
        raw_tokens = _tokens(raw)
        best, best_score = None, 0.0
        for item in self.crossref_biblio(raw):
            title = re.sub(r"<[^>]+>", "", (item.get("title") or [""])[0])
            t_tokens = _tokens(title)
            if not t_tokens:
                continue
            overlap = len(t_tokens & raw_tokens) / len(t_tokens)
            iyear = ""
            if item.get("issued", {}).get("date-parts"):
                iyear = str(item["issued"]["date-parts"][0][0])
            if year and iyear and year != iyear:
                overlap -= 0.25       # penalize year mismatch
            if overlap > best_score:
                best, best_score = item, overlap
        return best, round(best_score, 2)

    # ---- NCBI (PMID) ----------------------------------------------------
    def pubmed_summary(self, pmid: str) -> Optional[dict]:
        body = self._eutils("esummary.fcgi", {"db": "pubmed", "id": pmid, "retmode": "json"})
        if not body:
            return None
        try:
            res = json.loads(body).get("result", {})
            return res.get(pmid)
        except Exception:
            return None

    def pubmed_abstract(self, pmid: str) -> Optional[str]:
        """Clean abstract body from efetch XML (labels preserved, no header)."""
        body = self._eutils("efetch.fcgi", {"db": "pubmed", "id": pmid, "retmode": "xml"})
        if not body:
            return None
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(body)
        except ET.ParseError:
            return None
        parts = []
        for node in root.findall(".//Abstract/AbstractText"):
            label = node.get("Label")
            txt = "".join(node.itertext()).strip()
            if not txt:
                continue
            parts.append(f"{label}: {txt}" if label else txt)
        return "\n".join(parts).strip() or None

    def pmid_from_doi(self, doi: str) -> Optional[str]:
        body = self._eutils("esearch.fcgi", {"db": "pubmed", "term": f"{doi}[DOI]", "retmode": "json"})
        if not body:
            return None
        try:
            ids = json.loads(body)["esearchresult"].get("idlist", [])
            return ids[0] if ids else None
        except Exception:
            return None

    def doi_from_pmid(self, summary: dict) -> Optional[str]:
        for aid in summary.get("articleids", []):
            if aid.get("idtype") == "doi":
                return normalize_doi(aid.get("value"))
        return None

    # ---- orchestration --------------------------------------------------
    def resolve_work(self, work: dict) -> dict:
        """Return a *verification report* merged onto a copy of ``work``."""
        w = json.loads(json.dumps(work))  # deep copy
        custom = w.setdefault("custom", {})
        doi = normalize_doi(w.get("DOI"))
        pmid = normalize_pmid(custom.get("pmid"))
        report = {"doi_verified": False, "pmid_verified": False, "abstract": False,
                  "cross_filled": [], "match_score": None, "errors": []}

        cr = None
        # Bibliography-only entry: recover a DOI by bibliographic search first.
        if not doi and not pmid and custom.get("bib_raw"):
            item, score = self.best_bibmatch(custom["bib_raw"], year=_work_year(w))
            report["match_score"] = score
            if item and score >= 0.6:
                doi = normalize_doi(item.get("DOI"))
                w["DOI"] = doi
                cr = item
                report["cross_filled"].append("doi<-bibsearch")
            else:
                report["errors"].append("no confident bibliographic match")

        if cr is None:
            cr = self.crossref(doi) if doi else None
        if cr is not None:
            report["doi_verified"] = True
            self._merge_crossref(w, cr)

        if not pmid and doi:
            found = self.pmid_from_doi(doi)
            if found:
                pmid = found
                custom["pmid"] = pmid
                report["cross_filled"].append("pmid<-doi")

        summ = self.pubmed_summary(pmid) if pmid else None
        if summ and not summ.get("error"):
            report["pmid_verified"] = True
            if not doi:
                d2 = self.doi_from_pmid(summ)
                if d2:
                    w["DOI"] = doi = d2
                    report["cross_filled"].append("doi<-pmid")
            abstract = self.pubmed_abstract(pmid)
            if abstract:
                w["abstract"] = abstract
                report["abstract"] = True

        if not w.get("abstract") and cr and cr.get("abstract"):
            w["abstract"] = _strip_jats(cr["abstract"])
            report["abstract"] = True

        # Human-clickable, verified links.
        links = {}
        if doi and report["doi_verified"]:
            links["doi_url"] = "https://doi.org/" + doi
        if pmid and report["pmid_verified"]:
            links["pubmed_url"] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        pmcid = custom.get("pmcid")
        if pmcid:
            links["pmc_url"] = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"
        custom["links"] = links

        verified = report["doi_verified"] or report["pmid_verified"]
        custom["verification"] = {
            "status": "verified" if verified else "unresolved",
            **report,
        }
        # id may change if we cross-filled a DOI; keep original id stable for linking
        return w

    def _merge_crossref(self, w: dict, cr: dict) -> None:
        """Prefer Crossref's authoritative values where our record is thin."""
        def take(csl_key, cr_key=None, transform=None):
            cr_key = cr_key or csl_key
            val = cr.get(cr_key)
            if transform and val is not None:
                val = transform(val)
            if val and not w.get(csl_key):
                w[csl_key] = val

        if cr.get("title"):
            title = cr["title"][0] if isinstance(cr["title"], list) else cr["title"]
            w.setdefault("title", re.sub(r"<[^>]+>", "", title).strip())
        if cr.get("container-title"):
            ct = cr["container-title"]
            w.setdefault("container-title", ct[0] if isinstance(ct, list) else ct)
        take("volume"); take("issue"); take("page")
        if cr.get("author") and not w.get("author"):
            w["author"] = [
                {"family": a.get("family", ""), "given": a.get("given", "")}
                if a.get("family") else {"literal": a.get("name", "")}
                for a in cr["author"]
            ]
        if not w.get("issued") and cr.get("issued", {}).get("date-parts"):
            w["issued"] = cr["issued"]
        w.setdefault("custom", {})["crossref_type"] = cr.get("type")


def _strip_jats(s: str) -> str:
    import re
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


_STOP = {"the", "a", "an", "of", "and", "in", "on", "for", "to", "with", "by",
         "at", "from", "as", "is", "are", "using", "via", "et", "al"}


def _tokens(s: str) -> set:
    import re
    words = re.findall(r"[a-z0-9]+", (s or "").lower())
    return {w for w in words if len(w) > 2 and w not in _STOP}


def _work_year(w: dict):
    import re
    dp = w.get("issued", {}).get("date-parts")
    if dp and dp[0]:
        return str(dp[0][0])
    raw = w.get("custom", {}).get("bib_raw", "")
    m = re.findall(r"\((\d{4})[a-z]?\)", raw) or re.findall(r"\b(19|20)\d{2}\b", raw)
    if m:
        y = m[-1]
        return y if len(y) == 4 else None
    return None
