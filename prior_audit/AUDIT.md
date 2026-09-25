# AUDIT — "Extremal gerrymandering / neutrality-floor" research plan

Audit date: 2026-09-23. Scope: every claim, formula, citation, and novelty rating in the supplied document (§1–§40 + its "Research/QC log").
Evidence types: (V) verified against a primary/credible source this session · (P) proved here · (T) confirmed numerically on an exactly-enumerated toy state (`code/`, `results/`) · (U) could not verify — flagged, not assumed.

---

## 0. Verdict (answer first)

- **The document's mathematical core is half right.** Its §6 degeneracy finding is correct, but it fails to apply the same logic to its own flagship constructs: the "ensemble-relative envelope" width (§12) and "gerrymanderability width" $W_s$ (§27) are **mathematically independent of the ensemble** — they are the plain feasible seat range already computed by Fairmandering, Goedert et al., and the 2026 Atlas. (P, T)
- **The "neutrality floor" $G_s^{\min}$ (§10) — the doc's headline novelty — is, under deterministic seat counting, essentially an integer-rounding artifact.** On the toy state, $G^{\min}$ equals a closed-form integrality lower bound to within 0.2% under all three ensembles tested, with 7–27 tied minimizers. (P, T)
- **$G$ is mislabeled as "partisan distortion."** It mixes bias with responsiveness; a map with almost zero directional bias ($C=0.098$) sits at the 94th percentile of $G$. (T)
- **The one genuinely ensemble-relative quantity (asymmetry $A_s$) flips sign across three reasonable ensemble definitions** on the toy state, and the party favored by the argmax-$G$ map also flips. (T)
- **The document is out of date for a "September 2026" review.** It never mentions *Louisiana v. Callais* (decided 2026-04-29), which narrowed VRA §2 and invalidates its recommended VRA-constraint strategy, nor the 2025–26 mid-decade redistricting wave, nor directly overlapping 2023–2026 papers (Kenny et al. PNAS 2023; Fravel et al. 2026 dual bounds). (V)
- **Citation hygiene:** 2 author misattributions, 1 wrong threshold (Atlas "Max" is 51%, not 50%), several unverifiable items, tracking-parameter links. No fabricated papers found among those checked. (V)
- **What survives:** certification/upper bounds (now with real prior art to position against), out-of-sample durability (now testable on the 2026 midterm), and ensemble-sensitivity analysis. These feed the direction in `DIRECTION.md`.

---

## 1. Findings ranked by severity

