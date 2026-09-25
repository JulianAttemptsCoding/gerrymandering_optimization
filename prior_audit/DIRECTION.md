# DIRECTION — highest-impact research path after the audit

## 0. Recommendation (answer first)

**Build certified brackets on the "seat–safety frontier" of U.S. House maps after *Louisiana v. Callais*: for each state, party, safety margin, and explicit legal-constraint regime, prove an upper bound and construct a matching (or near-matching) map, then measure how much redistricting "headroom" remains for 2028 relative to the enacted 2026 maps.**

- Working title: *How far can the House redistricting arms race go? Certified bounds after* Callais.
- Headline outputs:
  - $[L,U]$ brackets on $S^*_{s,\pi,\rho}(m)$ (max seats for party $\pi$ with margin ≥ $m$ under regime $\rho$).
  - **Headroom** $=S^*-S^{\text{enacted 2026}}$.
  - **"*Callais* dividend"** $=S^*_{\text{no VRA proxy}}-S^*_{\text{VRA proxy}}$.
  - **Price of geography** = geography-free bound − certified geographic optimum.
- Optional, time-critical add-on (Phase 0): a **preregistered out-of-sample durability test on the Nov 3, 2026 midterm** — must be frozen before election day.

Why this and not the document's plan: the audit shows the doc's novel constructs are either ensemble-free (envelope width), rounding artifacts (neutrality floor), or mislabeled ($G$). The surviving high-value core is **certification + durability**, and the 2025–26 legal/political shock makes it policy-urgent now.

---

## 1. Why this direction wins (ranked alternatives)

Scores 1–5 (5 = best). Impact = scholarly + policy; Novelty = after positioning against verified prior art; Feasibility = for one strong quant researcher in 3–6 months; Fit = your stated skills (robust estimation, optimization-adjacent math, reproducible pipelines).

| # | Direction | Impact | Novelty | Feasibility | Fit | Verdict |
|---|---|---|---|---|---|---|
| 1 | **Certified seat–safety frontier + post-*Callais* headroom** | 5 | 4 | 3 | 5 | **Primary** |
| 2 | Preregistered 2026-midterm durability ("dummymander") test | 4 | 4 | 3 (deadline) | 4 | **Time-critical add-on** |
| 3 | Bias/responsiveness/residual decomposition + integrality-corrected neutrality (methods note) | 2 | 3 | 5 | 5 | Side note / appendix |
| 4 | Temporal gerrymanderability 2008–2024 at fixed statewide share | 3 | 2–3 | 4 | 4 | Secondary; Kenny 2026 adjacent |
| 5 | Doc's original neutrality floor | 1 | 1 | 4 | 4 | **Do not pursue** |

Why #1 is highest impact:
- **Policy demand is concrete and unmet.** Public estimates of post-*Callais* seat shifts are rough counts ("at least 15 districts" per an NPR analysis cited by Brookings; "16 to 18" per Democracy Docket). No one has published *provable ceilings*. 2028 redraws are being organized now (e.g., Georgia special session reported).
- **Certification is crisp for seat counts.** Seats are integers: if $U<L+1$, the constructed map is provably optimal. A sentence like "no Tennessee map under regime ρ yields more than k Republican seats with ≥10-point margins" is a publishable fact, not a model estimate.
- **The margin axis turns a static max into a durability object.** The Atlas "Max" (≥51%) and "Safe Max" (≥55%) maps are two *lower-bound* points on this same curve.
- **Mathematical depth.** Valid relaxations, refinement monotonicity, and certificate formats are your comparative advantage.

---

## 2. Research questions and estimands

Let $s$ = state, $\pi\in\{D,R\}$, $b$ = electoral baseline (default: 2024 presidential two-party vote projected to 2020 VTDs), $\rho$ = constraint regime, $m\ge 0$ = safety margin in two-party share points.

