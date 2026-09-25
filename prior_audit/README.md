# Gerrymandering-extremes plan: full audit + best direction (2026-09-23)

## Start here
1. `AUDIT.md` — verdict, 14 severity-ranked findings, proofs, citation and currency audit, corrected novelty table.
2. `DIRECTION.md` — recommended research program (certified seat–safety frontier after *Callais*), ranked alternatives, gates, commands, failure modes, kill criteria.
3. `QC_LOG.md` — every research/QA/QC loop and what changed.
4. `SOURCES.md` — sources with direct links and verification status.
5. `code/` + `results/` — exact-enumeration toy evidence (reproducible, ~2 min).

## Key numbers from the toy QC (5×5 grid, 4006 plans, exact)
- Neutrality floor / integrality floor = 1.000, 1.0016, 1.000 across 3 ensembles.
- Envelope width identical across ensembles (ensemble-free).
- Asymmetry A: −0.035 / +0.022 / +0.006 (sign flips with ensemble choice).
- Near-zero-bias map (C = 0.098) at the 94.5th percentile of G.
- Certification: coarse bound 4 vs exact 2; one adaptive refinement → 2 (certified).

## Reproduce
```bash
cd code
pip install numpy scipy networkx      # scipy >= 1.9 for milp/HiGHS
bash run_all.sh                        # writes ../results/*.json and run_log.txt
```
