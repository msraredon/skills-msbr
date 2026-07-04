"""Ingest a Word (.docx) document into citations + a numbered reference registry.

Word stores citations as (often nested) fields; an EndNote citation's code text
(``w:instrText``) is ``ADDIN EN.CITE ...`` and its *result* is the rendered
marker the reader sees (e.g. superscript ``16`` or ``8-10``). We respect
begin/separate/end nesting, replace each top-level citation with a placeholder
in a linear text stream, then segment into sentences so every citation attaches
to its sentence.

Reference metadata comes from two sources, unified by **reference number**:
  1. records embedded in some citation fields (authoritative DOI/PMID), and
  2. the rendered numbered bibliography (``EN.REFLIST`` / EndNoteBibliography),
     which is usually the only complete source.
An in-text marker (``8-10``) expands to reference numbers (8, 9, 10); those key
into the registry. Where a field embeds records, they are paired positionally to
the marker's numbers to seed authoritative identifiers.
"""
from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field as dc_field
from typing import Any, Iterator, Optional

from .bibliography import parse_bibliography, expand_marker, BibEntry
from .endnote import records_from_fieldcode
from .model import Citation, make_work
from .sentences import split_sentences

_CITE_OPEN = ""
_CITE_CLOSE = ""
_PLACEHOLDER_RE = re.compile(_CITE_OPEN + r"(\d+)" + _CITE_CLOSE)


def _placeholder(idx: int) -> str:
    return f"{_CITE_OPEN}{idx}{_CITE_CLOSE}"


def _unescape(s: str) -> str:
    for a, b in (
        ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'),
        ("&apos;", "'"), ("&#xD;", "\n"), ("&#xA;", "\n"), ("&amp;", "&"),
    ):
        s = s.replace(a, b)
    return s


@dataclass
class _Frame:
    code: str = ""
    phase: str = "code"
    result: list[str] = dc_field(default_factory=list)
    child_records: list[dict] = dc_field(default_factory=list)


_TOKEN_RE = re.compile(
    r'(?P<pbreak></w:p>)'
    r'|<w:fldChar[^>]*w:fldCharType="(?P<fld>begin|separate|end)"[^>]*/?>'
    r'|<w:instrText[^>]*>(?P<instr>.*?)</w:instrText>'
    r'|<w:t[^>]*>(?P<text>.*?)</w:t>'
    r'|<w:tab\b[^>]*/?>(?P<tab>)'
    r'|(?P<style><w:pStyle[^>]*w:val="[^"]*"[^>]*/?>)',
    re.S,
)


def _iter_tokens(xml: str) -> Iterator[tuple[str, str]]:
    for m in _TOKEN_RE.finditer(xml):
        if m.group("pbreak") is not None:
            yield ("PBREAK", "")
        elif m.group("fld") is not None:
            yield ("FLD", m.group("fld"))
        elif m.group("instr") is not None:
            yield ("INSTR", _unescape(m.group("instr")))
        elif m.group("text") is not None:
            yield ("TEXT", _unescape(m.group("text")))
        elif m.group("tab") is not None:
            yield ("TEXT", "\t")
        elif m.group("style") is not None:
            sm = re.search(r'w:val="([^"]*)"', m.group("style"))
            yield ("STYLE", sm.group(1) if sm else "")


def _is_citation_field(code: str) -> bool:
    return "EN.CITE" in code and "EN.REFLIST" not in code


def _is_reflist_field(code: str) -> bool:
    return "EN.REFLIST" in code


@dataclass
class DocxIngest:
    text: str
    citations: list[Citation]
    references: dict[int, dict[str, Any]]   # reference number -> canonical work
    bibliography: dict[int, BibEntry]

    def to_dict(self) -> dict[str, Any]:
        cited = {n for c in self.citations for n in c.ref_numbers}
        return {
            "source_type": "docx",
            "citations": [c.to_dict() for c in self.citations],
            "references": {str(n): w for n, w in sorted(self.references.items())},
            "stats": {
                "n_citations": len(self.citations),
                "n_references": len(self.references),
                "n_refs_cited": len(cited),
                "n_unresolved_citations":
                    sum(1 for c in self.citations if not c.resolved),
            },
        }


def _work_from_bibentry(num: int, be: BibEntry) -> dict[str, Any]:
    w = make_work(year=be.year, doi=be.doi, source="bibliography")
    w["id"] = f"ref:{num}"
    w["custom"]["ref_number"] = num
    w["custom"]["bib_raw"] = be.raw
    return w


