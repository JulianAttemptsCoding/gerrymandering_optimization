# Authoritative project state — 2026-09-23

## Goal

Produce a genuinely novel, mathematically defensible, politically symmetric research paper about U.S. House redistricting.

The paper should contribute to optimization / mathematical political science rather than merely publish another map generator or another scalar fairness metric.

## Final research question

For a state with a fixed geographic/electoral data layer and an explicitly stated districting-constraint regime:

> **At each partisan safety margin, what is the maximum number of House districts that can simultaneously clear that margin, and how tightly can that maximum be certified?**

The method is run symmetrically for either major-party label. The research object is the feasible set and its extrema, not a recommendation about which maps should be enacted.

## Core object

For state \(s\), party label \(\pi\), constraint regime \(\rho\), finite electoral scenario set \(\Omega\), and safety margin \(m\ge 0\),

\[
F_{s,\pi,\rho,\Omega}(m)
=
\max_{M\in\mathcal M_s^\rho}
\#\left\{
j:
\min_{\omega\in\Omega}
v^\pi_j(M,\omega)
\ge \tfrac12+m
\right\}.
\]

This is the **seat–safety frontier**.

For a plan \(M\), define district robust margins

\[
r^\pi_j(M)
=
\min_{\omega\in\Omega}
\left(v^\pi_j(M,\omega)-\tfrac12\right),
\]

and let \(r^\pi_{(1)}(M)\ge\dots\ge r^\pi_{(k)}(M)\) be the sorted margins. Define

\[
\sigma^*_{s,\pi,\rho,\Omega}(q)
=
\max_{M\in\mathcal M_s^\rho}
r^\pi_{(q)}(M),
\qquad q=1,\dots,k.
\]

The vector
\[
\Sigma^*=(\sigma^*(1),\dots,\sigma^*(k))
\]
is the **seat–safety spectrum**.

The two descriptions are generalized inverses:

\[
F(m)=\max\{q:\sigma^*(q)\ge m\}.
\]

## What is mathematically new enough to pursue

The candidate main methodological contribution is an **Adaptive Hierarchical Geographic Outer Relaxation (AHGOR)**.

At every coarse resolution it gives an optimization problem whose feasible set contains the projection of every exact atomic map. Therefore its objective is a valid **upper bound** on the exact optimum. Refining selected geographic cells only tightens that upper bound. At singleton atomic cells, the model becomes the exact districting MILP.

Desired theorem chain:

1. **Embedding / validity theorem**  
   Every exact atomic feasible map embeds in every compatible coarse outer relaxation. Hence
   \[
   \mathrm{OPT}(m)\le U_{\mathcal P}(m).
   \]

