# Certified seat–safety frontiers (project root)

Research code + manuscript for *Certified Seat–Safety Frontiers for U.S. House Districting* (paper/main.tex).

## Layout
- `src/gf/` — library: `data` (VEST+TIGER instances), `core` (regime, exact-integer safety coefficients, INDEPENDENT verifier),
  `hier` (cell hierarchy, Ward clustering), `agg` (aggregated relaxation + CEGAR), `search` (county-aware ReCom LB),
  `lns` (exact LNS), `frontier` (spectrum brackets), `relax_milp` (independent HiGHS encoding for audits), `baseline`, `analysis`.
- `scripts/` — `run_jobs.py` (parallel frontier jobs), `ablation_nobudget.py`, `resolution_ladder.py`, `audit_infeasible.py`,
  `verify_all_plans.py`, `summarize.py`, `make_tables.py`, `make_figs.py`.
- `tests/` — `test_agg.py` (CEGAR vs brute-force enumeration on random toy graphs: validity, monotone refinement, exact convergence),
  `test_milp_audit.py` (CP-SAT vs HiGHS agreement), `toys.py`.
- `data/raw` (downloads), `data/proc` (instances), `runs/<tag>/` (JSON brackets + plan npz), `paper/`, `LOG.md` (append-only research/QA log).
- `continuation/`, `prior_audit/`, `code/` — the original planning package (kept unchanged).

## Manuscript
`paper/main.pdf` (25 pages; source `paper/main.tex` + `sec_*.tex`, `results_*.tex`, `refs.bib`, generated `tables/` and `figs/`).
Rebuild tables and figures from `runs/` with `python scripts/make_tables.py` and `python scripts/make_figs.py all`.

## Data sources (not committed: `data/raw`, about 2.4 GB; `python -m gf.data ...` downloads them)
- VEST 2020 precinct election results + boundaries, Harvard Dataverse (Voting and Election Science Team, 2021), file ids resolved by `gf.data` via
  `https://dataverse.harvard.edu/api/access/datafile/<id>` (dataset "2020 Precinct-Level Election Results").
- 2020 Census block geometries and populations (TIGER/Line TABBLOCK20), one file per state:
  `https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_<stateFIPS>_tabblock20.zip`.
- `data/proc/` holds the processed per-state instances derived from these public sources, so the solvers can be run without the downloads.

## Scope and honest limits
Certified brackets for 16 states with 2 to 5 districts, both parties, 2020 precincts, +-1% population, at most k-1 county splits.
k >= 3 brackets stay 2-3 points wide near hard thresholds; the unconstrained (no split budget) regime is not certified; plans that split
precincts are outside the model; k >= 6 states and Hawaii were not run. The frontier is a capacity statement: symmetric in the parties,
not a forecast, no legal claim. See the manuscript, Section "Discussion and limitations", and `LOG.md`.

## Reproduce
```bash
pip install numpy scipy pandas geopandas shapely pyogrio networkx ortools highspy matplotlib
# data: python -m gf.data NH ME RI ID MT WV NE NM AR IA KS MS NV UT CT OK   (needs curl; downloads VEST 2020 + TIGER blocks)
PYTHONPATH=src python tests/test_agg.py 8           # brute-force validation (expects: bad 0)
PYTHONPATH=src python scripts/run_jobs.py main 2 5 120 k-1 NH ME RI ID WV MT NE NM IA MS NV CT UT AR OK KS
python scripts/verify_all_plans.py main             # re-verify every stored witness plan
python scripts/audit_infeasible.py main 40 1        # cross-solver audit of infeasibility proofs
cd paper && tectonic main.tex
```
Environment used: Python 3.12, ortools 9.15 (CP-SAT), highspy 1.14, 12 cores. Certificates are exact-integer CP-SAT proofs;
lower bounds are plans re-verified by `core.verify_plan` (no shared code with solvers).
