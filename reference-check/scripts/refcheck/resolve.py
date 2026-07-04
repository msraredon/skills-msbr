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

from .bibliography import extract_title
from .model import normalize_doi, normalize_pmid, parse_author

CONTACT = os.environ.get("REFCHECK_CONTACT", "michasam.raredon@yale.edu")
NCBI_KEY = os.environ.get("NCBI_API_KEY")
USER_AGENT = f"refcheck/0.1 (mailto:{CONTACT})"

CROSSREF = "https://api.crossref.org/works/"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
UNPAYWALL = "https://api.unpaywall.org/v2/"


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
        if self._cache.get(key):          # only cache successful, non-empty bodies
            return self._cache[key].encode("utf-8")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=20) as r:
                body = r.read()
            self._cache[key] = body.decode("utf-8", "replace")
        except Exception:
            body = None                   # do NOT cache failures; allow retry
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

    def best_bibmatch(self, raw: str, year: Optional[str] = None,
                      query: Optional[str] = None):
        """Resolve a free-text reference string to a Crossref record.

        Returns (item, score, accept) for the best candidate. Scores three
        independent signals — title-token containment, author-surname
        containment, and year match — so a record with a garbled Crossref title
        (e.g. small-caps markup) still verifies when the authors and year agree.
        A candidate is accepted only when at least two signals corroborate, so a
        wrong paper is never silently accepted.
        """
        raw_tokens = _tokens(raw)
        best, best_rank, best_sig = None, -1.0, (0.0, 0.0, 0.0, False)
        for item in self.crossref_biblio(query or raw):
            t, a, y, yknown = _match_signals(item, raw, raw_tokens, year)
            rank = _rank(t, a, y, yknown)
            if rank > best_rank:
                best, best_rank, best_sig = item, rank, (t, a, y, yknown)
        if best is None:
            return None, 0.0, False
        return best, round(best_rank, 2), _accept(*best_sig)

    def pubmed_bibmatch(self, raw: str, year: Optional[str] = None,
                        query: Optional[str] = None):
        """Fallback: resolve a free-text reference against PubMed by search.

        Better than Crossref for older biomedical papers that predate DOIs.
        Returns (pmid, score, accept).
        """
        body = self._eutils("esearch.fcgi",
                            {"db": "pubmed", "term": query or raw, "retmax": 5, "retmode": "json"})
        if not body:
            return None, 0.0, False
        try:
            ids = json.loads(body)["esearchresult"].get("idlist", [])
        except Exception:
            ids = []
        raw_tokens = _tokens(raw)
        best_pmid, best_rank, best_sig = None, -1.0, (0.0, 0.0, 0.0, False)
        for pmid in ids:
            summ = self.pubmed_summary(pmid)
            if not summ or summ.get("error"):
                continue
            t, a, y, yknown = _match_signals(_summary_to_itemish(summ), raw, raw_tokens, year)
            rank = _rank(t, a, y, yknown)
            if rank > best_rank:
                best_pmid, best_rank, best_sig = pmid, rank, (t, a, y, yknown)
        if best_pmid is None:
            return None, 0.0, False
        return best_pmid, round(best_rank, 2), _accept(*best_sig)

    # ---- Open access (Unpaywall + PubMed Central) -----------------------
    def unpaywall(self, doi: str) -> Optional[dict]:
        body = self._get(UNPAYWALL + urllib.parse.quote(doi) + f"?email={CONTACT}")
        if not body:
            return None
        try:
            d = json.loads(body)
        except Exception:
            return None
        loc = d.get("best_oa_location") or {}
        return {
            "is_oa": bool(d.get("is_oa")),
            "oa_url": loc.get("url_for_landing_page") or loc.get("url"),
            "pdf_url": loc.get("url_for_pdf"),
        }

    def pmcid_from_summary(self, summary: dict) -> Optional[str]:
        for aid in summary.get("articleids", []):
            if aid.get("idtype") in ("pmc", "pmcid") and aid.get("value"):
                m = re.search(r"PMC\d+", aid["value"])
                return m.group(0) if m else aid["value"]
        return None

    def pmc_fulltext(self, pmcid: str, limit: int = 12000) -> Optional[str]:
        """Open-access full-text body from PMC (open-access subset only)."""
        pmc_num = pmcid.replace("PMC", "")
        body = self._eutils("efetch.fcgi", {"db": "pmc", "id": pmc_num, "retmode": "xml"})
        if not body:
            return None
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(body)
        except ET.ParseError:
            return None
        body_el = root.find(".//body")
        if body_el is None:
            return None
        # gather paragraph text, dropping tables/figures markup
        chunks = []
        for p in body_el.iter("p"):
            txt = " ".join("".join(p.itertext()).split())
            if txt:
                chunks.append(txt)
        text = "\n".join(chunks).strip()
        return text[:limit] if text else None

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
                  "oa": False, "full_text": False,
                  "cross_filled": [], "match_score": None, "errors": []}

        cr = None
        # Bibliography-only entry: recover an identifier by search first —
        # Crossref (by DOI), then PubMed as a fallback for older biomedical work.
        if not doi and not pmid and custom.get("bib_raw"):
            raw, ryear = custom["bib_raw"], _work_year(w)
            title_q = extract_title(raw)
            best_score = 0.0
            # Try several searches; take the first that passes precision-gated
            # acceptance. PubMed first (biomedical corpus: yields PMID + abstract
            # + canonical DOI and avoids conference-abstract duplicates), then
            # Crossref; query by clean title first, then the full raw string.
            for source, q in (("pm", title_q), ("cr", title_q), ("pm", raw), ("cr", raw)):
                if source == "cr":
                    item, sc, ok = self.best_bibmatch(raw, year=ryear, query=q)
                    best_score = max(best_score, sc)
                    if ok and item and normalize_doi(item.get("DOI")):
                        doi = normalize_doi(item["DOI"]); w["DOI"] = doi; cr = item
                        report["cross_filled"].append("doi<-crossref"); break
                else:
                    pm, sc, ok = self.pubmed_bibmatch(raw, year=ryear, query=q)
                    best_score = max(best_score, sc)
                    if ok and pm:
                        pmid = pm; custom["pmid"] = pmid
                        report["cross_filled"].append("pmid<-pubmed"); break
            report["match_score"] = round(best_score, 2)
            if not doi and not pmid:
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
            pmcid = self.pmcid_from_summary(summ)
            if pmcid:
                custom["pmcid"] = pmcid

        if not w.get("abstract") and cr and cr.get("abstract"):
            w["abstract"] = _strip_jats(cr["abstract"])
            report["abstract"] = True

        # Open-access discovery + full text (for the appropriateness check).
        oa = self.unpaywall(doi) if doi else None
        if oa and oa.get("is_oa"):
            report["oa"] = True
            custom["oa"] = {"is_oa": True, "url": oa.get("oa_url"), "pdf_url": oa.get("pdf_url")}
        pmcid = custom.get("pmcid")
        if pmcid:
            full = self.pmc_fulltext(pmcid)
            if full:
                w["full_text"] = full
                report["full_text"] = True

        # Human-clickable, verified links.
        links = {}
        if doi and report["doi_verified"]:
            links["doi_url"] = "https://doi.org/" + doi
        if pmid and report["pmid_verified"]:
            links["pubmed_url"] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        if pmcid:
            links["pmc_url"] = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"
        if custom.get("oa", {}).get("url"):
            links["oa_url"] = custom["oa"]["url"]
        custom["links"] = links

        verified = report["doi_verified"] or report["pmid_verified"]
        custom["verification"] = {
            "status": "verified" if verified else "unresolved",
            **report,
        }
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
    words = re.findall(r"[a-z0-9]+", (s or "").lower())
    return {w for w in words if len(w) > 2 and w not in _STOP}


