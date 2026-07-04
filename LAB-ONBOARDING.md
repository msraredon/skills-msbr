# Lab onboarding — Raredon Lab Claude Code skills

A hand-to-a-labmate guide. No prior experience needed. This installs the lab's
Claude Code skills — starting with **reference-check**, which checks that every
citation in a document is real, formats them to lab standard, and tells you when
a reference doesn't actually support the sentence it's attached to.

## What you need first

1. **Claude Code** installed and working (the `claude` command in your terminal,
   or the Claude Code app). If you don't have it: https://claude.com/claude-code
2. **Python 3** (macOS and Linux already have it). Check with `python3 --version`.

You do **not** need to understand any code. You just describe what you want.

## Install (once)

In a Claude Code session, run these two commands (they start with `/`):

```
/plugin marketplace add https://github.com/RaredonLab/skills
/plugin install lab-skills@raredon-lab
```

Then **start a new session** (close and reopen, or run `claude` again). That's it
— the skills are now available in every project on your computer, and refresh
when the lab updates them.

## How to use it (this is the whole trick)

You don't type a special command. **Just describe your goal in plain English**,
and the right skill turns itself on. Open the folder that has your document, start
Claude Code there, and say something like:

- *"Check and tabulate the references in Manuscript.docx."*
- *"Are the citations in this paper real, and do they support what I'm claiming?"*
- *"Build me a clean reference library from this document for EndNote."*

Currently the reference checker reads **Microsoft Word (`.docx`)** documents.

## What you get back

In a new folder next to your document you'll find:

- **`…_references.xlsx`** — a spreadsheet with two tabs:
  - **Citations (audit)** — every citation in order, with the sentence it's in
    and, beneath it, each reference it points to; a plain verdict of whether the
    reference **Supports / Partial / Unclear / Mismatch** the sentence. Problem
    rows are highlighted.
  - **References (library)** — one row per unique paper, with clickable DOI /
    PubMed / open-access links you can check yourself.
- **A reference library** in five formats (`.bib`, `.ris`, `.enw`, `.rdf`,
  `.csl.json`) that import into EndNote, Zotero, Mendeley, or LaTeX.
- **`…_REVIEW.md`** — a short list of anything that needs your eyes.

Start with the highlighted rows and the REVIEW file.

## Privacy — important for unpublished work

To verify a reference, the tool sends only the **identifier or title** of each
reference to free public databases (Crossref, PubMed, Unpaywall). **Your
manuscript text is not uploaded.** If you're extra cautious with an unpublished
draft, add the word **offline** to your request (e.g. *"check the references
offline"*) and it will skip all internet lookups and use only what's already in
the document.

## Keeping it up to date

When the lab improves a skill:

```
/plugin marketplace update raredon-lab
```

Then start a new session.

## If something doesn't work

- **The skill didn't turn on?** Make sure you started a **new session** after
  installing. You can also just say: *"use the reference-check skill."*
- **An error about `openpyxl`?** Run `pip3 install openpyxl` (only needed for the
  Excel file; the other outputs still work without it).
- **References won't verify?** You need an internet connection (unless you asked
  for "offline"). Very old papers or editorials sometimes have no online record —
  the tool flags those for you rather than guessing.
- **Still stuck?** Contact the lab maintainer (see the repo owner) — and mention
  what you typed and what happened.

## For the curious

Each skill lives in `skills/<name>/` with a `README.md` (what it does) and a
`SKILL.md` (how Claude runs it). The lab's citation standard — required fields,
what gets flagged — is an editable file at
`skills/reference-check/standards/lab-reference-standard.md`. Suggest changes via
a pull request so everyone benefits.