| ID | Sev. | Doc § | Finding | Evidence | Required fix |
|---|---|---|---|---|---|
| F1 | **Critical** | §12, §26–27, §40 | Envelope width $U_s(v)-L_s(v)$ and $W_s=D_s^+-D_s^-$ do not depend on the ensemble; they equal the plain feasible (expected-)seat range. Claimed "less saturated" novelty is void. | P (§2.2 below); T (width identical across 3 ensembles: det. 0.1818, prob. 0.1470) | Drop "ensemble-relative envelope" as a novelty claim; cite Fairmandering / Goedert et al. / Atlas as the same object. |
| F2 | **Critical** | §10, §28, §40 | Neutrality floor $G^{\min}$ is dominated by an integrality floor computable without optimizing over maps; "irreducible geographic distortion" interpretation unsupported. | P (Lemma 2); T ($G^{\min}/L_{\text{int}}$ = 1.000, 1.0016, 1.000) | Report $G^{\min}-L_{\text{int}}$ (excess over rounding) or use probabilistic seats; drop the headline claim. |
| F3 | **Critical** | §18, §35–36 | Legal feasible set is stale: *Louisiana v. Callais* (2026-04-29) substantially narrowed VRA §2; ALARM's VRA constraints target the enacted count of minority-opportunity districts (circular and now legally contingent); ~10–11 states redrew in 2025–26. | V (SCOTUS opinion; CRS LSB11431; ALARM FAQ; Ballotpedia; CRS IF13082) | Encode explicit constraint regimes (with / without a VRA proxy) and state them as modeling choices, not law. |
| F4 | **High** | §7–9 | $G$ conflates partisan bias with responsiveness (slope). The doc's own $(+2,+2,-2,-2)$ example is a responsiveness pattern, not "partisan" distortion. $G^{\max}$ can be achieved by hyper-responsive maps. | P (§2.3); T (C5b) | Orthogonal decomposition $G^2=b^2+r^2+e^2$ (bias, responsiveness, residual). |
| F5 | **High** | §32, §40 | "Certification is sparse" is outdated: Fravel, Hildebrand, Goedert, Travis & Pierson (MMOR, 2026-03-30) derive dual bounds for expected partisan representation with exact contiguity (county level); Duchin et al. (2019) prove an impossibility bound for MA. | V | Position against both; see DIRECTION.md for the remaining gap. |
| F6 | **High** | whole doc | Missing directly overlapping work: Kenny et al. PNAS 2023 (ensemble-relative national House bias, election model, responsiveness); Duke "Gerrymandering Index" (L² distance to ensemble mean); Swamy–King–Jacobson (OR 2023, exact multilevel fairness MILP); Validi–Buchanan contiguity MIPs; foundational optimal-gerrymander theory (Owen–Grofman 1988; Friedman–Holden 2008; Lagarde–Tomala 2021). | V | Add to related work; several downgrade novelty ratings (§6 below). |
| F7 | **High** | §22–23 | $G$ (and $G^2$) is not separable over districts → the set-partitioning master problem is a convex MIQP (min) or non-convex MIQP (max), not an LP-priced column-generation problem; CG bounds are only valid if pricing is solved to optimality (itself NP-hard). | P (§2.6) | Reformulate (scenario-discretized L1/L2 with auxiliary variables) or restrict certificates to seat-count objectives. |
| F8 | Medium | §5 | "Uncertainty-aware optimization is now an active frontier" — it dates to Owen & Grofman (1988). Kolotilin paper is **Kolotilin & Wolitzky**. | V | Correct attribution and framing. |
| F9 | Medium | §3–4, §9 | "Goedert and Pierson" → actual authors Goedert, Hildebrand, Travis & Pierson (LSQ 49(3):551–583, 2024). Atlas "Max" uses ≥51% (doc says 50%); Safe Max 55% is correct. | V | Fix. |
| F10 | Medium | §11, §16 | Swing model unspecified in §11; §16 mixes percentage-point targets with logit shifts (a fixed logit shift does not give a fixed statewide pp swing). Fixed window [0.45, 0.55] is unrealistic for lopsided states. | P | Solve for the logit shift hitting each statewide target (bisection; cf. Rosenman–McCartan–Olivella logit shift); use state-specific windows. |
| F11 | Medium | §13–14 | ALARM standard files use 2016–2020 statewide elections; a 2024 baseline requires separate data (Atlas uses Kenny 2026 VTD-projected 2024 presidential returns). | V | Specify baseline data provenance. |
| F12 | Medium | §6–10 | Ensemble dependence of every ensemble-relative quantity is large: in the toy, asymmetry $A$ flips sign; argmax-$G$ map favors D under two ensembles and R under the third; argmin-$G$ plan differs under all three; Spearman($G$) across ensembles 0.55–0.97. | T (C6) | Treat ensemble choice as a first-class sensitivity axis, not a robustness appendix. |
| F13 | Low | §34 | Finite-sample optimism of in-sample $G^{\min}$: correct in sign; small in the toy (mean +0.0009, 66% of runs positive, N=100). | T (C7) | Keep the three-ensemble split rule; it is cheap. |
| F14 | Low | refs | Links carry `utm_source=chatgpt.com`; some venues unverified (Public Choice moving-knife; La Matematica venue of Ratliff et al.; DOJ §2 guidance status post-*Callais*). | V/U | Clean links; verify or drop. |

---

## 2. Mathematical audit (proofs + toy evidence)

Notation follows the document: $S_M(v)$ = seats for party D under plan $M$ at statewide environment $v$; $\mu(v)=\mathbb E_{Q\sim\Pi}[S_Q(v)]$; $n$ = number of districts.

