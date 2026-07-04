"""Parse a rendered reference list and map in-text markers to reference numbers.

Many documents (this is the common case for EndNote/Word) carry a fully rendered,
numbered bibliography even when the in-text citation fields have no embedded
metadata. EndNote renders it inside an ``EN.REFLIST`` field as paragraphs styled
``EndNoteBibliography``:

    105.<tab>J. A. Goldman, K. D. Poss, Gene regulatory programmes of tissue
             regeneration. Nature Reviews Genetics 21, 511-525 (2020).

The reference *number* is the linkage key: an in-text marker like ``8-10`` refers
to reference numbers 8, 9 and 10. We parse the numbered list, then expand each
citation marker to the reference numbers it points at. Metadata for each entry is
recovered by online bibliographic search (see resolve.resolve_bibentry), since
these rendered entries usually carry no DOI.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# Paragraph styles that mark a rendered bibliography entry (extend as needed).
_BIB_STYLES = ("EndNoteBibliography", "Bibliography")


def _para_text(p_xml: str) -> str:
    """Visible text of one <w:p>, tabs as spaces, tags stripped."""
    parts = []
    for m in re.finditer(r"<w:t[^>]*>(.*?)</w:t>|<w:tab\b[^>]*/?>", p_xml, re.S):
        parts.append(m.group(1) if m.group(1) is not None else "\t")
    s = "".join(parts)
    for a, b in (("&lt;", "<"), ("&gt;", ">"), ("&amp;", "&"),
                 ("&quot;", '"'), ("&apos;", "'")):
        s = s.replace(a, b)
    s = re.sub(r"<[^>]+>", "", s)          # strip any residual tags
    return re.sub(r"\s+", " ", s).strip()


@dataclass
class BibEntry:
    number: int
    raw: str
    year: Optional[str] = None
    doi: Optional[str] = None


_DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"'<>,]+", re.I)


def parse_bibliography(document_xml: str) -> dict[int, BibEntry]:
    """Return {reference_number: BibEntry} from the rendered bibliography."""
    entries: dict[int, BibEntry] = {}
    for p in re.findall(r"<w:p\b.*?</w:p>", document_xml, re.S):
        if not any(f'w:val="{s}"' in p for s in _BIB_STYLES):
            continue
        text = _para_text(p)
        m = re.match(r"^(\d+)\.\s*(.+)$", text, re.S)
        if not m:
            continue
        num = int(m.group(1))
        raw = m.group(2).strip()
        year = None
        ym = re.findall(r"\((\d{4})[a-z]?\)", raw) or re.findall(r"\b(19|20)\d{2}\b", raw)
        if ym:
            y = ym[-1]
            year = y if len(y) == 4 else None
        doi = _DOI_RE.search(raw)
        entries[num] = BibEntry(number=num, raw=raw, year=year,
                                doi=doi.group(0).rstrip(".") if doi else None)
    return entries


def expand_marker(marker: str) -> list[int]:
    """Expand a rendered citation marker to reference numbers.

    Handles numeric lists and ranges: '1,2' -> [1,2]; '8-10' -> [8,9,10];
    '16' -> [16]; '103-105, 20' -> [103,104,105,20]. Non-numeric markers
    (author-year styles) return [] — those are linked by other means.
    """
    nums: list[int] = []
    cleaned = marker.replace("–", "-").replace("‒", "-").replace("−", "-")
    # keep only digits, commas, hyphens (drop superscript brackets, spaces)
    cleaned = re.sub(r"[^\d,\-]", " ", cleaned)
    for part in re.split(r"[,\s]+", cleaned):
        part = part.strip()
        if not part:
            continue
        rng = re.match(r"^(\d+)-(\d+)$", part)
        if rng:
            a, b = int(rng.group(1)), int(rng.group(2))
            if 0 < b - a < 500:
                nums.extend(range(a, b + 1))
        elif part.isdigit():
            nums.append(int(part))
    # de-dup, preserve order
    seen, out = set(), []
    for n in nums:
        if n not in seen:
            seen.add(n); out.append(n)
    return out
