---
name: github-standards
version: 0.1.0
description: >-
  Set up and run version control for Raredon Lab computational projects the lab
  way: initialize or structure a repository, apply the fork model (RaredonLab
  origin main+dev -> personal fork repo-AB -> local clone), configure git and
  remotes, add the standard .gitignore / directory layout / repo CLAUDE.md, and
  drive the daily commit -> push -> pull-request-to-dev loop (GitHub Desktop
  friendly). Use when a user starts, organizes, forks, clones, commits, or opens
  a PR on a lab coding project in any language, wants a new repo initialized,
  asks about lab git/GitHub standards, or is coding in a RaredonLab-linked repo.
  Always offer; never force. Pairs with the coding-standards skill.
---

# github-standards

Make lab version control frictionless and consistent, especially for new users on
GitHub Desktop. This skill encodes the workflow in the Raredon Lab Computational
Manual, Ch. 03 (Git & GitHub) — the **manual is the source of truth**; this skill
applies it and links back to it.

## Consent model (always)

Standards are offered, never imposed. On detecting lab version-control work:

1. **Check the repo's `CLAUDE.md`** for a marker line:
   `raredon-standards: github v0.1 (opted-in: yes|no)`.
2. If absent, **offer once**, in one line: *"This looks like lab work — want me to
   set it up to Raredon Lab GitHub standards? I can, or leave it as-is."*
3. **Record the choice** in the repo `CLAUDE.md` marker so it isn't re-asked.
   If they decline, respect it and proceed as they wish.

The user is always free to do it their own way. Surface the standard and the
reason; let them choose.

## Role awareness

Behavior differs by role; determine it once (ask if unknown, or read
`~/.claude/raredon-lab.json` `{ "role": "pi" | "member", "initials": "AB" }`):

- **PI / repo-admin (e.g. MSBR):** may create the RaredonLab **origin**, set
  `dev` as default, add collaborators, and merge `dev` -> `main`.
- **Member:** works from a **personal fork**; never targets `main`; opens PRs to
  origin `dev`.

## Core workflow

### 1. Assess project state
Detect: is there a git repo? remotes (`origin`, `upstream`)? is `origin` a fork of
`RaredonLab/*`? is the directory structured to standard? Report briefly, then
offer next steps.

### 2. Initialize / structure a repository
Apply `references/github-standards.md` (fork model, structure, `.gitignore`,
naming). Scaffold the standard layout and files using the templates in `assets/`.

- **New lab repo, user is a member** (per lab decision): **scaffold locally** to
  standard, then **draft a PI request** (`assets/pi-request-template.md`) to
  create the `RaredonLab/<name>` origin (main+dev, dev default). Once it exists,
  help them **fork** it to `<username>/<name>-AB` and clone.
- **New lab repo, user is the PI:** create the origin from the **RaredonLab org**
  (browser/`gh`), main+dev with `dev` default, add collaborators; or instantiate
  the `RaredonLab/analysis-template` template repo if present.
- **Existing folder to bring up to standard:** add missing dirs
  (`functions/ scripts/ markdowns/ docs/ figures/ output/ data/`), `.gitkeep`s,
  `.gitignore`, `README.md`, repo `CLAUDE.md`; do not move the user's files
  without asking.

### 3. Wire the fork model
`origin` = the user's personal fork; `upstream` = `RaredonLab/<name>`; default
working branch `dev`. Verify with `git remote -v` and set tracking to
`origin/dev`. New users: give the **GitHub Desktop** click-path (File -> Clone,
Fork button, Push origin) alongside the CLI.

### 4. Daily loop
`commit -> push to fork -> PR to origin dev`. Enforce nothing, but remind: the
**end-of-day push is mandatory** per the manual. You may write commit messages
(what changed + why, specific) — the user reviews and stands behind them. PRs
target `dev`; **never `main`**. Self-approve/merge only if no conflicts and no
changes to shared infrastructure (`functions/`, `CLAUDE.md`, `.gitignore`,
`README.md`); otherwise flag for PI review.

### 5. Repo CLAUDE.md
Every lab repo has a root `CLAUDE.md` (manual Ch. 06). Generate one from
`assets/repo-CLAUDE.md.template` including the `raredon-standards:` marker so
future sessions follow lab standards and the consent choice persists.

## Guardrails
- Never commit data/credentials (the `.gitignore` handles it; also see manual
  Ch. 03 §6). If a credential was committed, tell the user to notify the PI and
  rotate the key.
- Don't force-push, rewrite shared history, or touch `main` without explicit PI
  authorization.
- Pushes/PRs are the user's outward actions — set them up, but let them run
  the push from their own authenticated terminal / GitHub Desktop.

## References
- `references/github-standards.md` — the full lab standard + templates.
- `assets/` — `.gitignore` (R + Python), repo structure, per-repo CLAUDE.md
  template, PI-request template.
- Source of truth: Raredon Lab Computational Manual, Ch. 03.
