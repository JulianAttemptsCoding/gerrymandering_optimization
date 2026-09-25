# Research / QA log (append-only, newest last)

## 2026-09-24 — session start
- Read `continuation/` package (AHGOR plan). Env: Python 3.12, HiGHS, CP-SAT (ortools 9.15), SCIP (pyscipopt 6.2), 12 cores, 16 GB, no Gurobi, no R.
- Data pipeline: VEST 2020 precincts (Harvard Dataverse doi:10.7910/DVN/K7760H) + TIGER/Line 2020 tabblock20 POP20 (block internal point -> precinct polygon).
  NH check: pop 1,377,529 = Census; Biden/Trump 424,937/365,660 = certified. 15 further states built, state pop asserts all pass.
- Prior-art check: Fravel et al. (MMOR 2026, arXiv 2305.17298) = COUNTY-level whole-county restriction, eps=10%, k<=7, probit representation objectives; not a fine-resolution valid outer relaxation. Novelty boundary in NOVELTY_PRIOR_ART.md stands.

## Finding 1 (kill-criterion test of original AHGOR design) — NEGATIVE
- Quotient-support connectivity coarsening (cells = counties -> 226/321 atoms) does NOT tighten: NH, D, k=2, eps=1%, one safe district:
  sigma*(1) upper bound stays 0.125 at every refinement level (10..145 cells), best witness (ReCom short-burst) 0.0725. Geography-free hull bound = 0.125 too.
- Exact atomic solves (CP-SAT parent-pointer, SCIP flow, HiGHS lazy cuts) all time out at n=321, k=2, even eps=25%. LP with vertex-separator / directed cuts converges very slowly.
- => Original claim "coarse-to-fine hierarchy closes gaps at realistic resolution" FAILS for the unconstrained core regime (population + contiguity only).

## Finding 2 — POSITIVE (new design)
- Add a subdivision budget: at most s counties split (regime rho_s). Coarse county-level relaxation with local hull (fractional-knapsack tangents, exact-integer) + quotient connectivity becomes tight, and CEGAR (refine only split multi-atom cells) terminates with exact atomic answers.
- NH D k=2 eps=1%: s=1: sigma*(1) in [0.0701,0.075), sigma*(2) in [0.0353,0.040). s=2 near threshold (m=0.09) times out at ~100 cells -> difficulty grows with s.

## QA events (bugs caught by tests)
1. Symmetry-breaking `rootexpr[a] < rootexpr[b]` wrongly strict for coarse cells (two districts can share a root cell) -> false 'infeasible'. Fixed to <=. Caught by brute-force test_agg.py.
2. Envelope cache keyed only by node id but envelopes depend on (party,m,contests) -> false 'exact' plan with margin below m. Caught by the independent verifier assertion. Fixed (regime-keyed cache).
3. python-requests is 403-blocked by Harvard Dataverse (use curl).
- Toy gates (tests/test_agg.py): validity U>=F, monotone refinement, exact convergence at atomic partition, CEGAR == brute force: 54/54 pass (with county-split caps).

