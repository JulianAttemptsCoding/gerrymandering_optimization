# Certified Gerrymanderability — continuation package

**Date:** 2026-09-23  
**Status:** authoritative research direction after re-auditing the uploaded `gerrymandering_audit_and_direction.zip` and checking 2025–2026 prior art.

## One-sentence project

Develop **provable lower and upper bounds on the U.S. House seat–safety frontier** under explicitly encoded districting constraints, using constructive map search for lower bounds and an **adaptive hierarchical geographic outer relaxation** for upper bounds that is valid at every level and converges to the atomic optimization problem under full refinement.

## Why this direction survives the novelty audit

The following are *not* sufficient novelty claims anymore:

- a new scalar gerrymandering score;
- the feasible min/max number of seats;
- heuristic “most gerrymandered” maps;
- a single safe-seat optimization at 51% or 55%;
- a generic multilevel districting algorithm;
- durability under electoral swings by itself.

Recent work already covers substantial parts of those spaces. The strongest remaining candidate contribution is the combination of:

1. a **full safety-margin frontier / seat–safety spectrum** rather than one threshold;
2. **certificates**: every reported extremum is bracketed between a feasible-map lower bound and a mathematically valid upper bound;
3. a **coarse-to-fine outer-relaxation hierarchy** that never falsely excludes a real atomic map and has a finite-convergence theorem;
4. **local attribute-allocation cuts** (fractional-knapsack / support-function envelopes) that tighten coarse geographic cells without sacrificing validity;
5. a symmetric U.S. House application, with all assumptions and constraint regimes stated explicitly.

The package deliberately does **not** recommend maps or political outcomes. It studies the mathematical capacity of district boundaries under symmetric objectives.

## Files

- `AUTHORITATIVE_STATE.md` — current project state and decisions.
- `ALL_THOUGHTS.md` — exhaustive shareable research log: ideas considered, rejected, retained, mathematical reasons, novelty caveats, and open problems.
- `MATH_SPEC.md` — formal definitions, MILP, theorem statements, proof sketches, and relaxation construction.
- `NOVELTY_PRIOR_ART.md` — exact novelty boundary against the main adjacent literature.
- `PAPER_BLUEPRINT.md` — proposed paper story, theorem/result structure, figures, tables, and contribution threshold.
- `IMPLEMENTATION_PLAN.md` — data, software, algorithm, validation, compute order, and reproducibility contract.
- `QC_AND_KILL_CRITERIA.md` — gates that can falsify or downgrade the project before large-scale compute.
- `SOURCES_VERIFIED_2026-09-23.md` — current sources re-checked for this continuation.
- `QC_RECHECK_2026-09-23.md` — re-run of the uploaded toy audit and extra mathematical QA.
- `../prior_audit/` — the uploaded audit package, preserved unchanged except for extraction.
- `../code/frontier_math_sanity.py` — dependency-free checks of the frontier/spectrum identities.

## Recommended next action

Do **not** scale nationally yet. Implement one exact/relaxed pilot on a small real state, with the same atomic data and constraints used by both lower- and upper-bound solvers. The first go/no-go result is whether the certified gap can close at several safety thresholds on a real instance.

## Naming

Working paper title:

> **Certified Gerrymanderability: Adaptive Geographic Relaxations for the U.S. House Seat–Safety Frontier**

Alternative:

> **Provable Limits of Partisan Redistricting: Certified Seat–Safety Frontiers for U.S. House Maps**

The word “gerrymanderability” should be treated as a descriptive mathematical term, not a legal conclusion.
