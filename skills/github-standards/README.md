# github-standards

**Version 0.2.0**

Set up and run version control for Raredon Lab computational projects the lab way —
so your work is versioned, reviewable, reproducible, and survives you. Built to be
frictionless for new users on **GitHub Desktop**, and useful in any language.

It applies the Computational Lab Manual, Ch. 03 (the **manual is the source of
truth**; this skill just makes it easy to follow).

## What it does

- **Initializes or structures a repo** to the lab standard: the `functions/ scripts/
  markdowns/ docs/ figures/ output/ data/` layout, the standard `.gitignore`
  (R and Python), a `README.md`, and a root `CLAUDE.md`.
- **Sets up the fork model:** RaredonLab origin (`main`+`dev`) -> your personal fork
  `repo-AB` (`dev`) -> local clone, with `origin`/`upstream` remotes wired.
- **Helps you commit and push** whatever you have — even broken, unfinished, or
  non-linear work. Getting it into version control is the win.
- **Knows the daily loop:** commit -> push to your fork -> pull request to origin
  `dev` (never `main`), if and when you want it.
- New RaredonLab org repos are created by the PI (MSBR); it can draft that request
  for you, or help you work in a personal repo first — whatever you prefer.

## How you use it

Just describe what you're doing — *"help me commit and push this,"* *"start a repo
for X,"* *"what's the fork workflow?"* It helps with that, and nothing more.

## Gentle by design

- **No enforcement, no friction.** It never blocks a commit, renames your files, or
  restructures your work. Off-standard, messy, or exploratory work is fine — you're
  learning, and momentum matters more than polish.
- It mostly works in the background, keeping *Claude's own* repo/commit output
  aligned with lab conventions; it only speaks up if you ask or it's clearly useful.
- Safety only: it won't commit credentials/data, force-push, rewrite shared history,
  or touch `main` without PI sign-off. You run your own `push`/PR from your
  authenticated GitHub Desktop/terminal.

## Files

- `references/github-standards.md` — the full lab standard.
- `assets/` — `.gitignore` templates (R, Python), the per-repo `CLAUDE.md`
  template with the standards marker, and a PI repo-request template.

## Pairs with

The **coding-standards** skill (how the code inside the repo is written).