## 2026-09-25 — engineering findings
- DATA BUG caught: VEST county column is `COUNTYFP` (not `COUNTYFP20`) in 11 states -> county was all-zero, cap regime vacuous. Fixed: county = population-plurality TIGER block county (authoritative); precincts without blocks fall back to VEST/nearest. All results before the fix discarded.
- CEGAR speedups (NH benchmarks): Ward homogeneity hierarchy (-3x), refine depth 3 (-2..10x), plan-completion primal heuristic (freeze whole cells, expand split cells to atoms; 37s->1s), CP-SAT restarts (heavy-tailed runtimes).
- Pool-first relaxation (q explicit safe districts + 1 aggregate rest): no gain for k=2, kept only for k>=4.
- Pairwise min-vertex-separator clauses (redundant strengthening) : NO gain on WV root instance (still unknown at 120s).
- Boundary-rooted (port-connected) local hull (exact small CP-SAT per cell): only 0-5% tighter than fractional knapsack on NH counties -> NOT integrated (negative result).
- CP-SAT native crash ("Check failed: heuristics.fixed_search != nullptr") when `repair_hint=True` -> removed; job runner now one OS process per job with retries.
- County-aware ReCom (spanning tree with intra-county edges cheap; hard cap on split counties) constructs cap-feasible plans in ms and hill-climbs to strong incumbents; CP-SAT could not even find a q=0 plan for NE (k=3,s=2) in 300s. => primal side = county-aware ReCom, proof side = CEGAR.
- Near-threshold queries (mid-gap between incumbent and proven-infeasible margin) time out at k>=3; unknown widths reported honestly.
- Cross-solver audit (tests/test_milp_audit.py, CP-SAT vs HiGHS MILP, toy grids, caps None/1/2, all q, partitions): first run exposed a bug in the AUDIT tool (split counted as sum(d_K-1) instead of #counties with d_K>=2); after fix 495/495 agree, 0 disagreements.

## 2026-09-25 (later) — definition fix + QA
- Definition change: split budget = sum_K (d_K-1) (Shahmizad & Buchanan convention). Diagnosis: with #split-counties, Douglas County (NE, 584k) could be cut 3 ways for one split; relaxations stayed loose and CEGAR root solves timed out. All k>=3 runs redone; k=2 results unaffected (identical definitions). Brute-force regression (72 configs) and CP-SAT/HiGHS audit re-run after change.
- Literature check: Shahmizad-Buchanan text confirms 'k-1 county splits' folklore and d-1 counting. Duchin et al. 2019 (ELJ) = geography-free sorting bound => our geography-free baseline is prior art (cited as such). Fixed short-bursts authorship in refs.bib (Cannon, Goldbloom-Helzner, Gupta, Matthews, Suwal).
- Party-swap symmetry test (NH, k=2): swapped-instance brackets equal original opposite-party brackets ((0.0702,0.075) identical; q=2 (0.0374 vs 0.0375, <0.04)). PASS.
- Cross-run consistency (analysis.consistency_check, main + main_v1, 40 (state,party,q) keys): 0 violations (every verified LB < every proven UB).
- Data QA: atoms with votes>pop hold <0.7% of votes in every state; zero-pop atoms are almost all vote-free.
- Diagnostics negative results: pairwise separator clauses / linear separators / linearization levels do not speed up root solves (NE q=2 root unknown at 60-90s); root hardness is inherent to connectivity+pop+cap skeleton search for k>=3.
- Safe-first decomposition (pool relaxation refined until safe districts exact, then complete rest with safe districts pinned; agg.cegar_safe_first): NOT better. IA R q=1 m=0.19 (just above ReCom LB 0.1874) still unknown after 240s at 255 cells. Kept in code, not used in pipeline. Near-threshold hardness = exact geometry of the safe district boundary, not the completion of the rest.

## 2026-09-25 (morning) — full main run complete
- Runs: main (k=2..5, 16 states x 2 parties, s=k-1, eps=1%, PRE) two-tier: pass 1 (ReCom LB + LNS + CEGAR bisection), lbboost (many-seed ReCom), esc (partial), ubsweep (cheap pool-relaxation upper-bound sweep), geofree (geography-free hull bound merged as extra upper bound). Bracket merge = max verified LB, min proven UB.
- Headline: at thresholds 50/55/60% 79/96 F values exact (36/36 for k=2); 80% of 992 (state,party,threshold) values exact on a 1-pt grid. Spectrum bracket widths: k=2 median 0.01 pt (21/24 <=0.5), k=3..5 median 2.2-2.6 pt.
- Ablation (79 nontrivial state/party/q): quotient (county or refined) never tighter than geography-free (median +0.3, max +0.8 pt); budgeted certified UB tighter than geography-free by >0.05pt in 55/78 (median 0.65; q=1 median 2.75, max 13.7).
- ReCom (no budget) incumbent >= certified UB only for ME D q=1 (63.3 vs <63.0): certified price of county integrity >= 0.3 pt.
- Audits: real-data CP-SAT vs HiGHS 33 agree / 0 disagree / 3 not reproduced (36 sampled proofs); toy CP-SAT vs HiGHS 495+ agree; brute force 72 configs pass; pool/safe-first/ReCom validity toy 22 checks pass; NH party swap consistent; cross-run consistency 104 keys 0 violations.
- Negative/unhelpful ideas logged: escalation with 4x time barely moves near-threshold unknowns; safe-first decomposition; port-connected hull; pair separator clauses.

## 2026-09-25 (afternoon) — manuscript QA pass
- Full-text read of compiled paper (25 pp). Fixed: broken cross-ref in Data section (stray CR ate the backslash of \ref{sec:frontier}); robust-table wording (5 of 6 two-district states; Montana omitted because tolerance variants not run and main brackets open); intro "ten points" -> "nearly ten points" (ME D 62.7-63.0 -> 53.2-53.5); coverage note (6 single-district states trivial, 27 states k>=6 not attempted, HI excluded).
- Numbers re-checked against tables/runs: 104 brackets / 44 tight; 79/96 F exact (36 + 43); 21/24 k=2; medians 2.23/2.62/2.21; audit 103 agree / 0 disagree / 13 unreproduced of 116 sampled; 429 verified plans, 0 failures. All match the text.
- Theorem/proposition/lemma counters left shared (single sequence; unambiguous).
- Recompiled clean: no unresolved refs; 25 pages.
