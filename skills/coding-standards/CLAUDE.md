# CLAUDE.md — coding-standards

Skill-specific working notes. Repo-wide conventions: [root CLAUDE.md](../../CLAUDE.md).
Usage: [README.md](README.md). Contract: [SKILL.md](SKILL.md).

## What this skill does
Writes R/Python for lab data-science to the Manual Ch. 04–06 standard: header
block, one-operation scripts, `functions/`, Quarto narration, lab naming, and the
describe-data / generate-executable-code / save-to-disk working pattern. Offer,
never force; record consent in the repo `CLAUDE.md`.

## Source of truth
**Computational Lab Manual, Ch. 04–06** (`RaredonLab/Computational-Lab-Manual`).
The `references/` files distill it; if they disagree with the manual, the manual
wins — update the ref.

## Load-bearing behaviors (get these right)
- **Executable-code-not-answers.** Default to producing runnable scripts the user
  executes locally; write against *described* data. Light touch on inputs — don't
  police pastes, but never assume/require real data.
- **Header block is mandatory** and in order (title, author, date, purpose,
  inputs, outputs, libraries, path variables). Paths are named variables at the
  top; nothing hardcoded.
- **One coherent operation per script**; split sprawl.
- **`functions/` not `R/`** for helpers; >~25 lines or reused -> extract;
  parameterize; document (Roxygen / docstrings); `snake_case`.
- **Quarto (.qmd)** is the cross-language narration default -> `docs/*.html`.
- **Naming** `NN_YYYYMMDD_AB_descriptive-name.ext`, outputs included.

## Hard scope boundaries (from the manual — do not cross)
- No scientific-paper prose (methods/results/discussion/captions). Grants may be
  AI-assisted.
- No visualization/figure *design* as an AI task (writing user-specified plotting
  code is fine).
- No invented citations (defer to `reference-check`).

## R ↔ Python parity
Keep science-facing conventions identical; swap only tooling: renv↔uv (`pyproject`
+ `uv.lock`), Roxygen↔docstrings, `.Rproj`↔`pyproject.toml`, CRAN↔pytest/mkdocs.
Parity table in `references/coding-standards.md`.

## Consent marker
Repo `CLAUDE.md`: `raredon-standards: coding v0.1 (opted-in: yes|no)`. Read before
offering; write after the user chooses.

## Extending
- Candidate borrowings (inspect first): ab604/claude-code-r-skills (Quarto
  authoring, R-package release checklist); pedrohcgs/claude-code-my-workflow
  (reproducibility audit — cross-check numeric claims against script outputs).
- Possible future: language-specific linters/formatters (air/styler for R, ruff
  for Python) offered opt-in; a header-block checker.

## Roadmap / maturity
v0.1.0 — SKILL contract + reference standard + header templates. Not yet: an
executable header/naming linter, package scaffolding helpers, worked R/Python
examples, an eval of standard-adherence. Re-score when those land.
