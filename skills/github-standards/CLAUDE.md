# CLAUDE.md — github-standards

Skill-specific working notes. Repo-wide conventions: [root CLAUDE.md](../../CLAUDE.md).
Usage: [README.md](README.md). Contract: [SKILL.md](SKILL.md).

## What this skill does
Applies the Raredon Lab git/GitHub workflow (Manual Ch. 03) to a project: repo
init/structure, the fork model, the daily commit->push->PR-to-dev loop. Offer,
never force; record consent in the repo's `CLAUDE.md`.

## Source of truth
The **Computational Lab Manual, Ch. 03** is canonical
(`RaredonLab/Computational-Lab-Manual`). `references/github-standards.md` is a
distillation — if it and the manual disagree, the manual wins; update the ref.

## Key invariants (don't violate)
- New origins come from the **RaredonLab org**, not personal accounts.
- `dev` is the default/working branch; **`main` is PI-only and never a PR target**
  from a fork.
- Personal fork is named `<repo>-AB`; push there, PR to origin `dev`.
- Self-approval only with no conflicts and no changes to shared infrastructure
  (`functions/`, `CLAUDE.md`, `.gitignore`, `README.md`).
- Never commit data/credentials. Never force-push or rewrite shared history.
- The human runs the outward push/PR from their own authenticated client.

## Role handling
PI/admin vs member changes the repo-init path (create-origin vs
scaffold+PI-request). Determine role once; a user-level `~/.claude/raredon-lab.json`
(`{"role","initials"}`) is the intended cache. MSBR = PI/admin.

## Consent marker
Repo `CLAUDE.md` carries `raredon-standards: github v0.1 (opted-in: yes|no)`.
Read it before offering; write it after the user chooses.

## New-user ergonomics
Most members use **GitHub Desktop**. Always give the GUI click-path (Clone, Fork,
Commit to dev, Push origin, Contribute->PR) next to any CLI. Avoid assuming `gh`
or SSH; offer them only as advanced accelerators.

## Extending
- If `RaredonLab/analysis-template` exists, prefer instantiating it over hand-
  scaffolding (keeps structure current).
- Optional future: a pre-commit hook checking header blocks / file naming (see
  the reproducibility/pre-commit patterns in pedrohcgs/claude-code-my-workflow) —
  keep it opt-in; new users should not hit friction.

## Roadmap / maturity
v0.1.0 — first version: SKILL contract, standard reference + templates. Not yet:
executable repo-scaffolding helper, `gh`-based origin creation for the PI, the
template repo, pre-commit hooks. Re-score when those land.
