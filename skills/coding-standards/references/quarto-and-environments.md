# Quarto narration & environments (reference)

The lab's narrated-analysis and reproducible-environment conventions. Quarto is the
cross-language default (renders both R and Python); `renv` (R) and `uv` (Python)
pin environments. Distilled from Manual Ch. 04; extended to Python per lab decision.

## When to narrate
Script first, narrate second. A narrated doc is a *guided tour* of an analysis that
already exists as a script — prose + code + figures on one page for a reader who
wants to understand what was done and why. It does not replace the script.

## Quarto document standard (`.qmd`)
Prefer `.qmd` over `.Rmd`/notebooks: it renders R and Python, diffs cleanly as
text, and produces the same `docs/*.html` vignette. Apply the file-naming standard
and commit the rendered HTML to `docs/`.

**YAML header:**
```yaml
---
title: "01 — EDA Overview: <dataset>"
author: "Author Name (AB)"
date: "2025-03-15"
format:
  html:
    toc: true
    toc-float: true
    code-fold: true
    theme: flatly
---
```

**Global setup chunk** (suppress noise; keep meaningful output visible):
```r
#| label: setup
#| include: false
knitr::opts_chunk$set(echo = TRUE, warning = FALSE, message = FALSE,
                      fig.width = 8, fig.height = 6)
```
Python engine equivalent: set warnings/logging quiet in the first cell.

**Named chunks/cells:** lowercase, hyphenated, descriptive — `load-data`,
`qc-filtering`, `umap-plot`, `export-table`. Named chunks give better knit errors,
a navigable outline, and selective caching.

**Keep HTML in sync:** if you change the source materially, re-render and re-commit
the HTML. A `docs/` that lags its source is worse than none.

## Environments

### R — `renv`
Initialize per repo (`renv::init()`), snapshot after adding packages
(`renv::snapshot()`), commit `renv.lock`. Restore on a new machine with
`renv::restore()`.

### Python — `uv`
- Init: `uv init` (creates `pyproject.toml`); add deps with `uv add <pkg>`
  (writes `uv.lock`). Commit `pyproject.toml` + `uv.lock`.
- Run scripts in the environment: `uv run python scripts/01_..._preprocessing.py`.
- Reproduce elsewhere: `uv sync`.
- Pin the interpreter with `.python-version` if the project needs a specific one.

Both lockfiles are committed; the `data/` and `output/` dirs are not (see the
`github-standards` `.gitignore`).

## Packages (pointer)
R: `usethis`/`devtools` scaffolding, Roxygen docs, `pkgdown` site, `NEWS.md`,
pass `R CMD check` clean. Python: `pyproject.toml`, `pytest`, `mkdocs`,
`CHANGELOG.md`. AI-assisted scaffolding is encouraged for the boilerplate; the
science and the tests are human-owned.