- **Frontier.** $S^*_{s,\pi,\rho,b}(m)=\max_{M\in\Omega_s^\rho}\ \#\{d\in M:\ \text{share}_\pi(d;b)\ge \tfrac12+m\}$.
- **Bracket.** $L\le S^*\le U$: $L$ from a constructed map that passes an independent validity check; $U$ from a certified relaxation.
- **Headroom.** $H_{s,\pi}(m)=S^*_{s,\pi}(m)-S^{\text{enacted}}_{s,\pi}(m)$ (bracketed).
- **Callais dividend.** $\Delta^{\text{VRA}}_{s,\pi}(m)=S^*_{\rho=R1}(m)-S^*_{\rho=R2}(m)$.
- **Price of geography.** $\text{PoG}_s(m)=U_{\text{geo-free}}(m)-S^*_s(m)$, linking to Owen–Grofman / Friedman–Holden / Kolotilin–Wolitzky theory.
- **National headroom.** $\sum_{s\in\mathcal C_\pi}H_{s,\pi}(m)$ over states where party $\pi$ can plausibly enact maps ($\mathcal C_\pi$ is a declared modeling input, sourced from NCSL/Ballotpedia).

Constraint regimes (modeling choices, **not** legal determinations):
- **R0:** contiguity + population balance (VTD-level tolerance τ, or fractional VTD splitting with exact balance).
- **R1:** R0 + county-split cap (ALARM default: fewer split counties than districts) or state-specific rules you verify.
- **R2:** R1 + a VRA *proxy*: at least $k_s$ districts with minority VAP ≥ 50%, where $k_s$ = count in the pre-*Callais* enacted map.

---

## 3. Novelty positioning (verified prior art)

| Work | What it does | Gap you fill |
|---|---|---|
| Kenny, Algorithmic Redistricting Atlas (2026) | Max (≥51%) / Safe Max (≥55%) maps via short bursts; 2026 enacted layer; explicitly no optimality guarantee | Upper bounds, whole margin curve, regimes, headroom |
| Fravel, Hildebrand, Goedert, Travis & Pierson, MMOR (2026) | Dual bounds for expected partisan/Black representation, exact contiguity, **county-level**, relaxed population tolerance | Their optimum over counties is **not** an upper bound for precinct-level plans (coarser units shrink the feasible set). You need **precinct-valid** relaxations + national, post-*Callais* application |
| Goedert, Hildebrand, Travis & Pierson, LSQ (2024) | Heuristic optimized maps, asymmetry of potential | Certification; regimes; 2026 maps |
| Gurnee & Shmoys, Fairmandering (2021) | Column-generation heuristic; seat ranges | Dual bounds |
| Palmer & Schneer, AJPS (2026) | Durable majorities, state legislatures, heuristic | House, certified, margin frontier |
| Duchin et al., ELJ (2019) | Proof that no MA plan yields an R seat | Systematic, multi-state, multi-margin |
| Validi–Buchanan–Lykhovyd (OR 2022); Validi–Buchanan (MPC 2022); Shahmizad–Buchanan (OR 2025) | Exact contiguity MIPs for compactness / county splits | Partisan threshold objectives, fractional-split relaxations |
| Swamy–King–Jacobson (OR 2023) | Multilevel exact bi-objective fairness MILP (Wisconsin) | Coarsened solves are not certificates for the fine problem |
| Kenny et al., PNAS (2023) | Ensemble-relative national bias, responsiveness | Extremes and certificates, not ensemble comparisons |

**Residual scoop risk:** moderate. The Atlas maps are labeled prototypes "likely to be updated", and the Virginia Tech group already has bound machinery. Mitigations: (a) move fast on a small-state pilot; (b) consider contacting either group about collaboration rather than competing.
**Before investing, run a one-day re-check:** arXiv (physics.soc-ph, cs.DS, math.OC), SSRN, SocArXiv, Optimization Online for "dual bound" / "upper bound" + "seats" + "precinct" / "VTD" + 2026.

---

## 4. Method

### 4.1 Lower bounds (constructive maps)
- `redist_shortburst()` with a custom score: count of districts meeting the margin, plus a small smooth tie-breaker (raw seat counts create flat plateaus; Define–Combine also used a smoothed score).
- Many independent restarts; also seed from the Atlas Max / Safe Max maps where available.
- **Every map passes an independent checker** (separate code, raw data): population per district, connectivity (networkx), county splits, VRA-proxy counts, recomputed margins.

