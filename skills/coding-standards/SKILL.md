---
name: coding-standards
version: 0.2.0
description: >-
  When generating R or Python for Raredon Lab data-science work, align your own
  output with the lab's coding conventions (standard header block; one coherent
  operation per script; paths as named variables; no hardcoding; reusable logic
  in functions/; Quarto narration -> docs/; NN_YYYYMMDD_AB naming) and the lab
  pattern of producing executable code the user runs locally against described
  (not uploaded) data. Also available if a user asks about lab coding standards.
  Use when writing/refactoring analysis scripts, functions, notebooks, or
  packages for lab work in any language. Gentle and optional: never enforce
  standards on a user's own code or add friction. Pairs with github-standards.
---

# coding-standards

A background resource for Raredon Lab coding conventions (Computational Lab Manual,
Ch. 04–06 — the **manual is the source of truth**). Two jobs, in priority order:

1. **Steer your own output.** When *you* (Claude) write R/Python for lab
   data-science, produce it in the lab style by default, so it is readable,
   reproducible, and transferable without anyone having to ask.
2. **Help when asked.** If a user wants to learn or apply the standards
   ("write this the lab way," "what's the header block?"), apply
   `references/coding-standards.md`.

## How this skill behaves — gentle, no friction

- **Never enforce or correct a user's own code.** If someone writes or requests
  something off-standard — messy, non-linear, misnamed, exploratory — that is
  completely fine. Help them do what they want. They are learners; curiosity and
  momentum matter more than polish.
- **No nagging.** Mention a convention only if clearly useful in the moment, then
  drop it. Otherwise stay quiet and just apply good style to what *you* generate.
- The standards exist to keep *your* output consistent and to help anyone who
  asks — not to police anyone's workflow.

## The core working pattern (how you produce, by default)

The lab uses Claude to generate **executable code the user runs locally**, not to
process data:

- **Describe data, don't ingest it.** Write against a *described* structure
  (dimensions, columns, object type), not pasted raw data — replicable, and keeps
  sensitive data out of AI tools. *Light touch:* this is your default; do not
  police what a user chooses to paste or ask for.
- **Linear, save-to-disk workflows:** load from disk -> operate -> save to disk,
  date-stamped, so results regenerate and validate.
- **Hand back runnable artifacts** (a `.R`/`.py` script, a `.qmd`, a `functions/`
  helper), not answers the user can't reproduce.

## What aligned output looks like (aim for this in your own code)
- **Header block** in order: title (= filename), author + initials, date, purpose,
  Inputs (abs paths), Outputs (abs paths), Libraries, path variables. Templates:
  `assets/header-block.R`, `assets/header-block.py`.
- **One coherent operation per script**; paths as named variables at the top; no
  hardcoded thresholds/columns/paths; `# ── section ──` dividers; comments that
  retrace the reasoning.
- **Reusable/long logic (>~25 lines) -> `functions/`**, parameterized, `snake_case`,
  documented (Roxygen in R, docstrings in Python).
- **Narrated analysis in Quarto (`.qmd`) -> HTML in `docs/`** (see
  `references/quarto-and-environments.md`).
- **Naming** `NN_YYYYMMDD_AB_descriptive-name.ext`, outputs included.

Suggest any of these to a user only if they ask or it clearly helps; never require.

## R ↔ Python parity
Keep science-facing conventions identical across languages; swap only tooling
(renv↔uv, Roxygen↔docstrings, `.Rproj`↔`pyproject.toml`). Table in
`references/coding-standards.md`.

## Scope boundaries (from the manual)
- Don't draft scientific-paper prose (methods/results/discussion/captions) — human
  work. Grant text may be AI-assisted.
- Don't design figures/visualizations as an AI task; writing user-specified
  plotting code is fine.
- Never invent citations (use the `reference-check` skill).

## References
- `references/coding-standards.md` — full standard + R/Python parity.
- `references/quarto-and-environments.md` — Quarto narration, renv/uv, packages.
- `assets/` — header-block templates.
- Source of truth: Computational Lab Manual, Ch. 04–06.
