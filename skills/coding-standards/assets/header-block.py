# ============================================================
# Title: NN_YYYYMMDD_AB_descriptive-name.py
# Author: Author Name (AB)
# Date: YYYY-MM-DD
# Purpose: <plain-language description of the one operation this
#          script performs, and on what data>
# ------------------------------------------------------------
# Inputs:
#   /abs/path/to/input.parquet
# Outputs:
#   /abs/path/to/output.parquet
#   figures/NN_YYYYMMDD_AB_name.pdf
# ============================================================

# ── Libraries ────────────────────────────────────────────────
import pandas as pd

# ── Import helper functions ──────────────────────────────────
from functions.helpers_qc import filter_by_qc

# ── File paths ───────────────────────────────────────────────
path_input = "/abs/path/to/input.parquet"
path_output = "/abs/path/to/output.parquet"
path_figs = "figures/"

# ── Load and inspect data ────────────────────────────────────
df = pd.read_parquet(path_input)
print(df.shape)

# ── <Operation> ──────────────────────────────────────────────
# ...analysis, using named variables/args (no hardcoded values)...

# ── Save output ──────────────────────────────────────────────
df.to_parquet(path_output)
