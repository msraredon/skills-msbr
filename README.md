# skills-msbr

A collection of [Claude Code](https://claude.com/claude-code) **skills** for the
Raredon Lab — reusable, self-contained capabilities that Claude can invoke to do
real scientific work. Built for personal use and shared with the lab; changes
flow upstream to the lab fork via pull requests.

Each skill is a directory under `skills/` with a `SKILL.md` (what it does + how
Claude should run it), bundled scripts, and its own docs and tests. Claude loads
a skill when a task matches its description.

This repo is also a **Claude Code plugin marketplace** — see
[Installing](#installing) and, for lab members, [LAB-ONBOARDING.md](LAB-ONBOARDING.md).

## Installing

**For your whole lab (recommended)** — install the plugin bundle once; updates
arrive with `git pull` / a marketplace refresh:

```
/plugin marketplace add https://github.com/RaredonLab/skills
/plugin install lab-skills@raredon-lab
```

Then start a new session and just describe the task (skills auto-trigger by their
description) — e.g. *"check and tabulate the references in Manuscript.docx."*
Full step-by-step, including for non-technical users, is in
[LAB-ONBOARDING.md](LAB-ONBOARDING.md).

**Personal (single machine, editable)** — symlink a skill into your user skills
folder so it's live everywhere and tracks your local edits:

```
mkdir -p ~/.claude/skills
ln -s "$PWD/skills/reference-check" ~/.claude/skills/reference-check
```

## Skills

| skill | what it does | status |
|-------|--------------|--------|
| [`reference-check`](skills/reference-check/) | Extract, verify (DOI/PMID/URL), and tabulate the references in a document; build a per-citation audit table + a per-reference library in five manager formats; judge whether each reference supports the sentence citing it. | v0.3.0 (Word .docx; LaTeX/PDF planned) |

## Planned skill domains

This repo is meant to grow into a lab toolkit spanning the scientific workflow:

- **Writing** — manuscripts, structure, clarity, journal formatting.
- **Referencing** — `reference-check` (citations, bibliographies, libraries).
- **Data visualization** — figures, plots, publication-ready graphics.
- **Computational work** — analysis pipelines, reproducible code, notebooks.
- **Experimental design** — power/sample size, controls, protocols.
- **Funding research** — finding relevant opportunities (NIH, foundations).
- **Grantsmanship** — aims pages, review-aware structure, budgets.
- **Wet/dry lab tasks** — assorted bench and computational chores.

## Conventions

New skills follow the patterns documented in [CLAUDE.md](CLAUDE.md): hybrid
design (deterministic scripts + model judgment), standard-library-first Python
with pinned dependencies, dependency-free tests any lab member can run, free
and keyless APIs, and run artifacts kept out of git.

## Repository layout

```
skills-msbr/
  README.md            ← this file
  CLAUDE.md            ← working notes for Claude in this repo
  LAB-ONBOARDING.md    ← hand-to-a-labmate install + usage guide
  .claude-plugin/
    marketplace.json   ← makes this repo an installable marketplace
    plugin.json        ← the "raredon-lab" plugin bundling all skills
  skills/
    <skill-name>/
      SKILL.md         ← skill definition (name + description + workflow)
      CLAUDE.md        ← skill-specific working notes
      README.md        ← human-facing usage
      scripts/         ← bundled code
      standards/       ← editable lab standards the skill follows
      references/      ← reference notes for the skill
      tests/           ← standalone tests
```

## Sharing

Work is committed to `dev`, pushed, and periodically proposed to the upstream
lab fork via pull request. Nothing is pushed or PR'd automatically — those are
deliberate steps.