### 2.1 §6 degeneracy — **correct** (P, T)
- $\Gamma(M)=\mathbb E_\theta[(S_M(\theta)-\mu(\theta))/n]=\mathbb E_\theta[S_M]/n - \text{const}$, so $\arg\max\Gamma=\arg\max \mathbb E_\theta[S_M]$.
- Toy check C1: holds under all 3 ensembles × 2 seat models.

### 2.2 The same degeneracy kills §12 and §27 — **doc error** (P, T)
- **Lemma 1.** For any ensemble $\Pi$: $U(v)-L(v)=\max_M S_M(v)-\min_M S_M(v)$, and $W=D^+-D^-=(\max_M \bar S_M-\min_M \bar S_M)/n$ with $\bar S_M=\mathbb E_\theta S_M$.
- *Proof.* $\mu(v)$ is constant in $M$, so it cancels in $\max_M(S_M-\mu)-\min_M(S_M-\mu)$. ∎
- Consequences:
  - The "ensemble-relative feasible envelope" width is exactly the feasible seat range (Fairmandering reports this per state; national headline: expected Democratic House share movable from 43% to 62% using natural districts).
  - Only the **location** of the interval relative to $\mu$ (i.e., $A=D^++D^-$) is ensemble-relative — and that is the quantity shown to be ensemble-fragile (F12).
  - $U(v)$ is attained by different maps at different $v$; it is a pointwise envelope, not a map. The doc never says so.
- Toy check C2: widths identical across uniform / spanning-tree / cut-edge-tilted ensembles.