2. **Monotone-refinement theorem**  
   If \(\mathcal P'\) refines \(\mathcal P\) and the child local relaxations project inside the parent local outer relaxation, then
   \[
   U_{\mathcal P'}(m)\le U_{\mathcal P}(m).
   \]

3. **Finite-convergence theorem**  
   If refinement terminates at singleton atomic cells and the leaf model uses exact assignment plus exact contiguity, then
   \[
   U_{\mathcal P_{\rm atom}}(m)=\mathrm{OPT}(m).
   \]

4. **Integer-certificate corollary**  
   If a constructed feasible map yields \(L(m)\) safe seats and the upper relaxation yields
   \[
   U(m)<L(m)+1,
   \]
   then, because the true objective is integer,
   \[
   L(m)=\mathrm{OPT}(m).
   \]

5. **Frontier/spectrum duality theorem**
   \[
   F(m)\ge q \iff \sigma^*(q)\ge m.
   \]

6. **Layer-cake identity**
   \[
   \int_0^{1/2}F(m)\,dm
   =
   \sum_{q=1}^{k}[\sigma^*(q)]_+.
   \]

The last identity is a structural summary; it should not be sold as a normative “fairness score.”

## Key tightening idea

For each coarse geographic cell \(C\), retain a valid outer description of all ways its atomic attributes can be distributed among districts.

A weak relaxation only conserves totals. A stronger relaxation adds **population-conditioned attribute envelopes**.

For nonnegative block attributes \((p_i,q_i)\), the vote/demographic mass that any one district can receive from a coarse cell satisfies

\[
\underline\phi_C(x)
\le q_{Cj}
\le \overline\phi_C(x),
\]

where \(\overline\phi_C\) is the fractional-knapsack upper envelope obtained by sorting \(q_i/p_i\) from high to low, and \(\underline\phi_C\) is the analogous lower envelope. Because whole-block subsets are contained in the fractional-knapsack relaxation, these inequalities are valid outer cuts.

This is one of the strongest candidate algorithmic contributions.

## Lower bounds

Constructive feasible maps provide lower bounds. Use an established redistricting search method first, e.g. merge-split / short-burst search with exactly the same encoded constraints.

The paper's claim is not that short bursts are new. Their role is to provide strong feasible incumbents \(L(m)\).

## What was rejected

### Rejected: ensemble-relative feasible-width as a new quantity
Subtracting an ensemble mean from both extrema cancels. The width is the ordinary feasible seat range.

### Rejected: the original “neutrality floor”
With hard winner-take-all seat counts it can be dominated by rounding/discreteness and is highly ensemble-dependent.

### Rejected: RMS distance from an ensemble mean as “partisan gerrymandering”
It mixes bias and responsiveness and does not cleanly isolate partisan direction.

### Rejected: “most/least gerrymandered map” as the headline
Heuristic seat-maximizing maps, fairness-optimized maps, and feasible seat ranges already have substantial prior art.

### Rejected: durability as the sole new idea
Palmer and Schneer (2026) directly develop durable majority gerrymanders under future electoral uncertainty.

### Demoted: a specific “Callais dividend”
The 2026 legal environment is moving, and a crude on/off VRA constraint is not a defensible legal model. If included at all, use generic, explicitly encoded **constraint-regime sensitivity** and avoid claiming that a computational regime equals a court's legal standard.

## Novelty boundary to defend

The defensible claim is narrower:

> Existing work has generated extreme maps, optimized fairness objectives, developed multilevel heuristics, and recently produced dual bounds for nonconvex representation objectives. The proposed contribution is a *certifying, adaptive geographic outer-relaxation hierarchy* for the entire partisan seat–safety frontier at much finer U.S. House geography, with constructive lower bounds, monotone upper bounds, finite convergence, and explicit certificate gaps.

This is a **candidate novelty claim**, not something to write as “first ever” until the final literature review is complete.

## Data architecture

Preferred geographic truth layer:
- 2020 Census P.L. 94-171 block population/demographics;
- TIGER/Line / P.L. 94-171 geometry and adjacency;
- state/VTD/precinct election totals from a reproducible source such as VEST / Redistricting Data Hub / a documented Atlas source.

Important measurement caveat:
- election returns are generally not observed at Census-block resolution;
- block-level electoral assignment is therefore model-based if blocks can split precincts;
- mathematical optimality must be stated **conditional on the electoral allocation model**, or a robust uncertainty formulation must be used.

## Computational architecture

- **R / `redist`**: constructive lower-bound search and ensemble diagnostics.
- **Python + Gurobi** preferred for the certifying MILP/branch-and-cut; SCIP is the principal open-source alternative.
- Exact contiguity: cut/separator or other exact formulation, not an inexact tree/DAG shortcut if the result is called a certificate.
- Hierarchical cell refinement: county/tract/block-group/custom connected clusters → eventually blocks where necessary.
- Independent verifier recomputes population, contiguity, threshold counts, and all encoded constraints from the final assignment.

## Pilot order

1. Synthetic exact-enumeration toy.
2. Small real state at tract or VTD level.
3. Same real state with a hierarchy whose finest level matches the atomic model.
4. Several methodologically different small/medium states chosen by computational characteristics, not partisan desirability.
5. Only then scale nationally.

## Go/no-go standard

A methods paper is credible if it can do at least one of the following:

- exactly certify multiple nontrivial frontier points at realistic resolution;
- close most frontier gaps to <1 seat so integrality certifies them;
- or, if exact closure is too hard, establish new strong upper bounds with demonstrable dominance over existing relaxations and rigorous monotonicity.

If the hierarchy is consistently too loose at realistic resolution and the local cuts do not materially improve it, the paper should be killed or narrowed before national-scale compute.

## Paper positioning

Primary identity: discrete optimization / certifiable political districting.

Not the main identity:
- election forecasting;
- advocacy;
- legal determination;
- a new fairness metric.

## Current authoritative working title

**Certified Gerrymanderability: Adaptive Geographic Relaxations for the U.S. House Seat–Safety Frontier**