### 4.2 Upper bounds (certified relaxation family)
Variables: fractional precinct shares $x_{ij}\in[0,1]$; unit-support binaries $y_{uj}$ on a unit partition $\mathcal U$; win binaries $w_j$; connectivity of $\{u:y_{uj}=1\}$ via single-commodity flow (prototype) or cut constraints with lazy separation (Validi–Buchanan style, at scale).

- **Lemma 3 (validity).** Every contiguous, balanced plan maps to a feasible point of $R(\mathcal U)$ with the same objective, so $\max R(\mathcal U)\ge S^*$.
  - *Proof sketch:* set $x$ to the plan's assignment and $y_{uj}=1$ iff district $j$ touches unit $u$. A connected district touches a connected set of units, because a path of precincts maps to a walk of adjacent units. ∎
- **Lemma 4 (monotone refinement).** If $\mathcal U'$ refines $\mathcal U$, then $\max R(\mathcal U')\le\max R(\mathcal U)$, since connected fine support implies connected coarse support.
- **Adaptive refinement:** solve; split every multi-precinct unit that the relaxed optimum shares among ≥2 districts; re-solve; stop when $U<L+1$ or the budget is exhausted.
- **Model-choice caveat (QC catch):** the strengthening $y_{uj}\le\sum_{i\in u}x_{ij}$ is valid **only for whole-precinct plans**. If you model block-level VTD splitting (real plans do split VTDs), drop it. Votes inside a VTD are then assumed proportional to VAP — the same assumption as the Atlas projection.
- **Toy evidence** (`code/qc_checks_iter2.py`, `code/qc_checks_iter3.py`):

  | Relaxation | m=0 | m=0.02 | m=0.05 |
  |---|---|---|---|
  | exact optimum (enumeration) | 2 | 2 | 2 |
  | flow MILP, precinct units, integer $x$ | 2 ✔ contiguous & balanced | 2 | 2 |
  | geography-free fractional | 4 | 3 | 2 |
  | 9 coarse blocks | 4 | 3 | 2 |
  | after 1 adaptive refinement (21/25 units) | **2 (certified)** | **2 (certified)** | — |

  Interpretation: coarse relaxations can be loose by 2 seats even on a toy; adaptive refinement closed the gap in one step. Whether the savings scale is **the** empirical question of the pilot (Gate G5).
- **Extensions:**
  - Expected-seat (probit) objectives via Fravel et al.'s stepwise relaxations.
  - Symmetry breaking (order districts by $w$ and by anchor unit).
  - Knapsack/cover cuts on population.
  - A geography-free "vote-mass" cap $\sum_j w_j\le\lfloor V_\pi/v_{\min}\rfloor$.

### 4.3 Certificate format (so referees can verify)
Per $(s,\pi,\rho,m)$ publish:
- the best map (block/VTD assignment + hash) and its checker log;
- the unit partition used;
- the relaxation model file (`.mps`/`.lp`);
- the solver's proven bound and log;
- the validity proof reference (Lemmas 3–4).

Tolerance discipline: use the same ε for "≥ ½+m" in both bounds.

### 4.4 Out-of-sample axis (links to Phase 0)
- The margin $m$ is a durability proxy. Test it on 2026 (and later) results: flip rates by 2024-baseline margin bucket for newly drawn vs carried-over districts.

---

## 5. Phased plan with gates

