# CLAUDE.md — working notes for this repo

This repository holds **Claude Code skills** for the Raredon Lab (biomedical
research, Yale; lung biology / regeneration). Skills are built for the PI's
personal use and shared with lab members. The lab spans highly technical wet-
and dry-lab work, and writes papers, grants, and scientific documents.

The goal is a toolkit of skills across the scientific workflow: **writing,
referencing, data visualization, computational work, experimental design,
funding-opportunity research, grantsmanship, and other wet/dry lab tasks.**

## How skills are structured

Each skill is a top-level directory:

```
<skill-name>/
  SKILL.md       required. YAML frontmatter (name, description) + workflow.
                 The description is what triggers the skill — make it specific
                 about what the skill does and when to use it.
  README.md      human-facing usage.
  scripts/       bundled code (a small importable package + a CLI entry point).
  standards/     editable lab standards the skill enforces (source of truth).
  references/    notes/patterns the skill or a future maintainer needs.
  tests/         standalone tests.
  requirements.txt
  .gitignore     keep run artifacts out of git.
```

## Design principles

1. **Hybrid: deterministic scripts + model judgment.** Put parsing, API calls,
   file generation, and anything reproducible in Python. Reserve the model for
   genuine judgment (e.g. "does this reference support this sentence?"). Scripts
   leave judgment columns blank; the model fills them.
2. **Standard library first.** Minimize third-party dependencies; pin what you
   need in `requirements.txt`. Prefer parsing formats directly (we read .docx
   XML rather than depend on python-docx) when it's not much more code.
3. **Dependency-free tests.** Tests use plain `assert` and run with
   `python3 tests/test_*.py` — no pytest required, so any lab member can run
   them. Cover the tricky deterministic logic (parsers, normalizers, linkage).
4. **Free, keyless APIs.** Use Crossref, NCBI E-utilities, Unpaywall, OpenAlex,
   etc. Pass a contact email (Crossref polite pool); read optional API keys from
   env vars (`NCBI_API_KEY`, `REFCHECK_CONTACT`). Cache HTTP responses on disk.
5. **A canonical data model per skill**, with lossless exports derived from it
   (e.g. reference-check keeps CSL-JSON and exports BibTeX/RIS/.enw/RDF from it).
6. **Never silently drop or guess.** Flag low-confidence results for human
   review rather than fabricating. A flag is a valid, useful output.
7. **Standards live in `standards/`**, not hard-coded. The skill reads them; the
   user edits them to change behavior.

## Working conventions

- **Test on real inputs.** Build parsers against real lab documents (see a
  skill's `demo-inputs/`), not assumptions. Real files are messy in instructive
  ways — e.g. a Word doc may carry embedded citation metadata for only *some*
  citations, with the rest only in the rendered bibliography.
- **Keep artifacts out of git.** Generated tables/libraries, caches, and
  `examples/` outputs are gitignored.
- **Commit/push/PR are deliberate.** Commit to `dev`; push and open PRs to the
  upstream lab fork only when the user asks. Default/main branch is `dev`.
- Co-author commits: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

## Skills in this repo

### reference-check
Extract, verify, and tabulate references in a scholarly document. Reads Word
citation fields (including EndNote embedded records) **and** the rendered
numbered bibliography, unifying them by reference number; verifies each via
Crossref + PubMed (DOI↔PMID cross-fill, abstracts); judges appropriateness per
(citation, reference) pair. Outputs a grouped per-citation audit table, a
per-reference library table, and a reference library in five formats. See
[reference-check/SKILL.md](reference-check/SKILL.md). Key lesson baked into its
design: **references may live in the rendered bibliography, not the citation
fields — read both.**
