# coding-standards

**Version 0.1.0**

Write R or Python for Raredon Lab data-science work the lab way — code that is
readable, reproducible, and transferable to collaborators, reviewers, and yourself
six months from now. Encodes the Computational Lab Manual, Ch. 04–06 (the **manual
is the source of truth**).

## How the lab works with Claude

The lab uses Claude to **generate executable code you run locally**, not to process
data. So this skill, by default:

- writes code against a **described** data structure (you never upload raw data),
- produces **linear, load-from-disk → operate → save-to-disk** scripts with
  date-stamped outputs, and
- hands you a runnable `.R`/`.py`/`.qmd`/helper you execute and validate.

## What it produces

- **Scripts** with the standard header block (title, author, date, purpose,
  inputs, outputs, libraries, path variables), one coherent operation each, paths
  declared at the top, and no hardcoded values.
- **Functions** in `functions/` when logic is reused or >~25 lines —
  parameterized, `snake_case`, documented (Roxygen in R, docstrings in Python).
- **Narrated analysis** in **Quarto** (`.qmd`) → HTML in `docs/`, with clean chunk
  options and named chunks.
- **Files named** `NN_YYYYMMDD_AB_descriptive-name.ext` (outputs too).

## R and Python

R is primary; Python (via `uv` + Quarto) follows the same science-facing
conventions — same header block, naming, `functions/`, and narrated docs. Only the
ecosystem tooling differs (renv↔uv, Roxygen↔docstrings). Parity table in
`references/coding-standards.md`.

## What it won't do (lab boundaries)

- It won't draft **scientific-paper prose** (methods/results/discussion/captions) —
  that's human work (grant text may be AI-assisted).
- It won't **design figures/visualizations** — drawing and viz design are human
  thinking. Writing the plotting code you specify is fine.
- It won't invent citations — use the `reference-check` skill for verified refs.

## Consent

Standards are **offered, never forced**; your choice is recorded in the repo's
`CLAUDE.md`. Work your own way whenever you want.

## Files

- `references/coding-standards.md` — the full standard + R↔Python parity.
- `references/quarto-and-environments.md` — Quarto narration + renv/uv.
- `assets/` — copy-paste header-block templates (R, Python).

## Pairs with

The **github-standards** skill (how the repo around the code is organized).
