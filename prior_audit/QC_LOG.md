# QC LOG — research / QA / QC iterations

Each loop = (claim or plan) → (check) → (result) → (change). Nothing below relies on memory alone where a source could be checked.

## Loop R — literature and citations
| # | Check | Result | Change made |
|---|---|---|---|
| R1 | Palmer–Schneer AJPS 2026 exists and scope | ✅ Early View Aug 2026; state legislatures | none |
| R2 | Econometrica 2026 authorship | ⚠️ Kolotilin **& Wolitzky** | F8 |
| R3 | Atlas Max/Safe Max thresholds | ⚠️ Max = 51% (doc: 50%); Atlas also has a 2026 enacted layer | F9; used in Phase 0 |
| R4 | LSQ 2024 authorship | ⚠️ 4 authors (doc: 2) | F9 |
| R5 | Barber–Taylor–Trende ELJ 2026 | ✅ | none |
| R6 | Legal changes since doc's frame | ✅ *Callais* 2026-04-29 (SCOTUS PDF, CRS) | F3 (critical) |
| R7 | 2025–26 mid-decade wave | ✅ Ballotpedia, CRS; Wikipedia used only for cross-checking | F3; Phase 0 scope |
| R8 | National ensemble-relative prior art | ✅ Kenny et al. PNAS 2023 | F6 |
| R9 | Certification prior art (doc: "sparse") | ✅ Fravel et al. MMOR 2026; Duchin et al. 2019 | F5; forced the direction to be *precinct-valid* |
| R10 | Distance-to-ensemble-mean prior art | ✅ Herschlag et al. 2020; Gonatas 2021 | F2 context |
| R11 | Exact districting MIPs | ✅ Validi–Buchanan(–Lykhovyd), Shahmizad–Buchanan, Swamy–King–Jacobson | F6; method basis |
| R12 | `redist_shortburst` capabilities | ✅ custom score_fn, mergesplit/flip, vector scores | none |
| R13 | ALARM ensemble details | ✅ 0.5% tol; VRA target = enacted count; 2016–2020 elections | F3, F11 |
| R14 | Post-*Callais* public seat estimates | ✅ Brookings (NPR ≥15), Democracy Docket (16–18) — rough counts only | motivates certification |
| R15 | Dummymander discourse 2026 | ✅ many commentaries; no preregistered ensemble-based test found | Phase 0 retained (moderate novelty) |

## Loop M — mathematics (proofs + exact toy; code in `code/`, outputs in `results/`)
| # | Claim tested | Result | Consequence |
|---|---|---|---|
| M0 | Toy enumeration correct | 4006 plans (known value) ✅ | harness trusted |
| M1 | §6 degeneracy | holds (C1) | doc correct |
| M2 | Envelope/W ensemble-relative? | **No** — Lemma 1; identical widths across 3 ensembles (C2) | F1 |
| M3 | C ∈ [0,1] | holds (C3) | doc correct |
| M4 | Neutrality floor informative? | $G^{\min}/L_{\text{int}}$ = 1.000 / 1.0016 / 1.000; 7–27 tied minimizers (C4) | F2 |
| M5 | $G$ = partisan distortion? | C=0.098 map at G-percentile 94.5; 57% of top-decile G have C<0.5 (C5b) | F4 |
| M6 | Ensemble robustness | A flips sign; argmax-G party flips; argmin differs ×3 (C6) | F12 |
| M7 | In-sample optimism | +0.0009 mean, 66% positive (C7) | F13 (minor) |
| M8 | Certification relaxations valid? | exact ≤ all relaxations at all m (C8, C8b) | Lemma 3 supported |
| M9 | Flow-MILP formulation correct? | integer precinct model = enumeration optimum; returned plan contiguous & balanced (C8b) | formulation trusted |
| M10 | Are coarse relaxations tight? | **No**: 4 vs 2 at m=0 | added adaptive refinement + gate G5 |
| M11 | Does adaptive refinement close gap? | 9→21 units, bound 4→2 (m=0), 3→2 (m=0.02), certified (iter3) | method retained; scaling is pilot question |

## Loop D — direction revisions
| # | Draft | Problem found | Revision |
|---|---|---|---|
| D1 | "Fix the neutrality floor" as main paper | M4: rounding artifact; normative objection; prior art | demoted to methods note (#3) |
| D2 | "Certified bounds" (generic) | R9: Fravel et al. 2026 already give county-level dual bounds | narrowed to **precinct-valid** bounds + margin frontier + post-*Callais* regimes + headroom |
| D3 | Coarse (county) relaxation as the certification engine | M10: loose by 2 seats even on toy | adaptive refinement (Lemma 4) + explicit go/no-go gate G5 |
| D4 | Strengthening $y\le\sum x$ everywhere | Invalid when VTDs can be split at block level | model-dependent flag (DIRECTION §4.2) |
| D5 | Durability study, retrospective only | Nov 3, 2026 offers a genuine out-of-sample test | Phase 0 preregistration, with a hard freeze date |
| D6 | "All states" scope | Feasibility; policy relevance concentrated in *Callais* states | pilot MS/LA/AL/SC/TN first |

## Residual uncertainties (explicitly not resolved)
- Exact `alarmdata` function and column names (marked GATE in DIRECTION §6).
- Which Missouri map governs Nov 2026; Louisiana schedule (secondary sources only).
- Scalability of adaptive refinement beyond small-k states — the purpose of Gate G5.
- Unverified doc refs listed in SOURCES.md.
