# Novelty and prior-art boundary — checked through 2026-09-23

## Algorithmic Redistricting Atlas (2026)
Current Atlas methodology includes short-burst optimization maps:
- Max: maximize seats with at least 51% under 2024 presidential vote;
- Safe Max: at least 55%;
- short bursts explicitly do not guarantee global extrema.

**Therefore:** heuristic U.S. House extreme maps at one/two thresholds are not novel.

## Fairmandering — Gurnee & Shmoys (2021)
Column-generation heuristic, flexible fairness objectives, large feasible expected-outcome ranges.

**Therefore:** fairness optimization and broad feasible seat ranges are not novel.

## Swamy, King & Jacobson — Operations Research
Scalable multilevel multiobjective redistricting; approximate Pareto front; fairness objectives.

**Therefore:** “multilevel districting” alone is not novel.

## Validi, Buchanan & Lykhovyd — exact contiguity
Exact contiguity formulations and branch-and-cut are established.

**Therefore:** reuse exact connectivity; do not claim it.

## Fravel et al. (2026) — closest methodological neighbor
*Optimizing representation in redistricting: dual bounds for partitioning problems with non-convex objectives.*

They develop dual/optimization bounds for representation objectives and demonstrate on county-level districting test beds.

**Threat:** generic “provable bounds for redistricting” is already prior art.

**Candidate differentiation:**
- partisan seat-safety frontier;
- adaptive geographic outer hierarchy;
- fine geographic application;
- local fractional-knapsack / attribute-hull cuts;
- explicit whole-frontier certificate gaps.

This paper must be read in full before a submission novelty claim is frozen.

## Jolly & Buchanan (2026)
Current guide warns that several fast contiguity formulations are inexact because they can exclude valid connected solutions.

**Therefore:** final certificate model must use valid outer/necessary connectivity and exact leaf contiguity.

## Palmer & Schneer (2026)
Durable majority gerrymanders under electoral uncertainty.

**Therefore:** durability by itself is not novel.

## FAccT France (2025)
Studies diversity/extrema of legal redistricting maps as gerrymandering potential.

**Therefore:** min/max seats or “gerrymanderability range” is not novel.

## McCartan et al. APSR (2026)
Models institutional redistricting “leeway” as a game-theoretic score.

**Therefore:** do not conflate institutional leeway with our geometric feasible-set extremum.

## ALARM 50-state simulations
5,000 alternative plans and state-specific workflows are mature infrastructure.

**Therefore:** ensemble generation is not a contribution here.

# Candidate novelty statement

> We introduce a seat–safety frontier and a certifying adaptive geographic relaxation for extremal U.S. House redistricting. Constructive maps provide lower bounds, while a hierarchy of valid coarse outer models provides monotone upper bounds that converge to the exact atomic problem under refinement. This yields explicit certificate gaps for an entire partisan safety spectrum.

Any “first” language remains provisional until the final literature audit.

# Claims to avoid

- no one has optimized gerrymandering;
- no one has generated extreme maps;
- no one has used multilevel redistricting;
- no one has derived redistricting upper bounds;
- first gerrymanderability measure;
- computational feasibility = legal validity;
- extremal capacity = evidence of intent.
