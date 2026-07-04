---
name: github-standards
version: 0.2.0
description: >-
  Help with version control for Raredon Lab computational projects and, when
  generating repo setup / commits / PRs yourself, align with the lab's git
  workflow (RaredonLab origin main+dev -> personal fork -> local; PR to dev,
  not main; standard .gitignore and layout; NN_YYYYMMDD_AB naming). Use when a
  user asks for help starting, structuring, forking, cloning, committing, or
  opening a PR on a lab project in any language, or asks about the lab git
  workflow. Gentle and optional: help people commit and push whatever they have
  without friction; never enforce structure, naming, or standards on their own
  work. Pairs with coding-standards.
---

# github-standards

A background resource for the Raredon Lab git/GitHub workflow (Computational Lab
Manual, Ch. 03 — the **manual is the source of truth**). Two jobs, in priority
order:

1. **Steer your own output.** When *you* (Claude) set up a repo, write a commit,
   open a PR, or scaffold structure for lab work, follow the lab conventions below
   by default, so what you produce is already aligned.
2. **Help when asked.** If a user wants the lab setup ("get this repo going the
   lab way," "help me commit and open a PR," "what's the fork workflow?"), apply
   `references/github-standards.md`.

## How this skill behaves — gentle, no friction

This is the important part. Many lab members are new to Git and to coding.

- **Never enforce, gate, or police.** Help people commit and push whatever they
  have — even if it's broken, non-linear, misnamed, or unfinished. Getting work
  into version control is the win; polish is optional and comes later.
- **Never correct or restructure a user's own work** unless they ask. If someone
  writes or requests something off-standard, that is fine — let it happen. They
  are learners; curiosity comes first.
- **No nagging.** You may mention a relevant standard once, briefly, only if it is
  clearly useful in the moment, then drop it. Default to staying quiet and just
  helping. Almost background.
- **Available, not imposed.** The standards are here to help if wanted and to keep
  *your* generated output consistent — not to constrain anyone's workflow.

## The common case: help someone commit and push
Most requests are simply "help me save/share my work." Do that with zero friction,
GitHub Desktop first (Commit to dev -> Push origin), CLI if they prefer. If you are
composing the commit message, make it specific (what changed + why); if they wrote
their own, leave it. Don't require naming or structure to help them commit.

## The lab workflow (apply when setting up, or when asked)
Keep it loose — an almost-empty repo with an empty README is a perfectly good
start. When it helps:

- **Fork model:** RaredonLab origin (`main`+`dev`) -> personal fork `<repo>-AB`
  (`dev`) -> local clone. Push to your fork; PR to origin `dev`.
- **`main` is the PI's** (MSBR): merging `dev`->`main` and creating new RaredonLab
  origins happen from the RaredonLab org, by the PI. Anyone who wants a lab-org
  repo can just ask the PI — there's an optional draft in
  `assets/pi-request-template.md`. Working in a personal repo first is also fine.
- **Structure / `.gitignore` / repo `CLAUDE.md`:** offer the standard layout and
  the `.gitignore` templates (`assets/`) if someone wants them; don't impose them.
- **Naming:** `NN_YYYYMMDD_AB_descriptive-name.ext` when *you* create files;
  suggest it only if asked.

## Guardrails (safety only, not process)
- Never commit credentials/data. If a secret was committed, tell the user to notify
  the PI and rotate the key.
- Don't force-push, rewrite shared history, or push to `main` without explicit PI
  authorization.
- The user runs their own `push`/PR from their authenticated GitHub Desktop/terminal.

## References
- `references/github-standards.md` — the full lab workflow + templates.
- `assets/` — `.gitignore` (R + Python), standard structure, an optional repo
  `CLAUDE.md`, an optional PI repo-request draft.
- Source of truth: Raredon Lab Computational Manual, Ch. 03.
