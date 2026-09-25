# Implementation plan

## Reproducibility contract
Every reported point stores:
- input hashes;
- constraint regime;
- electoral scenario set;
- lower witness map;
- independent verifier output;
- upper solver log;
- refinement log;
- final certificate bracket.

## Data
- 2020 Census P.L. 94-171 population/demographic data;
- TIGER/P.L. 94-171 geometry and adjacency;
- documented precinct/VTD election returns;
- explicit precinct-to-finer-unit allocation if using blocks.

## Constraint regimes
Use mathematically explicit regimes:
- core: population + contiguity + district count;
- subdivision-aware;
- state-specific encoded extensions.

Do not call a regime legally sufficient without separate legal verification.

## Lower bound
Use R `redist` short-burst / merge-split first.
Run multiple starts and seeds.
Independently verify every best witness.

## Upper bound
Python + Gurobi preferred; SCIP fallback.

Coarse model:
- aggregate cell attributes;
- fractional internal allocation outer sets;
- support connectivity;
- knapsack envelope cuts.

Leaf model:
- exact atomic assignment;
- exact contiguity;
- exact encoded constraints.

## Refinement loop
1. Solve upper model.
2. Compare with best lower witness.
3. If \(U<L+1\), certify.
4. Otherwise refine cells with high:
   - split entropy;
   - phantom support;
   - threshold impact;
   - envelope slack;
   - dual sensitivity.
5. Warm start and repeat.

## Spectrum
For target seat count \(q\), bisection on \(m\) using monotonicity of \(F(m)\).

## Independent verifier
Check:
- unique assignment;
- nonempty districts;
- population;
- graph connectivity;
- regime constraints;
- vote totals;
- all robust margins;
- safe-seat count.

## Pilot ladder
1. Existing exact toy.
2. One small real state.
3. Same real instance with full hierarchy to atomic model.
4. Diverse small/medium states selected by computational structure.
5. National scale only after gap behavior is understood.

## Measurement caveat
Block-level votes are usually model-allocated from precinct returns. The certificate is conditional on those vote fields unless a robust uncertainty model is added.