### Phase 0 — optional, time-critical: preregistration (now → Oct 30, 2026)
- **Deadline logic:** predictions must be frozen before any Nov 3 results exist. Louisiana's House general election is reported as Dec 12 (secondary source; verify). Missouri's map status depends on a Nov 3 veto referendum (secondary source; verify which map governs Nov 2026).
- **Scope:** districts in states with new 2026 maps. The Atlas 2026 layer covers CA, FL, LA, MO, NC, OH, TN, TX, UT; Alabama's map needs a separate source.
- **Preregister (OSF), with code hash:**
  - **H1 (margin–durability):** conditional on the national environment, the drawing party's loss probability decreases in the district's 2024 baseline margin, and newly drawn target districts underperform baseline by more than carried-over districts.
  - **H2 (Hispanic reversion):** in TX/FL/CA redrawn districts, the residual (actual − baseline-plus-swing) for the drawing party is negatively associated with Hispanic CVAP share.
  - **H3 (estimand only):** realized seat effect of each new map vs the prior map, computed on 2026 precinct returns when released.
- **Gate G0:** do Phase 0 only if you can commit about 40–60 focused hours before Oct 30. Otherwise skip it. Do **not** backfill predictions after results — that invalidates the design.

### Phase 1 — harness and small-instance validation (weeks 1–3)
- **G1:** toy reproduces (enumeration 4006; flow MILP exact = 2; hierarchy valid). *(Already passing: `results/`.)*
- **G2:** for one real small state, the exported unit graph is connected; population sums match the census state total; 2024 vote totals match the official statewide two-party totals within projection error you report.
- **G3:** on a coarsened instance small enough to enumerate or solve exactly (≤ ~30 units), relaxation $U$ = exact optimum and short-burst $L$ = exact optimum.

### Phase 2 — pilot on post-*Callais* small-k states (weeks 3–8)
- **States:** MS (4), LA (6), AL (7), SC (7), TN (9). Small k and directly *Callais*-relevant.
- **Grid:** $\pi\in\{D,R\}$ × $m\in\{0,.025,.05,.075,.10\}$ × $\rho\in\{R0,R1,R2\}$.
- **G4:** every reported $L$ passes the independent checker; every $U\ge L$ (any violation = bug; stop).
- **G5 (go/no-go):** ≥60% of cells certified ($U-L<1$) within 24 CPU-hours per cell, and median bracket width ≤1 seat.
  - If 30–60%: continue with stronger cuts and a finer initial partition.
  - If <30%: pivot (§8).

### Phase 3 — scale and aggregate (months 3–6)
- **States:** GA (14), NC (14), then blue-state D-max cases (IL, NY, NJ, MD, CO, WA, OR, VA). Stretch: FL (28), TX (38).
- **Outputs:** national headroom brackets by controlling party; *Callais* dividend; price of geography.

### Phase 4 — out-of-sample and write-up (2027 H1)
- When precinct-level 2026 returns are available: evaluate H1–H3; re-score frontier maps under the 2026 baseline (durability of frontier maps).
- Papers:
  - Methods: *Operations Research* / *Math Programming Computation* / *INFORMS J. Computing*.
  - Substantive: *PNAS* / *Science Advances* / *Political Analysis* / *APSR*.
  - Policy/legal: *Election Law Journal*.

---

## 6. Step-by-step commands, paths, expected outputs

Directory layout (proposed):
```text
project/
  code/            # this zip's code/ + new modules
  data/<ST>/       # units.parquet, edges.csv, enacted_2026.csv
  runs/<ST>/<pi>_<rho>_m<m>/   # lower/, upper/, certificate.json
  prereg/          # Phase 0 OSF materials
```

1) Reproduce toy QC (Python ≥3.10):
```bash
pip install numpy scipy networkx
cd code && python3 qc_checks.py && python3 qc_checks_iter2.py && python3 qc_checks_iter3.py
# expect: C0 4006; C8b exact_flowMILP value 2 with returned_plan_contiguous_balanced true;
#         iter3 m=0.0 trace 4 -> 2 certified true
```

2) Get state data (R ≥4.3). **Verify function and column names before trusting them** — they are expected, not confirmed:
```r
install.packages(c("redist", "alarmdata", "geomander", "sf", "dplyr", "arrow"))
library(alarmdata); ls("package:alarmdata")          # GATE: confirm function names
map   <- alarm_50state_map("AL")                      # expected: VTD-level redist_map
names(map)                                            # GATE: find pop, VAP-by-race, vote columns
```

