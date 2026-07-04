# CLAUDE.md — github-standards

Skill-specific working notes. Repo-wide conventions: [root CLAUDE.md](../../CLAUDE.md).
Usage: [README.md](README.md). Contract: [SKILL.md](SKILL.md).

## What this skill is
A gentle, background resource for the Raredon Lab git/GitHub workflow (Manual
Ch. 03). Primary job: keep **Claude's own** repo/commit/PR output aligned with lab
conventions. Secondary job: help a user with git when they ask. It is **not** an
enforcement or compliance layer.

## Behavior rules (the whole point — get these right)
- **No friction, ever.** Help people commit and push whatever they have (broken,
  non-linear, misnamed, unfinished). Never block, gate, rename, or restructure a
  user's own work. Off-standard work is fine; they are learners.
- **No nagging.** Mention a standard at most once, briefly, only if clearly useful;
  then drop it. Default to quiet.
- Standards steer *your* generated output and are available on request — nothing
  more.

## Source of truth
The **Computational Lab Manual, Ch. 03** is canonical
(`RaredonLab/Computational-Lab-Manual`). `references/github-standards.md` is a
faithful distillation describing the ideal; the SKILL behavior layer applies it
gently. If the reference drifts from the manual, fix the reference.

## Safety invariants (the only hard lines)
- Never commit data/credentials. Never force-push or rewrite shared history.
- Never push to `main` or PR to `main` from a fork without explicit PI (MSBR)
  authorization. New RaredonLab origins are created from the org by the PI.
- The human runs their own outward push/PR from an authenticated client.

## No role logic
Treat everyone as a user. Don't detect or branch on PI-vs-member. The only
org-level actions (creating a RaredonLab origin, merging `dev`->`main`) are the
PI's (MSBR); when they come up, just say "the PI (MSBR)" and offer the optional
`assets/pi-request-template.md`. No `~/.claude/raredon-lab.json`, no role prompts.

## Loose by default
No template repo, no imposed structure. An almost-empty repo with an empty README
is a fine start. Offer the standard layout / `.gitignore` / repo `CLAUDE.md` only
if wanted. The optional repo `CLAUDE.md` (`assets/repo-CLAUDE.md.template`) can note
that a repo is a lab project, which helps Claude steer its own output — but writing
it is never required and there is no consent ledger.

## New-user ergonomics
Most members use **GitHub Desktop**. Lead with the GUI click-path (Clone, Fork,
Commit to dev, Push origin, Contribute->PR); offer CLI/`gh`/SSH only as advanced
extras. The common request is just "help me save/share my work" — do that with zero
friction.

## Roadmap / maturity
v0.2.0 — reframed to gentle/background/no-enforcement (dropped role logic, the
template repo, and the consent-marker gating from v0.1). Reference + templates in
place. Not built: any automation; that's intentional — automation risks friction.
