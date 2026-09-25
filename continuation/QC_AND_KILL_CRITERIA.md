# QC and kill criteria

## Hard correctness gates
1. Exact toy: all upper bounds satisfy \(U\ge F\).
2. All lower witnesses satisfy \(L\le F\).
3. Refinement must be monotone:
   \[
   U_0\ge U_1\ge\dots.
   \]
4. Atomic refinement must reproduce exact optimum on a manageable instance.
5. Every local cut is exhaustively/randomly validated on small cells.
6. Independent lower-map verifier is separate from solver model.
7. Final certificates may not rely on an inexact contiguity formulation that can exclude valid maps.
8. Party-label swap must produce corresponding symmetric behavior.
9. Scenario-set expansion must not increase robust frontier.
10. Nested constraint tightening must not increase frontier.

## Critical implementation pitfalls
- Whole-VTD coarsening is a restriction, not an upper relaxation.
- Independent vote/population splitting may be too loose; local envelopes matter.
- Support binaries can accidentally restrict valid maps.
- “Continuous” assignment can become accidentally integral through linking.
- MILP incumbent is a lower bound in maximization; best bound is the upper bound.
- Floating-point vote thresholds can change seat classification; use rational/integer arithmetic where possible.
- Computational constraints are not automatically legal standards.

## Performance gate
Before national scaling, require several nontrivial real frontier points to:
- close exactly, or
- approach within <1 seat, or
- show a large, reproducible improvement over baseline upper relaxations.

If the upper model remains effectively trivial after realistic refinement and stronger local cuts, kill or narrow the project.

## Novelty kill criterion
If a final literature audit finds an existing paper with the same adaptive valid outer hierarchy + seat-safety frontier + comparable fine-resolution certification, pivot rather than relabel the same method.
