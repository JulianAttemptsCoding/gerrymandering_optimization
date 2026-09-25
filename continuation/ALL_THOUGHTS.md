# ALL THOUGHTS — shareable research decision log

This file is the fullest **shareable** project reasoning log: ideas, failures, retained mathematics, novelty boundaries, risks, and next steps. It is not private chain-of-thought.

## 1. Original direction
The project began with a single quantitative “gerrymandering-ness” formula, then the idea of optimizing U.S. House maps for maximum and minimum values.

That produced candidate paths:
- fairness scalar;
- neutral-ensemble deviation;
- feasible seat range;
- durable map optimization;
- exact/certified extrema.

## 2. Why the scalar-metric route weakened
Prominent metrics already compress different phenomena:
- partisan direction;
- response slope;
- geography;
- vote-seat discreteness.

The uploaded toy showed that an RMS ensemble-deviation quantity can rank maps highly because of responsiveness rather than durable partisan bias. That is a poor basis for a new “true” metric.

## 3. Ensemble-relative width cancellation
For map-independent baseline \(\mu\),
\[
d(M)=S(M)-\mu.
\]
Then
\[
\max d-\min d=\max S-\min S.
\]
So the proposed “ensemble-relative envelope width” was only an ordinary feasible seat range.

Similarly:
\[
\arg\max E[S-\mu]=\arg\max E[S].
\]
Baseline subtraction does not create a new extremal problem.

## 4. Neutrality floor failure
Hard seat counts create rounding/discreteness. The toy showed the minimum ensemble-distance value could nearly equal a simple rounding lower bound, with many tied maps and sensitivity to how the reference ensemble is sampled.

Conclusion: do not headline this quantity.

## 5. Plain min/max seats is prior art
Fairmandering, extreme-map optimization, the Algorithmic Redistricting Atlas, and the 2025 FAccT France work all substantially occupy the “feasible range / gerrymandering potential” space.

Conclusion: not novel enough.

## 6. Durability is adjacent current work
Palmer & Schneer (2026) directly study durable majority gerrymanders under electoral uncertainty.

Conclusion: multiple-election robustness is useful, but not the novelty core.

## 7. Main pivot
Existing algorithms can find extreme maps. The unresolved mathematical question is often:
> how close is this found map to the true extremum?

This creates a certifiable optimization project.

For maximization:
- feasible map = lower bound;
- valid relaxation = upper bound;
- close the gap.

## 8. Seat–safety frontier
Define robust district margin:
\[
r_j^\pi(M)=\min_{\omega\in\Omega}\left(v_j^\pi(M,\omega)-\tfrac12\right).
\]

Define:
\[
F(m)=\max_M\#\{j:r_j^\pi(M)\ge m\}.
\]

This generalizes one-off 51% / 55% objectives to a whole curve.

## 9. Seat–safety spectrum
Sort robust margins:
\[
r_{(1)}\ge\dots\ge r_{(k)}.
\]

Define:
\[
\sigma^*(q)=\max_Mr_{(q)}(M).
\]

Then:
\[
F(m)\ge q\iff \sigma^*(q)\ge m.
\]

So:
\[
F(m)=\max\{q:\sigma^*(q)\ge m\}.
\]

## 10. Layer-cake identity
\[
F(m)=\sum_q\mathbf 1\{\sigma^*(q)\ge m\}
\]
implies
\[
\int_0^{1/2}F(m)\,dm
=
\sum_q[\sigma^*(q)]_+.
\]

This is a structural summary, not a fairness axiom.

## 11. Fixed-margin linearization
At fixed \(m\):
\[
\frac{P}{P+O}\ge\tfrac12+m
\]
iff
\[
(\tfrac12-m)P-(\tfrac12+m)O\ge0.
\]

Thus each frontier point is a mixed-integer graph-partition problem with a linear safety condition.

## 12. Why standard coarsening is wrong for upper certification
Forcing counties/tracts/VTDs whole creates a subset of real maps.

For maximization, that yields another lower bound.

We instead need a superset of projected exact maps.

## 13. Adaptive Hierarchical Geographic Outer Relaxation
Partition atoms into coarse cells.

Within a cell, allow aggregate population/votes/demographics to split among districts according to an **outer polytope** that contains every atomic split.

Then:
\[
F(m)\le U_{\mathcal P}(m).
\]

Refine selected cells to tighten.