def _author_families(item: dict) -> list[str]:
    fams = []
    for a in item.get("author", []):
        fam = a.get("family") or a.get("name") or ""
        fam = re.sub(r"[^A-Za-z]", "", fam).lower()
        if len(fam) > 2:
            fams.append(fam)
    return fams


def _match_signals(item: dict, raw: str, raw_tokens: set, year: Optional[str]):
    """Return (title_score, author_score, year_score, year_known) in [0,1]."""
    title = re.sub(r"<[^>]+>", "", (item.get("title") or [""])[0])
    t_tokens = _tokens(title)
    t = (len(t_tokens & raw_tokens) / len(t_tokens)) if t_tokens else 0.0
    fams = _author_families(item)[:4]
    a = (sum(1 for f in fams if f in raw_tokens) / len(fams)) if fams else 0.0
    iyear = ""
    if item.get("issued", {}).get("date-parts") and item["issued"]["date-parts"][0]:
        iyear = str(item["issued"]["date-parts"][0][0])
    yknown = bool(year and iyear)
    y = 0.0
    if yknown:
        try:
            y = 1.0 if abs(int(year) - int(iyear)) <= 1 else 0.0  # tolerate epub/print
        except ValueError:
            y = 0.0
    return t, a, y, yknown


def _rank(t: float, a: float, y: float, yknown: bool) -> float:
    return 0.45 * t + 0.25 * a + 0.30 * (y if yknown else 0.5)


def _accept(t: float, a: float, y: float, yknown: bool) -> bool:
    """Precision-first acceptance: never accept a wrong-year match.

    When the year is comparable it must agree (within tolerance) AND one of
    title/author must corroborate. When the year cannot be compared, require
    strong title evidence. This favors flagging over accepting a wrong paper.
    """
    if yknown:
        return y == 1.0 and (t >= 0.45 or a >= 0.5)
    return t >= 0.7 or (t >= 0.5 and a >= 0.6)


def _summary_to_itemish(summ: dict) -> dict:
    """Shape a PubMed esummary like a Crossref item for scoring."""
    authors = [{"family": (a.get("name", "").split()[0] if a.get("name") else "")}
               for a in summ.get("authors", [])]
    year = ""
    m = re.search(r"\b(19|20)\d{2}\b", summ.get("pubdate", ""))
    if m:
        year = m.group(0)
    return {
        "title": [summ.get("title", "")],
        "author": authors,
        "issued": {"date-parts": [[int(year)]]} if year else {},
    }


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