3) Export graph and attributes:
```r
library(sf); library(arrow)
write_parquet(sf::st_drop_geometry(map), "data/AL/units.parquet")
adj <- map$adj    # expected 0-indexed neighbor lists; GATE: check symmetric & length == nrow(map)
e <- do.call(rbind, lapply(seq_along(adj), function(i) if (length(adj[[i]])) cbind(i - 1, adj[[i]])))
write.csv(e, "data/AL/edges.csv", row.names = FALSE)
```
Expected: `edges.csv` symmetric; one connected component (islands need manual edges — the ALARM docs describe their handling).

4) 2024 baseline: use the Atlas's source (Kenny 2026 VTD-projected 2024 presidential returns) if downloadable. Otherwise use Redistricting Data Hub / Metcalf 2024 precincts + `geomander` projection. **GATE G2:** statewide two-party totals reconcile.

5) Lower bound (R) — replace `rep24` / `dem24` with the verified column names:
```r
m_margin <- 0.05
score_seats_m <- function(pl) apply(pl, 2, function(z) {
  sh <- tapply(map$rep24, z, sum) / tapply(map$rep24 + map$dem24, z, sum)
  sum(sh >= 0.5 + m_margin) + mean(pmin(sh, 0.5 + m_margin))   # tie-breaker < 1
})
res <- redist_shortburst(map, score_seats_m, max_bursts = 2000, maximize = TRUE,
                         backend = "mergesplit")
```
Expected: a monotone best-score trace; export the best plan and run the independent checker. Floor(score) = seats.

6) Upper bound (Python): generalize `flow_milp()` from `code/qc_checks_iter2.py` to arbitrary unit graphs (read `units.parquet`/`edges.csv`). Use HiGHS for pilots and Gurobi + lazy cut constraints for scale. Expected per run: `certificate.json` with `{L, U, units, solver_bound, status, runtime}`.

---

## 7. Failure modes (ranked) and mitigations
1. **Loose relaxations** (big-M, fractional support). → Indicator constraints; district-ordering symmetry breaking; adaptive refinement; cover cuts; tighter big-M from per-district vote bounds.
2. **Validity bugs** (an "upper bound" below a verified feasible map). → Gate G4 hard stop; unit tests on enumerable instances.
3. **Invalid strengthening for the chosen plan model** (`y ≤ Σx` with block splits). → One config flag; tests for both models.
4. **Data misalignment** (2024 votes projected to 2020 VTDs by VAP). → Report reconciliation error; sensitivity to an alternative baseline (2020 pres, a composite).
5. **Threshold tolerance mismatch** between L and U (≥ vs >). → A single ε constant shared by both codes.
6. **Legal-regime overclaiming.** → Always "under encoded regime ρ"; never "legal".
7. **Moving targets** (maps enjoined or changed; Missouri referendum; Alabama). → Freeze a dated snapshot per run; record provenance.
8. **Solver access.** → HiGHS works for pilots. Gurobi academic eligibility depends on your affiliation — not assumed here.

---

## 8. Kill criteria / pivots
- G5 < 30% certified after refinement → **Plan B1:** certify at declared granularity (county/tract) and bound the granularity gap empirically. **Plan B2:** switch to expected-seat objectives with Fravel-style relaxations.
- A competing precinct-valid national-bracket paper appears → pivot to the margin-frontier durability analysis + Phase 4 out-of-sample (still novel if preregistered).
- Phase 0 not frozen by Oct 30 → drop H1–H2 preregistration. Keep H3 as a post-hoc descriptive estimand, clearly labeled.

---

## 9. Items I could not resolve (need your input)
1. Solver: do you have (or qualify for) a Gurobi academic license, or should the plan assume HiGHS/SCIP only?
2. Compute: rough CPU-hours/month available?
3. Phase 0: can you commit ~40–60 hours before Oct 30?
4. First paper: methods-first (OR venue) or substantive-first (PNAS / political science)?
5. Openness to contacting the ALARM/Atlas or Virginia Tech (RAVT) groups?
