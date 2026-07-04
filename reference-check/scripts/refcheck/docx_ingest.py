"""Ingest a Word (.docx) document into citations + works.

Word stores citations as *fields*. An EndNote citation is a (possibly nested)
field whose code text (``w:instrText``) is ``ADDIN EN.CITE ...`` and whose
*result* (the run text after ``fldChar separate``) is the rendered marker the
reader sees, e.g. a superscript ``16``. Fields nest: ``EN.CITE`` wraps an inner
``EN.CITE.DATA`` field that actually carries the record XML, so we must respect
begin/separate/end nesting rather than concatenate all instrText globally.

The parser produces a linear text stream in which each top-level citation field
is replaced by a placeholder token. We then segment that stream into sentences
so every citation can be attached to the sentence it sits in — the unit the
appropriateness check operates on.
"""
from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field as dc_field
from typing import Any, Iterator, Optional

from .endnote import records_from_fieldcode
from .model import Citation, work_key
from .sentences import split_sentences

# Sentinel wrapping a citation index, unlikely to occur in real text.
_CITE_OPEN = ""
_CITE_CLOSE = ""


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
    phase: str = "code"                 # "code" until fldChar separate, then "result"
    result: list[str] = dc_field(default_factory=list)
    child_records: list[dict] = dc_field(default_factory=list)


# Ordered token stream from document.xml: paragraph breaks, field boundaries,
# field-code text, style boundaries, and visible runs.
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
    return "EN.CITE" in code or "CITAVI" in code or "MENDELEY_CITATION" in code


@dataclass
class DocxIngest:
    text: str                       # linear text with citation placeholders
    citations: list[Citation]
    works: dict[str, dict[str, Any]]
    raw_citation_fields: list[dict]  # per top-level citation: marker + works

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": "docx",
            "citations": [c.to_dict() for c in self.citations],
            "works": list(self.works.values()),
            "stats": {
                "n_citations": len(self.citations),
                "n_works": len(self.works),
                "n_unresolved_citations": sum(1 for c in self.citations if not c.resolved),
            },
        }


def parse_document_xml(xml: str) -> DocxIngest:
    stack: list[_Frame] = []
    stream: list[str] = []          # top-level output tokens (text + placeholders)
    para_styles: list[str] = []     # style of each paragraph, in order
    cur_style: Optional[str] = None
    raw_fields: list[dict] = []     # each top-level citation field's payload

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
                    # Nested field: bubble records up, splice visible text in.
                    stack[-1].child_records.extend(records)
                    stack[-1].result.append(result_text)
                elif _is_citation_field(f.code):
                    idx = len(raw_fields)
                    raw_fields.append({"marker": result_text.strip(), "works": records})
                    stream.append(_placeholder(idx))
                else:
                    # Non-citation field (TOC, REF, hyperlink, EN.REFLIST...):
                    # keep its rendered text in the flow.
                    stream.append(result_text)
        elif kind == "INSTR":
            if stack and stack[-1].phase == "code":
                stack[-1].code += val
        elif kind == "TEXT":
            out(val)

    text = "".join(stream)
    citations, works = _link_citations(text, raw_fields, para_styles)
    return DocxIngest(
        text=text,
        citations=citations,
        works=works,
        raw_citation_fields=raw_fields,
    )


def _paragraph_of(offset: int, para_offsets: list[int]) -> int:
    """Index of the paragraph containing a character offset."""
    lo, hi = 0, len(para_offsets) - 1
    idx = 0
    for i, start in enumerate(para_offsets):
        if offset >= start:
            idx = i
        else:
            break
    return idx


def _link_citations(
    text: str, raw_fields: list[dict], para_styles: list[str]
) -> tuple[list[Citation], dict[str, dict]]:
    # Precompute paragraph start offsets (paragraphs separated by '\n').
    para_offsets = [0]
    for m in re.finditer("\n", text):
        para_offsets.append(m.end())

    # Deduplicate works across the whole document (per-work library view).
    works: dict[str, dict] = {}

    citations: list[Citation] = []
    # Walk placeholders in order; assign each to its enclosing sentence.
    sentences = split_sentences(text, placeholder_re=re.compile(
        re.escape(_CITE_OPEN) + r"\d+" + re.escape(_CITE_CLOSE)))

    # Map placeholder index -> owning sentence text (cleaned of placeholders).
    for sent in sentences:
        for m in re.finditer(
            re.escape(_CITE_OPEN) + r"(\d+)" + re.escape(_CITE_CLOSE), sent.raw
        ):
            idx = int(m.group(1))
            rf = raw_fields[idx]
            work_ids = []
            for w in rf["works"]:
                key = w["id"]
                works.setdefault(key, w)
                work_ids.append(key)
            para_idx = _paragraph_of(sent.start, para_offsets)
            section = para_styles[para_idx] if 0 <= para_idx < len(para_styles) else None
            resolved = any(
                works[k].get("DOI") or works[k].get("custom", {}).get("pmid")
                for k in work_ids
            )
            citations.append(
                Citation(
                    id=f"c{idx+1:03d}",
                    marker=rf["marker"],
                    sentence=sent.clean,
                    work_ids=work_ids,
                    paragraph_index=para_idx,
                    section=section,
                    resolved=resolved,
                    note=None if work_ids else "no embedded metadata; needs library or resolution",
                )
            )
    citations.sort(key=lambda c: c.id)
    return citations, works


def ingest_docx(path: str) -> DocxIngest:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    return parse_document_xml(xml)
