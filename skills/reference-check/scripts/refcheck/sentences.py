"""Lightweight sentence segmentation tuned for scientific prose.

We deliberately avoid heavyweight NLP dependencies. The tricky part in academic
text is not the general case but the abbreviations that carry a period without
ending a sentence (e.g., "et al.", "Fig.", "i.e.", "vs.", "approx. 3 mm") and
decimals. We protect those, split on sentence-final punctuation, then restore.

Each returned Sentence keeps three views:
  * ``raw``   – exact substring, citation placeholders still embedded
  * ``clean`` – human-readable text with placeholders replaced by their marker
                (or removed), for display in the audit table
  * ``start`` – character offset of the sentence in the source stream
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Pattern

# Abbreviations that end in '.' but do not end a sentence.
_ABBREV = [
    "et al", "e.g", "i.e", "cf", "vs", "viz", "approx", "ca", "Fig", "Figs",
    "Eq", "Ref", "Refs", "No", "Dr", "Prof", "Mr", "Mrs", "Ms", "St", "Inc",
    "Ltd", "Co", "Jr", "Sr", "Vol", "pp", "p", "ed", "eds", "al",
    "Jan", "Feb", "Mar", "Apr", "Jun", "Jul", "Aug", "Sep", "Sept", "Oct",
    "Nov", "Dec",
]
_ABBREV_RE = re.compile(
    r"\b(" + "|".join(re.escape(a) for a in _ABBREV) + r")\.",
    re.IGNORECASE,
)
_DECIMAL_RE = re.compile(r"(\d)\.(\d)")
_INITIAL_RE = re.compile(r"\b([A-Z])\.")   # single-letter initials, e.g. "D. S."

_DOT = "\x00DOT\x00"


def _protect(s: str) -> str:
    s = _ABBREV_RE.sub(lambda m: m.group(1) + _DOT, s)
    s = _DECIMAL_RE.sub(lambda m: m.group(1) + _DOT + m.group(2), s)
    s = _INITIAL_RE.sub(lambda m: m.group(1) + _DOT, s)
    return s


def _restore(s: str) -> str:
    return s.replace(_DOT, ".")


@dataclass
class Sentence:
    raw: str
    clean: str
    start: int


# Split points: sentence-final punctuation followed by whitespace, or newline.
_SPLIT_RE = re.compile(r"(?<=[.!?])[\"')\]]*\s+|\n+")


def split_sentences(
    text: str, placeholder_re: Optional[Pattern] = None
) -> list[Sentence]:
    """Segment ``text`` into sentences, preserving source offsets.

    ``placeholder_re`` marks citation placeholders so ``clean`` can strip them.
    """
    protected = _protect(text)
    sentences: list[Sentence] = []
    pos = 0
    for m in _SPLIT_RE.finditer(protected):
        raw = _restore(protected[pos:m.start()])
        if raw.strip():
            sentences.append(_mk(raw, pos, placeholder_re))
        pos = m.end()
    tail = _restore(protected[pos:])
    if tail.strip():
        sentences.append(_mk(tail, pos, placeholder_re))
    return sentences


def _mk(raw: str, start: int, placeholder_re: Optional[Pattern]) -> Sentence:
    clean = raw
    if placeholder_re is not None:
        clean = placeholder_re.sub("", raw)
    clean = re.sub(r"\s+", " ", clean)
    clean = re.sub(r"\s+([,.;:)\]])", r"\1", clean)   # drop space left by removed markers
    clean = re.sub(r"\(\s+", "(", clean)
    return Sentence(raw=raw, clean=clean.strip(), start=start)
