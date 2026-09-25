# Paper blueprint

## Working title
**Certified Gerrymanderability: Adaptive Geographic Relaxations for the U.S. House Seat–Safety Frontier**

## Core story
Heuristic redistricting algorithms can find extreme maps, but a found map does not establish the true extremal limit. The paper converts extreme partisan districting into a certification problem.

For each margin:
\[
L_s(m)\le F_s(m)\le U_s(m).
\]

The lower curve is witnessed by feasible maps; the upper curve is mathematically certified.

## Section plan
1. Introduction: heuristic extremeness versus certified extremality.
2. Related work.
3. Seat–safety frontier and spectrum.
4. Exact fixed-margin MILP.
5. Adaptive hierarchical geographic outer relaxation.
6. Local fractional-knapsack / support-function cuts.
7. Lower-bound search and independent verification.
8. Synthetic exact validation.
9. U.S. House real-state pilot.
10. National decomposition / extension.
11. Measurement and constraint sensitivity.
12. Limitations.

## Core theorem package
- frontier/spectrum generalized inverse;
- layer-cake identity;
- state separability;
- quotient-connectivity lemma;
- outer-validity theorem;
- monotone-refinement theorem;
- finite-convergence theorem;
- integer certificate corollary;
- local-envelope validity proposition.

## Central figure
x-axis: safety margin \(m\).  
y-axis: number of seats.

Plot:
- lower staircase \(L(m)\);
- upper staircase \(U(m)\);
- unresolved band.

This figure displays both knowledge and uncertainty honestly.

## Essential ablation
Compare:
1. conservation-only coarse relaxation;
2. + quotient connectivity;
3. + local knapsack envelopes;
4. + adaptive refinement.

Report:
- upper-bound quality;
- gap;
- runtime;
- nodes;
- memory.

## Impact threshold
The paper is not ready merely because it generates interesting maps.

At least one should hold:
- exact certification of multiple nontrivial real-state frontier points;
- most gaps below one seat;
- new relaxation strongly dominates baseline upper bounds;
- broader graph-partition insight that generalizes beyond redistricting.

## Venue identity
Primary: discrete optimization / mathematical political methodology.

Exact venue should depend on what the real pilot proves, not be fixed in advance.