def _attach_embedded(work_registry: dict[int, dict], num: int, rec: dict) -> None:
    """Seed reference ``num`` with an authoritative embedded record."""
    rec = dict(rec)
    rec["id"] = f"ref:{num}"
    rec.setdefault("custom", {})
    # preserve the bibliography raw string if we had one
    prev = work_registry.get(num, {})
    if prev.get("custom", {}).get("bib_raw"):
        rec["custom"]["bib_raw"] = prev["custom"]["bib_raw"]
    rec["custom"]["ref_number"] = num
    rec["custom"]["source"] = "endnote-embedded"
    work_registry[num] = rec


def parse_document_xml(xml: str) -> DocxIngest:
    stack: list[_Frame] = []
    stream: list[str] = []
    para_styles: list[str] = []
    cur_style: Optional[str] = None
    raw_fields: list[dict] = []

    def out(s: str) -> None:
        (stack[-1].result if stack else stream).append(s)

    for kind, val in _iter_tokens(xml):
        if kind == "STYLE":
            cur_style = val
        elif kind == "PBREAK":
            out("\n")
            if not stack:
                para_styles.append(cur_style or "")
            cur_style = None
        elif kind == "FLD":
            if val == "begin":
                stack.append(_Frame())
            elif val == "separate":
                if stack:
                    stack[-1].phase = "result"
            elif val == "end":
                if not stack:
                    continue
                f = stack.pop()
                records = records_from_fieldcode(f.code) + f.child_records
                result_text = "".join(f.result)
                if stack:
                    stack[-1].child_records.extend(records)
                    stack[-1].result.append(result_text)
                elif _is_citation_field(f.code):
                    idx = len(raw_fields)
                    raw_fields.append({"marker": result_text.strip(), "records": records})
                    stream.append(_placeholder(idx))
                elif _is_reflist_field(f.code):
                    pass  # bibliography parsed separately from the raw xml
                else:
                    stream.append(result_text)
        elif kind == "INSTR":
            if stack and stack[-1].phase == "code":
                stack[-1].code += val
        elif kind == "TEXT":
            out(val)

    text = "".join(stream)
    bib = parse_bibliography(xml)
    citations, references = _link(text, raw_fields, para_styles, bib)
    return DocxIngest(text=text, citations=citations, references=references, bibliography=bib)


def _paragraph_of(offset: int, para_offsets: list[int]) -> int:
    idx = 0
    for i, start in enumerate(para_offsets):
        if offset >= start:
            idx = i
        else:
            break
    return idx


def _link(text, raw_fields, para_styles, bib):
    para_offsets = [0] + [m.end() for m in re.finditer("\n", text)]

    # 1) reference registry seeded from the rendered bibliography
    references: dict[int, dict] = {n: _work_from_bibentry(n, be) for n, be in bib.items()}

    # 2) overlay authoritative embedded records, paired to marker numbers
    for rf in raw_fields:
        nums = expand_marker(rf["marker"])
        recs = rf["records"]
        for i, rec in enumerate(recs):
            if i < len(nums):
                _attach_embedded(references, nums[i], rec)
            else:
                # extra record without a numbered slot: index by a synthetic key
                references.setdefault(-(len(references) + 1), rec)

    # 3) build citations, attach to sentences
    citations: list[Citation] = []
    sentences = split_sentences(text, placeholder_re=_PLACEHOLDER_RE)
    order = 0
    for sent in sentences:
        for m in _PLACEHOLDER_RE.finditer(sent.raw):
            idx = int(m.group(1))
            rf = raw_fields[idx]
            nums = expand_marker(rf["marker"])
            para_idx = _paragraph_of(sent.start, para_offsets)
            section = para_styles[para_idx] if 0 <= para_idx < len(para_styles) else None
            missing = [n for n in nums if n not in references]
            note = None
            if not nums:
                note = "non-numeric marker; link via reference library"
            elif missing:
                note = f"reference number(s) not in bibliography: {missing}"
            order += 1
            citations.append(Citation(
                id=f"C{order}",
                marker=rf["marker"],
                sentence=sent.clean,
                ref_numbers=nums,
                work_ids=[references[n]["id"] for n in nums if n in references],
                paragraph_index=para_idx,
                section=section,
                resolved=bool(nums) and not missing,
                note=note,
            ))
    return citations, references


def ingest_docx(path: str) -> DocxIngest:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    return parse_document_xml(xml)
