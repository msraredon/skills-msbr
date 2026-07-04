# Raredon Lab coding standard (reference)

Distilled from the Computational Lab Manual, Ch. 04–06. The manual is canonical.
Language-agnostic; R is primary, Python parity noted throughout.

> This describes the ideal to aim for. The skill applies it **gently**: it shapes
> Claude's own generated code and is here to teach if asked. It is never enforced
> on anyone's work — messy, exploratory, and off-standard code are all fine.

## Philosophy
The test for any code: *could someone not present when I wrote this reproduce my
results, understand my reasoning, and build on my work?* Exploration is normal and
messy; the standard describes what to reach by the time work is **shared or
committed as the record**. The gap between draft and standard is the polishing
step, not failure.

## Three categories of code
- **Scripts** (`.R` / `.py`) — the primary medium for doing analysis: load,
  transform, visualize, save.
- **Narrated docs** (`.qmd` / `.Rmd` -> `.html`) — teaching/communicating work
  already scripted.
- **Packages** — versioned, tested, documented tools for broad/long-term reuse.

Relationship: script an analysis -> narrate what you found -> extract the reusable
logic into functions and eventually a package.

## Scripts

### The header block (required, in this order)
1. **Title block:** filename, author + initials, date, plain-language purpose.
2. **Inputs / Outputs:** absolute paths to every file read and written.
3. **Libraries:** all imports grouped together.
4. **File-path variables:** a named variable for every input/output path.

A reader should open the script, read the header, and know what it operates on and
where results go before reading any analysis code. Declare paths at the top and
reference the variables throughout — this also makes the script trivial to adapt to
a new dataset/machine. See `assets/header-block.R` and `assets/header-block.py`.

### Scope and length
One coherent operation per script — one analysis stage, roughly one day of work to
reproduce. Length is fine; **sprawl** is the problem. A 500-line single pipeline is
well-scoped; a 500-line script that preprocesses + clusters + builds a figure +
exports a table is four scripts merged.

### Section dividers, comments
Use `# ── Named section ─────` dividers (RStudio/Positron render an outline).
Comment enough to retrace your thinking — what a step does, why a parameter was
chosen, where a decision was made. For polished/teaching scripts, err toward more.

### No hardcoding
Any numeric threshold, column name, string pattern, or path that could vary must be
a named variable or a function argument with a sensible default.

## Functions (`functions/`)
Write a helper when a block is **>~25 lines** or you'd copy logic across scripts.
Helpers keep scripts short and create shared, improvable infrastructure instead of
per-person silos.

- **Parameterize** everything that could vary; **`snake_case`**; return one object
  explicitly.
- **Document:** Roxygen (R) / docstrings (Python). Include purpose, `@param`/args,
  `@return`/returns.
- Keep each function focused on one task; two jobs -> two functions.

```r
#' Filter cells by QC metrics
#' @param obj A single-cell object.
#' @param min_features Minimum features per cell. Default 200.
#' @param max_mt_pct Maximum mitochondrial percentage. Default 20.
#' @return A filtered single-cell object.
#' @export
filter_by_qc <- function(obj, min_features = 200, max_features = 6000, max_mt_pct = 20) {
  keep <- obj$nFeature > min_features & obj$nFeature < max_features
  keep <- keep & obj$pct_mt < max_mt_pct
  return(obj[, keep])
}
```
Python parity: a module in `functions/` with typed args + a docstring and an
explicit `return`.

## Packages
Warranted when tools are broadly applicable or used across projects. R packages
follow CRAN standards (documented, built/checked/tested, docs site, `NEWS.md`, no
errors/warnings). Python: `pyproject.toml`, tests (pytest), a docs site,
`CHANGELOG.md`. AI-assisted scaffolding is encouraged for the boilerplate.

## Publication-ready code
Linear execution; load-from-disk -> operate -> save-to-disk; date-stamped outputs;
no redundant intermediates; every figure traceable to the code + data that made it.

## File naming
`NN_YYYYMMDD_AB_descriptive-name.ext` for scripts, docs, and **outputs** alike
(e.g. `02_20250308_NW_umap-celltype.pdf`, never `plot_final_v3.pdf`).

## R ↔ Python parity
| Concern | R (primary) | Python |
|---------|-------------|--------|
| Script | `.R` + header block | `.py` + header block (same fields, `#` comments) |
| Reusable logic | `functions/*.R`, Roxygen | `functions/*.py` module, docstrings |
| Narrated doc | `.Rmd` or `.qmd` -> `docs/*.html` | `.qmd` -> `docs/*.html` (Quarto, jupyter engine) |
| Environment | `renv` | `uv` (`pyproject.toml` + `uv.lock`) |
| Project file | `<name>.Rproj` | `pyproject.toml` |
| Package standard | CRAN (`R CMD check`, pkgdown, `NEWS.md`) | `pyproject`, pytest, mkdocs, `CHANGELOG.md` |
| Naming, header block, `functions/`, docs/, no-hardcode, save-to-disk | identical | identical |

Keep the science-facing conventions identical across languages; only the ecosystem
tooling differs.

## Data safety (light touch, but the default)
Write code against **described** data, produce runnable scripts that load/save from
disk locally. Do not require or assume access to real data. Don't police what the
user pastes, but default every workflow to the describe-then-generate pattern
(manual Ch. 05–06; Yale generative-AI policy: no moderate/high-risk data in AI
tools).
