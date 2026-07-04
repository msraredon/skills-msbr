# CLAUDE.md — coding-standards

Skill-specific working notes. Repo-wide conventions: [root CLAUDE.md](../../CLAUDE.md).
Usage: [README.md](README.md). Contract: [SKILL.md](SKILL.md).

## What this skill is
A gentle, background resource. Primary job: keep **Claude's own** R/Python output
for lab data-science in the Manual Ch. 04–06 style (header block, one-operation
scripts, `functions/`, Quarto narration, lab naming, describe-data /
generate-executable-code / save-to-disk). Secondary: help a user who asks. It is
**not** an enforcement layer.

## Behavior rules (the whole point)
- **Never enforce or correct a user's own code.** Messy, non-linear, misnamed,
  exploratory, or off-standard work is fine — help them do what they want. No
  friction. Learners and momentum first.
- **No nagging.** Mention a convention only if clearly useful, then drop it.
  Otherwise just apply good style to what *you* generate and stay quiet.

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

## No consent ledger, no policing
Don't gate behavior on a marker or ask permission to help. A repo `CLAUDE.md` may
note the project is lab work (helps you steer your own output), but it is never
required and never a compliance check. Treat everyone as a user; no role logic.

## Extending
- Candidate borrowings (inspect first): ab604/claude-code-r-skills (Quarto
  authoring, R-package release checklist); pedrohcgs/claude-code-my-workflow
  (reproducibility audit — cross-check numeric claims against script outputs).
- Possible future: language-specific linters/formatters (air/styler for R, ruff
  for Python) offered opt-in; a header-block checker.

## Roadmap / maturity
v0.2.0 — reframed to gentle/background/no-enforcement (dropped the consent-marker
gating and role logic from v0.1). SKILL contract + reference standard + header
templates in place. Deliberately no linter/enforcement automation — that would add
the friction we're avoiding. Worked R/Python examples are a fine future addition.