### 2.3 $G$ mixes bias and responsiveness — **doc mislabel** (P, T)
- Let $d(v)=(S_M(v)-\mu(v))/n$ on window $\mathcal V$ with weight $w$. Take $w$-orthonormal polynomials $\phi_0=1,\ \phi_1\propto (v-\bar v)$. Then exactly
  $G^2=\|d\|_w^2=b^2+r^2+e^2$, with $b=\langle d,\phi_0\rangle$ (bias = the doc's $D$), $r=\langle d,\phi_1\rangle$ (responsiveness deviation), $e$ = residual.
- So $C=|D|/G=|b|/\sqrt{b^2+r^2+e^2}$; the doc's $C$ is a symptom indicator, not a decomposition.
- The doc's example $(+2,+2,-2,-2)$: if the $+2$ values occur on one side of the environment range and $-2$ on the other, the map is **more (or less) responsive** than the ensemble — a bipartisan/incumbent-protection or competitiveness effect, not a partisan one.
- Toy check C5b (deterministic, uniform ensemble):
  - highest-$G$ map with $C<0.25$: $G=0.117$, **94.5th percentile** of $G$, bias $\Gamma=-0.011$, slope +1.20 seat-share per unit vote-share above the ensemble mean slope;
  - 57% of top-decile-$G$ maps have $C<0.5$;
  - corr($G$, |slope deviation|) = 0.46.
- Fix: report $(b,r,e)$ separately; if a single scalar is wanted for "partisan distortion", use $b$ (and it degenerates to seat maximization, per §6).

### 2.4 Neutrality floor = integrality floor — **doc error** (P, T)
- Under uniform additive swing and deterministic seat counting, each district share increases with $v$, so every feasible $S_M(\cdot)$ is a **non-decreasing integer step function** with values in $\{0,\dots,n\}$.
- **Lemma 2.** $G^{\min}\ \ge\ L_{\text{int}}:=\frac1n\min_{f\in\mathcal F_\uparrow}\|f-\mu\|_w$, where $\mathcal F_\uparrow$ = non-decreasing integer step functions. $L_{\text{int}}$ is computable in $O(Tn^2)$ by dynamic programming (implemented: `integrality_floor()` in `code/qc_checks.py`).
- *Proof.* The feasible curves are a subset of $\mathcal F_\uparrow$. ∎
- Interpretation: $L_{\text{int}}>0$ whenever $\mu(v)$ is non-integer (almost always, since $\mu$ is an average). A state can have large $G^{\min}$ purely because its ensemble-mean curve sits near half-integers — nothing to do with geography.
- Toy check C4 (deterministic seats): $G^{\min}/L_{\text{int}}$ = **1.000** (uniform), **1.0016** (spanning-tree), **1.000** (cut-edge tilt); number of tied minimizing maps: 27, 7, 27. The "least-distorted map" is neither informative nor unique.
- Probabilistic seats remove the rounding but make the floor small: $G^{\min}$ = 0.008–0.014 vs $G^{\max}$ ≈ 0.10–0.11 (toy).
- Normative issue (not fixable by math): the ensemble mean is **sampler-relative**, and ensembles inherit geography-driven bias (Kenny et al. 2023 attribute a moderate pro-Republican bias to geography and rules; Kenny 2026 argues this advantage largely disappeared by 2024 — itself evidence that "neutral" baselines move). Matching $\mu$ is not "fair" by any standard the doc defines.
- Prior art for "distance to ensemble center": Duke Gerrymandering Index (L² distance of ordered district vote shares to the ensemble mean; Herschlag et al. 2020); Gonatas (arXiv 2103.01735) explicitly compares selecting plans near ensemble means vs low efficiency gap.

### 2.5 Units in §16 — **doc error, minor** (P)
- "θ in percentage points … shift consistently in logit space": a constant logit shift $\lambda$ produces statewide change $\sum_i T_i[\sigma(\ell_i+\lambda)-\sigma(\ell_i)]/\sum_i T_i$, which varies with the precinct distribution. Solve for $\lambda(v)$ by bisection per target $v$.

### 2.6 §23 optimization structure — **doc omission** (P)
- With scenario grid $\Theta$: $G^2(x)=\frac1{|\Theta|}\sum_\theta\big(\sum_j x_j s_j(\theta)-\mu(\theta)\big)^2/n^2$ — a convex quadratic in the column-selection vector $x$. Minimization = convex MIQP; maximization = non-convex MIQP. Neither is the LP-priced master problem implied.
- Column-generation bounds certify optimality only if pricing (find the connected, population-balanced district of best reduced cost) is solved exactly; Fravel et al. (2026) note that Fairmandering provides no dual bounds.

### 2.7 Ensemble sensitivity (T, check C6)
| Quantity (deterministic seats) | uniform | spanning-tree (ReCom/SMC-like) | cut-edge tilt β=1 |
|---|---|---|---|
| $A=D^++D^-$ | **−0.035** | **+0.022** | **+0.006** |
| $\Gamma$ of argmax-$G$ map | **−0.084** (R-favoring) | **+0.096** (D-favoring) | **+0.088** (D-favoring) |
| argmin-$G$ plan id | 811 | 1425 | 670 |
| $W=D^+-D^-$ | 0.1818 | 0.1818 | 0.1818 |

Spearman correlation of $G$ across ensembles: 0.56 / 0.76 / 0.96 (det.); 0.55 / 0.72 / 0.97 (prob.).

### 2.8 Correct claims confirmed
- $0\le C\le 1$ (Cauchy–Schwarz) — C3 pass.
- $G=0$ iff $S_M=\mu$ $w$-a.e. — definitional.
- Short bursts give lower bounds only (§22) — correct and also stated by the Atlas itself.
- Separate baseline / optimization / validation ensembles (§34) — correct; optimism quantified small but positive (C7).

---

## 3. Citation audit

Legend: ✅ verified this session · ⚠️ verified with correction · ❓ not verified.

| Doc ref | Claim in doc | Status | Note |
|---|---|---|---|
| [2] ALARM FAQ | 5,000 plans/state; code, data, constraints | ✅ | Also: pop. deviation ≤0.5%; VRA constraint targets enacted count of opportunity districts; elections averaged 2016–2020. |
| [3] redist | SMC, MCMC, merge-split | ✅ | redist 4.3.2 docs. |
| [4] McCartan & Imai SMC (AOAS) | balanced compact sampling | ✅ | |
| [5] arXiv 1911.05725 | "ReCom/merge-split" | ❓ (not re-checked) | ReCom (DeFord–Duchin–Solomon) ≠ merge-split (Carter et al.; Autry et al. 2021); conflated. |
| [6] Cannon et al. MCAP 2023 | short bursts | ✅ | Authors: Cannon, Goldbloom-Helzner, Gupta, Matthews, Suwal. |
| [7] `redist_shortburst()` | arbitrary score fn; merge-split backend | ✅ | Also supports vector scores / Pareto output. |
| [8] Define–Combine (PA 2024) | short bursts for extreme maps | ✅ | Confirmed by Palmer–Schneer 2026 text; uses a smoothed score, not raw seats. |
| [9] LSQ 2024 | "Goedert and Pierson" | ⚠️ | Goedert, Hildebrand, Travis, Pierson; LSQ 49(3):551–583. ">100 seats nationally" swing; little compactness tradeoff ✅. "Probabilistic approach incl. national uncertainty": ❓ (CPVI-probit district model confirmed via Fravel et al.; national-uncertainty part not verified). |
| [10] Atlas methodology | Max 50%, Safe Max 55% | ⚠️ | Max = **51%**, Safe Max = 55%; both prototypes; no global-optimum guarantee. Atlas also has a **2026 enacted layer** (CA, FL, LA, MO, NC, OH, TN, TX, UT) — omitted by doc. |
| [11]/[22] Fairmandering | seat range, CG | ✅ | 43%→62% Democratic House share with natural districts. Heuristic; no dual bounds. |
| [12] HSS Comms 2021 | minimize partisan bias | ✅ (existence) | |
| [13] Public Choice moving-knife | | ❓ | Not verified. |
| [14] Palmer & Schneer AJPS 2026 | durable majority gerrymanders | ✅ | Early View Aug 2026; state legislatures. |
| [15] Econometrica 2026 | "Kolotilin's paper" | ⚠️ | **Kolotilin & Wolitzky**, 94(1):71–103. Finds idiosyncratic uncertainty dominates in practice. |
| [16]/[17] Census PL 94-171 / TIGER | | ❓ (standard; not re-checked) | |
| [18] Atlas data | 2008–2024 baselines | ✅ | 2024 baseline from Kenny (2026) VTD-projected returns. |
| [19] Imai MCMC page | graph partition framing | ❓ | Uncontroversial. |
| [20] DOJ §2 guidance | VRA compliance | ❓ | Status post-*Callais* unverified; likely superseded in part. |
| [21] Ratliff–Somersille–Veomett | metrics gameable | ✅ (arXiv 2409.17186) | Venue "La Matematica" not verified. |
| [23] arXiv 2102.09889 | hardness | ❓ (not re-checked) | |
| [24] Barber–Taylor–Trende ELJ 2026 | durability skepticism | ✅ (existence, abstract) | |
| [25] Duke ensemble guidance | | ❓ | |
| [26] ALARM 50-state | not legal determinations | ✅ | |

---

## 4. Currency audit — what the "through September 2026" review missed (all ✅)

- ***Louisiana v. Callais*, No. 24-109, decided 2026-04-29 (6–3):** held Louisiana's second majority-Black district an unconstitutional racial gerrymander and significantly narrowed §2 vote-dilution claims (CRS LSB11431). Directly changes $\Omega_s$ in Southern states.
- **2025–26 mid-decade wave:** new maps in CA, MO, NC, OH, TX, UT (by Feb 2026, Ballotpedia), then FL and TN post-*Callais*; Louisiana redrew after *Callais*; Alabama legislated a contingent redraw. Virginia's referendum map was struck by its supreme court. Missouri's map faces a veto referendum on the Nov 3, 2026 ballot (secondary sources; verify before use).
- **Kenny et al., PNAS 2023:** national ensemble-relative House bias with an election model; partisan bias mostly cancels (~2 seats to R), geography/rules add moderate R bias, gerrymandering reduces responsiveness — the doc's framework minus optimization.
- **Fravel et al., MMOR 2026:** dual bounds for expected partisan and Black representation (probit objectives) with exact contiguity, county-level data, relaxed population tolerance.
- **Kenny 2026 (SocArXiv):** Republican geographic advantage largely disappeared by 2024 (title-level; content not read) — undercuts any "fixed geography" framing of $G^{\min}$ and bears on temporal analyses (§29).

---

## 5. Section-by-section notes (compact)

- **§1** ✅ state-by-state structure; add: 44 multi-district states; 2-district states have tiny objective ranges.
- **§2–4** ✅ with corrections F9; add Swamy–King–Jacobson 2023, Validi–Buchanan 2022.
- **§5** F8. Add Owen–Grofman 1988, Friedman–Holden 2008, Lagarde–Tomala 2021.
- **§6** ✅ correct and valuable.
- **§7** F4 — example misinterpreted.
- **§8** ✅ definitions; C bound correct.
- **§9** "Gerrymanderability $=G^{\max}$" mislabeled (F4); $G^{\max}$ also ensemble-fragile (F12).
- **§10** F2 — headline claim fails.
- **§11** functional metric fine; swing model and window unspecified (F10).
- **§12** F1.
- **§13–14** mostly fine; F11; also note census differential-privacy noise at small geographies.
- **§15** standard hierarchical logit; turnout $T_{it}$ must itself be forecast for future elections.
- **§16** F10.
- **§17** VTD-level 0.5% tolerance ≠ enactable plans (real plans balance at block level); state the assumption.
- **§18** F3.
- **§19–21** ✅.
- **§22** ✅ important and correct.
- **§23** F7.
- **§24–25** ✅ reasonable (GNN/RL skepticism sound).
- **§26–27** F1; $A_s$ is the only ensemble-relative part and is fragile (F12).
- **§28** depends on $G^{\min}$ → inherits F2.
- **§29** reasonable; must hold statewide share fixed (normalize by swing) to separate sorting from level; Kenny 2026 adjacent.
- **§30–31** ✅ good ideas; the 2026 midterm is a real out-of-sample test (time-critical).
- **§32** F5; also note a trivial certificate already exists for $G^{\min}$ (Lemma 2).
- **§33** ✅ positioned correctly; add DeFord–Veomett "Bounds and Bugs".
- **§34–36** ✅.
- **§37–38** ✅ sensible pipeline.
- **§39** the "stronger result" is built on F1/F2 constructs.
- **§40** ratings corrected below.
- **QC log** claims a September-2026 literature check but misses F3/F6 items → incomplete.

---

## 6. Corrected novelty table (replaces doc §40)

| Contribution | Doc rating | Corrected rating | Reason |
|---|---|---|---|
| Seat-maximizing House maps | Low | Low | agree |
| Ensemble-relative feasible envelope | Moderate–high | **Low** | width is ensemble-free (F1) |
| Neutrality floor $G^{\min}$ | High | **Low** | integrality artifact + normative + prior art (F2) |
| $G$ as partisan distortion | (implicit high) | **Low–moderate** | needs bias/responsiveness decomposition (F4) |
| Optimality certificates / bounds | High | **High, but must be precinct-valid and positioned vs Fravel et al. 2026** | F5 |
| Out-of-sample durability | Moderate–high | **High if preregistered on the 2026 midterm; moderate otherwise** | time-critical |
| Ensemble-definition sensitivity | High (method) | **Moderate–high** | toy shows sign flips (F12); literature cautions exist |
| Temporal gerrymanderability | Potentially high | **Moderate** | Atlas baselines + Kenny 2026 adjacent |
| Post-*Callais* constraint-regime effects | (absent) | **High** | not in doc; policy-critical |

---

## 7. What survives
1. Upper-bound certification of seat extrema (with a precinct-valid relaxation — see DIRECTION.md).
2. Margin/durability as a first-class axis (the Atlas's Max vs Safe Max are two lower-bound points of one curve).
3. Out-of-sample testing using the 2026 midterm.
4. Ensemble-choice sensitivity as a mandatory axis.
5. Using ALARM + `redist` + short bursts for lower bounds (sound engineering advice).

---

## 8. Reproducibility of the toy evidence
- `code/qc_checks.py` (C0–C8), `code/qc_checks_iter2.py` (C5b, C8b), `code/qc_checks_iter3.py` (adaptive refinement). Outputs in `results/*.json`.
- Toy state: 5×5 grid, equal populations, 5 districts of 5 precincts; D shares fixed in code (statewide 0.4732). Enumeration count **4006** (matches the known count) — gate passed.
- Limits: a toy cannot establish magnitudes for real states; it establishes that the claimed properties fail in a legitimate instance (counterexamples) and that Lemmas 1–2 hold.