## 14. Quotient connectivity
Any atomic connected district touches a connected set of coarse cells in the quotient graph.

Thus quotient support connectivity is a valid necessary condition.

Allowing phantom support is safe for the upper direction if needed.

## 15. Monotone refinement
Require every child relaxation to project inside its parent relaxation.

Then:
\[
U_{\mathcal P'}\le U_{\mathcal P}.
\]

At singleton atoms with exact assignment/contiguity:
\[
U_{\rm atom}=F.
\]

This gives finite convergence.

## 16. Integer certificate
If witness map has \(L\) seats and
\[
U<L+1,
\]
then integer objective forces:
\[
F=L.
\]

This is a practical advantage: the continuous/numerical bound need only cross the next seat.

## 17. Main risk: weak aggregate allocations
Total conservation alone can let a coarse cell give one district implausibly high party vote mass with very little population.

Need stronger local cuts.

## 18. Fractional-knapsack envelope idea
For cell atoms with \((p_i,q_i)\), allow fractional selection.

Upper envelope:
\[
\overline\phi_C(x)
=
\max\left\{\sum_iq_i\lambda_i:
\sum_ip_i\lambda_i=x,\;0\le\lambda_i\le1\right\}.
\]

Lower envelope analogous.

Every whole-block subset lies inside:
\[
\underline\phi_C(p_{Cj})
\le q_{Cj}
\le\overline\phi_C(p_{Cj}).
\]

These are valid outer cuts and may sharply reduce unrealistic coarse allocations.

## 19. General local hull
Conceptually:
\[
\mathcal H_C^k=\operatorname{conv}\{\text{all true \(k\)-way atomic attribute allocations in }C\}.
\]

Possible hierarchy:
- conservation;
- knapsack envelopes;
- pairwise/joint cuts;
- support-function cuts;
- exact local enumeration in small refined cells.

This may become the deepest OR contribution.

## 20. Adaptive refinement heuristics
Candidates:
- split entropy;
- phantom connector usage;
- near-threshold influence;
- envelope slack;
- dual impact;
- largest cell fallback.

Refinement policy affects speed only, not correctness.

## 21. Lower-bound method
Use existing short-burst / merge-split search.
Do not spend novelty budget on a new map generator initially.

Every candidate lower map is independently verified.

## 22. No GNN/RL initially
A learned map drawer would complicate hard constraints and still not give a global upper bound.

A learned refinement policy can be a later extension if it accelerates certificates.

## 23. Exact contiguity is prior art
Use Validi/Buchanan-style exact formulations.
Do not claim exact connectivity as new.

Current Jolly–Buchanan work reinforces that inexact constraints can cut off valid maps, which is fatal to a claimed global upper bound.

## 24. Closest methodological threat
Fravel et al. (2026) already derive dual bounds for nonconvex representation objectives in redistricting.

The project survives only if it demonstrates a substantive methodological difference:
- full partisan safety frontier;
- adaptive valid geographic hierarchy;
- local attribute envelope cuts;
- finer U.S. House geography;
- explicit certificate curves.

This is the paper that must be read line-by-line.

## 25. “Gerrymanderability” word is not novel
Prior work already uses related gerrymandering-potential / leeway concepts.

Use precise mathematical names:
- seat–safety frontier;
- seat–safety spectrum;
- certified extremal capacity.

## 26. National decomposition
State maps are independent, so:
\[
F_{\rm US}(m)=\sum_sF_s(m).
\]

Likewise:
\[
\sum_sL_s(m)\le F_{\rm US}(m)\le\sum_sU_s(m).
\]

No national mega-MILP is required.

## 27. Census blocks versus VTDs
VTDs align better with observed elections but forcing them whole restricts map space.

Blocks align with redistricting population but election votes are usually not directly observed.

Best scientific practice:
- define exact optimization conditional on a documented block vote allocation;
- compare multiple allocations;
- eventually use a robust within-precinct uncertainty model if needed.

## 28. Potential measurement-robust extension
For precinct totals:
\[
\sum_{b\in P}D_b=D_P,\qquad
\sum_{b\in P}R_b=R_P.
\]

Add block turnout-capacity bounds and optimize over all feasible allocations.

This could make electoral certification robust to downscaling, but may be paper 2.

## 29. Legal caution
The 2026 legal environment changed, including *Louisiana v. Callais*.

Do not reduce current law to a crude “VRA on/off” switch.

Call each model an **encoded constraint regime** unless legal experts validate more.

## 30. Why the Callais-specific idea was demoted
A “Callais dividend” is topical but would make the paper depend on moving legal doctrine and a potentially crude computational representation.

The generic nested-regime result is cleaner:
\[
\mathcal M^{\rho_2}\subseteq\mathcal M^{\rho_1}
\Rightarrow F_{\rho_1}\ge F_{\rho_2}.
\]

## 31. Political symmetry
Run exactly the same method for either party label.
Pick pilot states by computational/data criteria.
Do not recommend enactment of any extremal map.

## 32. Central impact distinction
Heuristic claim:
> “We found a map with X safe seats.”

Certified claim:
> “We found X, and no map in the specified model can have X+1.”

That is the qualitative upgrade.

## 33. Main empirical figure
For each state:
\[
L(m)\le F(m)\le U(m)
\]
as lower and upper staircases.

Resolved regions have zero gap.
Unresolved regions remain visibly shaded.

## 34. Main paper weaknesses to avoid
- only generating maps;
- reporting incumbents as if optimal;
- restrictive coarsening mislabeled as upper bound;
- hidden unresolved gaps;
- ignored block-vote measurement;
- inexact connectivity inside certificate;
- “legal map” overclaim.

## 35. First experiment ladder
1. Existing exact toy.
2. Full toy frontier/spectrum.
3. Coarse valid outer model.
4. Knapsack envelopes.
5. Adaptive refinement to exact atoms.
6. One small real state.
7. Several structured pilots.
8. National only after gap behavior passes.

## 36. Proof obligations
Before large coding:
- quotient connectivity lemma;
- exact-plan embedding;
- monotone refinement compatibility;
- finite convergence;
- envelope validity;
- state decomposition.

## 37. Solver notes
Preferred upper-bound stack: Python + Gurobi.
Open-source fallback: SCIP.
Lower search: R `redist`.

Store incumbent and best bound separately.

## 38. Threshold arithmetic
Prefer rational/integer arithmetic around seat thresholds to avoid floating-point changes.

## 39. Symmetry breaking
District-label symmetry can be reduced with valid anchors/order constraints, but those are engineering, not novelty.

## 40. Compactness
Compactness may be an encoded constraint but should not define gerrymandering itself.

## 41. Constraint sensitivity
For nested regimes:
\[
\Delta(m)=F_{\rm looser}(m)-F_{\rm tighter}(m).
\]

This can quantify how much a structural rule shrinks the feasible frontier without making a political judgment.

## 42. Temporal extension
Recompute the same frontier using electoral geography from multiple election cycles to study how feasible capacity changes through time.

Secondary project.

## 43. Out-of-sample extension
Construct maps using earlier scenarios; evaluate later elections.
Useful but adjacent to active durability literature.

## 44. Broader optimization generalization
The hierarchy may generalize to:
> connected balanced graph partitioning with threshold objectives and additive attributes, certified through adaptive local-allocation outer polytopes.

If successful, this may be more mathematically impactful than the application alone.

## 45. Highest risk
Bound looseness.

If upper models remain trivial until nearly atomic refinement, the method may not scale.

Knapsack envelopes are the first test.

## 46. Second risk
Block election measurement may dominate results.

Must be tested rather than assumed harmless.

## 47. Third risk
Prior art, especially Fravel et al.

Final novelty claims remain provisional.

## 48. Contribution ladder
Minimum:
- formal frontier;
- valid upper/lower bracket;
- real pilot.

Strong:
- adaptive refinement;
- new local cuts;
- several exact real points.

Very strong:
- block/near-block certificates;
- multi-state/national brackets;
- general graph-partition relaxation result.

## 49. Immediate work order
1. Full read of Fravel et al.
2. Formal LaTeX proof write-up.
3. Toy frontier/spectrum implementation.
4. Local envelope implementation and exhaustive validation.
5. One real-state data pipeline.
6. Upper-bound ablation.
7. Decide whether to scale.

## 50. Final project formulation
Do **not** frame the project as:
> invent the one true gerrymandering score and draw the most/least gerrymandered map.

Frame it as:
> **determine, with mathematical certificates, the limits of partisan seat safety that district boundaries can achieve under transparent U.S. House districting models.**

The novelty is **provable bounds + adaptive geographic relaxation**, not a political choice.
