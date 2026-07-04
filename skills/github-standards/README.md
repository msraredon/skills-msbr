# github-standards

**Version 0.1.0**

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
- **Drives the daily loop:** commit -> push to your fork -> pull request to origin
  `dev` (never `main`), with lab-standard commit messages and PR rules.
- **Respects roles:** if you're the PI it can create the origin from the RaredonLab
  org; if you're a member it scaffolds locally and drafts a request for the PI to
  create the origin, then helps you fork.

## How you use it

Just describe what you're doing — *"start a new lab project for X,"* *"get this
repo set up the lab way,"* *"help me commit and open a PR."* The skill offers to
apply lab standards once and remembers your choice in the repo's `CLAUDE.md`. You
can always decline and work your own way.

## Consent & safety

- Standards are **offered, never forced**. Your choice is recorded per repo.
- It won't force-push, rewrite shared history, or touch `main` without PI sign-off.
- It never commits data or credentials (the `.gitignore` handles it).
- You run the actual `push`/PR from your own authenticated GitHub Desktop/terminal.

## Files

- `references/github-standards.md` — the full lab standard.
- `assets/` — `.gitignore` templates (R, Python), the per-repo `CLAUDE.md`
  template with the standards marker, and a PI repo-request template.

## Pairs with

The **coding-standards** skill (how the code inside the repo is written).
