"""Standalone tests for the deterministic core. Run: python3 tests/test_core.py

No pytest dependency — plain asserts so any lab member can run it.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from refcheck.model import normalize_doi, normalize_pmid, parse_author, work_key, make_work
from refcheck.sentences import split_sentences
from refcheck.docx_ingest import parse_document_xml
from refcheck.endnote import records_from_fieldcode


def test_normalize_doi():
    assert normalize_doi("https://doi.org/10.1234/AbC") == "10.1234/abc"
    assert normalize_doi("doi: 10.1000/xyz.") == "10.1000/xyz"
    assert normalize_doi("not a doi") is None


def test_normalize_pmid():
    assert normalize_pmid("PMID: 12345") == "12345"
    assert normalize_pmid("abc") is None


def test_parse_author():
    assert parse_author("Goldstein, D. S.") == {"family": "Goldstein", "given": "D. S."}
    a = parse_author("Jane Roe")
    assert a["family"] == "Roe" and a["given"] == "Jane"


def test_work_key_prefers_doi_then_pmid():
    w = make_work(title="t", doi="10.1234/x", pmid="99")
    assert work_key(w) == "doi:10.1234/x"
    w2 = make_work(title="t2", pmid="99")
    assert work_key(w2) == "pmid:99"


def test_sentence_split_protects_abbrev_and_decimals():
    text = "Growth was 3.5 mm in ferrets et al. observed it. A second sentence follows."
    sents = split_sentences(text)
    assert len(sents) == 2, [s.clean for s in sents]
    assert "3.5 mm" in sents[0].clean


def _wrap(body: str) -> str:
    return f'<w:document><w:body>{body}</w:body></w:document>'


def _field(code: str, result: str, nested_data_code: str = "") -> str:
    """Build a Word field: begin, [nested data field], instr, separate, result, end."""
    inner = ""
    if nested_data_code:
        inner = (
            '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
            f'<w:r><w:instrText>{nested_data_code}</w:instrText></w:r>'
            '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
        )
    return (
        '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
        + inner
        + f'<w:r><w:instrText>{code}</w:instrText></w:r>'
        '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
        f'<w:r><w:t>{result}</w:t></w:r>'
        '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
    )


ENDNOTE_RECORD = (
    "ADDIN EN.CITE.DATA &lt;EndNote&gt;&lt;Cite&gt;&lt;record&gt;"
    "&lt;contributors&gt;&lt;authors&gt;&lt;author&gt;Smith, J.&lt;/author&gt;&lt;/authors&gt;&lt;/contributors&gt;"
    "&lt;titles&gt;&lt;title&gt;A study&lt;/title&gt;&lt;secondary-title&gt;J Test&lt;/secondary-title&gt;&lt;/titles&gt;"
    "&lt;dates&gt;&lt;year&gt;2020&lt;/year&gt;&lt;/dates&gt;"
    "&lt;electronic-resource-num&gt;10.1000/abc&lt;/electronic-resource-num&gt;"
    "&lt;accession-num&gt;12345&lt;/accession-num&gt;"
    "&lt;/record&gt;&lt;/Cite&gt;&lt;/EndNote&gt;"
)


def test_nested_endnote_field_extracts_record_and_sentence():
    para = (
        '<w:p><w:r><w:t>The lung regenerates after injury</w:t></w:r>'
        + _field("ADDIN EN.CITE", "1", nested_data_code=ENDNOTE_RECORD)
        + '<w:r><w:t>. A different unrelated sentence.</w:t></w:r></w:p>'
    )
    ing = parse_document_xml(_wrap(para))
    assert len(ing.citations) == 1, ing.citations
    c = ing.citations[0]
    assert c.marker == "1"
    assert c.resolved is True
    # citation attaches to the FIRST sentence, not the second
    assert "regenerates after injury" in c.sentence
    assert "unrelated" not in c.sentence
    # embedded record captured with DOI + PMID
    assert len(ing.works) == 1
    w = next(iter(ing.works.values()))
    assert w["DOI"] == "10.1000/abc"
    assert w["custom"]["pmid"] == "12345"


def test_dataless_citation_flagged_not_dropped():
    para = (
        '<w:p><w:r><w:t>Claim without data</w:t></w:r>'
        + _field("ADDIN EN.CITE", "7")
        + '<w:r><w:t>.</w:t></w:r></w:p>'
    )
    ing = parse_document_xml(_wrap(para))
    assert len(ing.citations) == 1
    c = ing.citations[0]
    assert c.marker == "7"
    assert c.resolved is False
    assert c.work_ids == []
    assert c.note and "needs library" in c.note


def test_records_from_fieldcode_multiple_cites():
    code = ENDNOTE_RECORD.replace("&lt;", "<").replace("&gt;", ">")
    recs = records_from_fieldcode(code)
    assert len(recs) == 1 and recs[0]["DOI"] == "10.1000/abc"


def run():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
        passed += 1
    print(f"\n{passed}/{len(tests)} passed")


if __name__ == "__main__":
    run()
