# QC recheck — 2026-09-23

The uploaded `prior_audit/code/qc_checks.py` was re-run.

Reproduced:
- exact toy plans: **4,006**;
- ensemble-width cancellation checks passed;
- argmax baseline-subtracted signed statistic equals argmax mean seats;
- deterministic neutrality-floor behavior remained near the rounding lower bound;
- safety toy:
  - \(m=0.00\): exact 2, coarse 4;
  - \(m=0.02\): exact 2, coarse 3;
  - \(m=0.05\): exact 2, coarse 2;
  - \(m=0.08\): exact 2, coarse 2.

Conceptual conclusions:
1. ensemble-relative width is not ensemble-relative;
2. signed baseline subtraction does not alter the maximizer;
3. full safety frontier is a cleaner extremal object;
4. upper certification requires **outer**, not whole-cell restrictive, coarsening;
5. inexact contiguity cannot support a global certificate;
6. accidental integrality in purported fractional models must be audited.

The new AHGOR construction remains a **research design** until implemented on real data. The main unknown is whether its upper bounds stay useful at realistic resolution.
