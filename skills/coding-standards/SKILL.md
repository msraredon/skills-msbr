---
name: coding-standards
version: 0.1.0
description: >-
  Write R or Python for Raredon Lab data-science work the lab way: every script
  carries the standard header block (title/author/date/purpose/inputs/outputs/
  libraries/paths), does one coherent operation, declares paths as named
  variables, avoids hardcoding, extracts reused/long logic into documented
  functions/, narrates finished work in Quarto/Rmarkdown -> HTML in docs/, and
  follows the NN_YYYYMMDD_AB_descriptive-name naming. Produces executable,
  linear, load-from-disk / operate / save-to-disk scripts the user runs locally
  against data they only describe. Use when writing/refactoring analysis scripts,
  functions, notebooks, or packages for lab work in any language, or when a user
  asks to apply lab coding standards. Offer; never force. Pairs with
  github-standards.
---

# coding-standards

Help lab members (and the PI) produce computational work that is readable,
reproducible, and transferable — code someone else, or you in six months, can run
and build on. Encodes the Computational Lab Manual, Ch. 04–06. The **manual is the
source of truth**; this skill applies it.

## The core working pattern (default behavior)

The lab works by having Claude generate **executable code that the user runs
locally**, not by having Claude process data. So by default:

- **Describe data, don't ingest it.** Write code against a *described* data
  structure (dimensions, columns, object type), never against pasted raw data.
  This keeps outputs replicable and keeps sensitive data out of AI tools (manual
  Ch. 06; Yale policy). *Light touch:* follow this pattern by default; do not
  police what the user chooses to paste.
- **Linear, save-to-disk workflows.** Load from disk -> operate -> save to disk,
  with date-stamped outputs, so every result can be regenerated and validated.
- **Hand back runnable artifacts:** a `.R`/`.py` script, a `.qmd`, or a
  `functions/` helper the user executes and checks — not an answer they can't
  reproduce.

## Consent model
Offer, don't impose. If the repo `CLAUDE.md` marker
(`raredon-standards: coding v0.1 (opted-in: yes|no)`) is absent, offer once:
*"Want me to write this to Raredon Lab coding standards?"* Record the choice.
Members may always work their own way; surface the standard and its payoff.

## What to produce

### Scripts (.R / .py) — the primary medium
- **Header block** at the top, in order: title (= filename), author + initials,
  date, plain-language purpose, **Inputs** (absolute paths), **Outputs**
  (absolute paths), **Libraries**, **File-path variables**. Use the templates in
  `assets/header-block.R` / `assets/header-block.py`.
- **One coherent operation per script** (~one day of work to reproduce). Split
  when a script starts doing multiple distinct goals.
- **Declare every path as a named variable in the header**; reference the
  variable throughout. Never bury a path inline.
- **No hardcoding.** Thresholds, column names, patterns -> named variables or
  function arguments with sensible defaults.
- **Section dividers** (`# ── name ─────`) for a navigable outline; comment enough
  to retrace your reasoning.

### Functions (functions/)
- Extract logic that is **>~25 lines or reused** into `functions/`. Parameterize
  anything that could vary; return one object explicitly; `snake_case`.
- Document with **Roxygen** (R) / **docstrings** (Python, NumPy or Google style).
  This makes an eventual package transition seamless.

### Narrated analysis (Quarto / Rmarkdown -> docs/)
- Script first, narrate second. Use **Quarto (`.qmd`)** as the cross-language
  default (renders R and Python). Standard YAML header; global chunk options that
  suppress package/warning noise; **named chunks**; render HTML into `docs/` and
  commit it. See `references/quarto-and-environments.md`.

### Packages
- When tools are broadly reusable across projects, build a package to CRAN-level
  (R) / packaging (Python) standards — documented, tested, with a docs site and a
  changelog. AI-assisted package scaffolding is encouraged. See the reference.

## Language parity (R ↔ Python)
R is primary; Python is growing. Keep conventions parallel — same header block,
naming, `functions/`, Quarto narration; swap only the ecosystem tooling (renv↔uv,
Roxygen↔docstrings, .Rproj↔pyproject). Full table in
`references/coding-standards.md`.

## Scope boundaries (from the manual — respect these)
- **Do not draft scientific-paper prose** (methods, results, discussion, figure
  captions) — human work. Grant text may be AI-assisted.
- **Do not design visualizations/figures as an AI task** — drawing and viz design
  are human thinking. Writing the *plotting code* the user specifies is fine.
- Literature/citations must be verifiable (PMIDs/DOIs); never invent one. (See the
  `reference-check` skill.)

## References
- `references/coding-standards.md` — full standard + R/Python parity.
- `references/quarto-and-environments.md` — Quarto narration, renv/uv, packages.
- `assets/` — copy-paste header-block and Quarto setup templates.
- Source of truth: Computational Lab Manual, Ch. 04–06.
