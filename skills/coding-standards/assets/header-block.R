# ============================================================
# Title: NN_YYYYMMDD_AB_descriptive-name.R
# Author: Author Name (AB)
# Date: YYYY-MM-DD
# Purpose: <plain-language description of the one operation this
#          script performs, and on what data>
# ------------------------------------------------------------
# Inputs:
#   /abs/path/to/input.rds
# Outputs:
#   /abs/path/to/output.rds
#   figures/NN_YYYYMMDD_AB_name.pdf
# ============================================================

# ── Libraries ────────────────────────────────────────────────
library(PackageA)
library(PackageB)

# ── Source helper functions ──────────────────────────────────
source("functions/helpers_qc.R")
source("functions/helpers_viz.R")

# ── File paths ───────────────────────────────────────────────
path_input  <- "/abs/path/to/input.rds"
path_output <- "/abs/path/to/output.rds"
path_figs   <- "figures/"

# ── Load and inspect data ────────────────────────────────────
obj <- readRDS(path_input)
dim(obj)

# ── <Operation> ──────────────────────────────────────────────
# ...analysis, using named variables/args (no hardcoded values)...

# ── Save output ──────────────────────────────────────────────
saveRDS(obj, path_output)
