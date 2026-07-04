# Raredon Lab GitHub standard (reference)

Distilled from the Computational Lab Manual, Ch. 03. The manual is canonical;
keep this in sync. Applies to any language (R, Python, other).

> This describes the ideal workflow. The skill applies it **gently**: it keeps
> Claude's own repo/commit output aligned and helps when asked. It never enforces
> structure, naming, or process on anyone's work, and always helps people commit
> and push whatever they have. Words like "must"/"mandatory" below reflect the
> manual's language, not a gate the skill imposes.

## The fork model
Three tiers, connected by commit -> push -> pull request:

```
RaredonLab/<name>  (ORIGIN)         main (protected, PI only)  +  dev (default, shared)
        ▲ pull request -> dev
<username>/<name>-AB  (YOUR FORK)   dev  (your working copy)
        ▲ push            ▼ clone
local clone            ~/projects/<name>-AB  and/or  /hpc/path/<name>-AB
```

- **Origin** lives in the **RaredonLab org** (not a personal account). `main` +
  `dev`; `dev` is the default. `main` is protected — PI/authorized only.
- **Personal fork** is named `<name>-AB` (append your initials). Fork `dev` at
  minimum. This is where you push.
- **Local clone** of your fork on laptop and/or HPC.

## Prerequisites (each member, once)
1. Personal GitHub account with a professional username (it becomes your
   scientific identity).
2. Send the username to the PI to be added as a collaborator; accept the email
   invite.
3. Install a Git interface — **new users: GitHub Desktop**. Advanced: CLI / Claude.
4. Configure identity:
   ```bash
   git config --global user.name "Your Full Name"
   git config --global user.email "your.email@yale.edu"
   ```

## Setting up a repository
**New RaredonLab origin (the PI, MSBR):** create the repo from the **RaredonLab
org**, initialize `main` + `dev`, set `dev` as default, add collaborators
(Settings -> Collaborators). Keep it loose — an almost-empty repo (even just a
README) is a fine start; the structure below is optional and can be added later.

**Working from it, forking + cloning (once per repo):**
1. On GitHub, open the RaredonLab origin repo (signed in to your account).
2. **Fork** -> your account; rename to `<name>-AB`. Fork `dev` (and `main` only if
   your role needs it).
3. **Clone your fork** (not the origin) to laptop/HPC. GitHub Desktop: File ->
   Clone Repository -> your fork. CLI:
   ```bash
   git clone https://github.com/<username>/<name>-AB.git
   cd <name>-AB
   git remote add upstream https://github.com/RaredonLab/<name>.git
   ```

## Standard directory structure
Git holds code, docs, and lightweight HTML vignettes only. Large data/outputs
(20–50 GB objects, matrices, spatial outputs) live on HPC/shared storage, with
paths declared at the top of each script. Keep it **flat** — no deep nesting.

```
<name>-AB/
├── functions/     # reusable helpers (generalized, documented). NOT R/
├── scripts/       # numbered, dated, initialed analysis scripts
├── markdowns/     # Quarto (.qmd) / Rmarkdown (.Rmd) narrated analysis
├── docs/          # knit/rendered HTML vignettes — committed
├── figures/       # small figures for README/docs only
├── output/        # large outputs — gitignored (keep .gitkeep)
├── data/          # raw data — gitignored (keep .gitkeep)
├── .gitignore
├── README.md
├── CLAUDE.md      # AI context + raredon-standards marker
└── <name>.Rproj   # (R) or pyproject.toml / .venv (Python)
```
`output/` and `data/` are gitignored but kept via `.gitkeep` (`touch
output/.gitkeep`). See `assets/` for `.gitignore` templates.

## Daily workflow
1. **Edit** in your local clone.
2. **Commit** at logical stopping points and always end-of-day. GitHub Desktop:
   review files, write a message, Commit to `dev`. CLI: `git add -A && git commit`.
3. **Push to your fork** — GitHub Desktop: Push origin. CLI: `git push origin dev`.
4. **Pull request** to origin `dev` when a meaningful unit is ready.

**End-of-day push is mandatory.** Local-only code cannot be reviewed or helped
with, and is lost if the machine fails.

## Commit messages
Say **what changed and why**, specifically. The history is a scientific record.
- Good: `Add QC filtering with doublet removal; parameterize min.cells in helpers_qc.R`
- Bad: `wip`, `update`, `fixes`, `asdf`

Claude may draft commit messages from your diff; review and stand behind them.

## Pull requests
All fork -> origin changes go through a PR, even trivial ones. Open from your fork
("Contribute" -> "Open pull request"); confirm base = `RaredonLab/<name>` branch
`dev`. Write a descriptive title + brief summary.
- **Self-approve/merge** only if no conflicts AND no changes to shared
  infrastructure: `functions/`, `CLAUDE.md`, `.gitignore`, `README.md`. Those
  always go to PI review.
- **Never PR to `main`.** Merging `dev` -> `main` is a deliberate, infrequent PI
  action at stable milestones.

## Branch rules
| Branch | Lives in | Purpose | Who merges |
|--------|----------|---------|-----------|
| `main` | origin only | stable, milestone-worthy record | PI / authorized only |
| `dev`  | origin + all forks | active shared development | members via PR from fork |

Keep branching minimal; discuss feature branches with the PI first.

## File naming
`NN_YYYYMMDD_AB_descriptive-name.ext`
- `NN` two-digit sequence (`01`, `02`); `YYYYMMDD` ISO date no separators;
  `AB` author initials (2–4 uppercase); `descriptive-name` lowercase, hyphenated.
- Examples: `01_20250301_AB_preprocessing-qc.R`,
  `02_20250308_CD_clustering-umap.qmd`, `01_20250301_AB_eda-overview.html`.
- Stamp **outputs** too: `02_20250308_NW_umap-celltype.pdf`, not `plot_final_v3.pdf`.

## Using Claude with Git
Encouraged for the mechanical parts: drafting commit messages, opening/refining
PRs, scaffolding structure, writing `.gitignore`/`CLAUDE.md`. The user reviews and
owns the result. Never let AI push to `main` or rewrite shared history.
