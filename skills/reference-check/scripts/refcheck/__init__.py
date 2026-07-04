"""refcheck: extract, verify, and tabulate references from scholarly documents.

Phase 1 provides the ingest + normalization backbone. The canonical in-memory
representation of a cited work is a CSL-JSON-compatible dict (see ``model.py``),
from which every export format (BibTeX, RIS, EndNote .enw, Zotero RDF, CSL-JSON)
is derived.
"""

__version__ = "0.3.0"
