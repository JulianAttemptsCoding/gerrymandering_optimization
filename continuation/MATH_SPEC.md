# Mathematical specification

## 1. Atomic districting model

Fix a state. Let
\[
G=(V,E)
\]
be the adjacency graph of the atomic geographic units. The intended limiting atomic units are Census blocks, although pilot instances may use tracts, block groups, or VTD-like units if the paper clearly states the model resolution.

Let:
- \(k\): number of congressional districts;
- \(p_i\ge0\): Census population of atom \(i\);
- \(D_{i\omega},R_{i\omega}\ge0\): two-party vote masses under electoral scenario \(\omega\in\Omega\);
- \(a_i\in\mathbb R_+^q\): optional vector of other additive attributes.

A plan \(M=(V_1,\dots,V_k)\) is feasible under encoded regime \(\rho\) if:
1. \(V_1,\dots,V_k\) partition \(V\);
2. each \(G[V_j]\) is connected;
3. each district satisfies
   \[
   L\le \sum_{i\in V_j}p_i\le U;
   \]
4. it satisfies every other explicitly encoded constraint in \(\rho\).

No claim of legal validity follows merely from satisfying \(\rho\).

## 2. Robust partisan margin

For generic party label \(\pi\), write \(P_{i\omega}\) for that party's vote and \(O_{i\omega}\) for the other major party's vote.

\[
v^\pi_j(M,\omega)
=
\frac{\sum_{i\in V_j}P_{i\omega}}
{\sum_{i\in V_j}(P_{i\omega}+O_{i\omega})}.
\]

Define
\[
r^\pi_j(M)
=
\min_{\omega\in\Omega}
\left(
v^\pi_j(M,\omega)-\frac12
\right).
\]

## 3. Seat–safety frontier

\[
F_{\pi,\rho,\Omega}(m)
=
\max_{M\in\mathcal M^\rho}
\sum_{j=1}^k
\mathbf 1\{r^\pi_j(M)\ge m\}.
\]

### Proposition 1 — margin monotonicity
If \(m_1\le m_2\), then
\[
F(m_1)\ge F(m_2).
\]

### Proposition 2 — uncertainty monotonicity
If \(\Omega_1\subseteq\Omega_2\), then
\[
F_{\Omega_1}(m)\ge F_{\Omega_2}(m).
\]

### Proposition 3 — constraint monotonicity
If \(\mathcal M^{\rho_2}\subseteq\mathcal M^{\rho_1}\), then
\[
F_{\rho_1}(m)\ge F_{\rho_2}(m).
\]

## 4. Seat–safety spectrum

Sort
\[
r^\pi_{(1)}(M)\ge\dots\ge r^\pi_{(k)}(M).
\]

Define
\[
\sigma^*(q)=\max_{M\in\mathcal M^\rho}r^\pi_{(q)}(M).
\]

### Theorem 1 — generalized inverse
\[
F(m)=\max\{q\in\{0,\dots,k\}:\sigma^*(q)\ge m\}.
\]

**Proof sketch.**
\(F(m)\ge q\) iff some feasible plan has at least \(q\) robust margins at least \(m\), iff some plan's \(q\)-th order statistic is at least \(m\), iff \(\sigma^*(q)\ge m\). \(\square\)

### Corollary 1 — layer-cake identity
\[
\int_0^{1/2}F(m)\,dm
=
\sum_{q=1}^k[\sigma^*(q)]_+.
\]

This is a structural capacity summary, not a normative fairness score.

## 5. Fixed-margin MILP

For fixed \(m\), let
\[
c_{i\omega}^{\pi}(m)
=
\left(\frac12-m\right)P_{i\omega}
-
\left(\frac12+m\right)O_{i\omega}.
\]

Then
\[
v^\pi_j(M,\omega)\ge \frac12+m
\]
iff
\[
\sum_i c_{i\omega}^{\pi}(m)x_{ij}\ge0.
\]

Variables:
\[
x_{ij}\in\{0,1\},\qquad w_j\in\{0,1\}.
\]

Assignment:
\[
\sum_jx_{ij}=1.
\]

Population:
\[
L\le\sum_ip_ix_{ij}\le U.
\]

Safety implication:
\[
\sum_i c_{i\omega}^{\pi}(m)x_{ij}
\ge
-M_\omega(m)(1-w_j)
\quad \forall j,\omega.
\]

A safe generic value is
\[
M_\omega(m)
=
\left(\frac12+m\right)\sum_iO_{i\omega},
\]
but tighter district-level bounds should be used.

Contiguity must be imposed by an exact formulation for final certification.

Objective:
\[
\max\sum_jw_j.
\]

## 6. National decomposition

If state map choices are independent and the objective is additive:
\[
F_{\mathrm{US}}(m)=\sum_sF_s(m).
\]

This follows from
\[
\max_{(M_s)_s\in\prod_s\mathcal M_s}\sum_sf_s(M_s)
=
\sum_s\max_{M_s\in\mathcal M_s}f_s(M_s).
\]

# Part II — certifying upper bounds

## 7. Coarse partition and local allocation polytope

Let
\[
\mathcal P=\{C_1,\dots,C_h\}
\]
partition atomic units.

For cell \(C\), define the exact \(k\)-way aggregate-allocation set
\[
\mathcal Z_C^k
=
\left\{
(z_{C1},\dots,z_{Ck}):
C=A_1\sqcup\dots\sqcup A_k,\;
z_{Cj}=\sum_{i\in A_j}a_i
\right\}.
\]

Let
\[
\mathcal H_C^k=\operatorname{conv}(\mathcal Z_C^k).
\]

Use a tractable outer polyhedron
\[
\widehat{\mathcal H}_C^k\supseteq\mathcal H_C^k.
\]

A base relaxation uses only nonnegativity and total conservation:
\[
z_{Cj}\ge0,\qquad \sum_jz_{Cj}=A_C.
\]

## 8. Quotient support

Let \(G/\mathcal P\) be the quotient graph. Let \(y_{Cj}\) indicate that district \(j\) may use cell \(C\).

Link positive allocated population:
\[
p_{Cj}\le P_Cy_{Cj}.
\]

Allowing \(y=1\) with zero allocation is a deliberate outer relaxation.

### Lemma — quotient connectivity
If an exact district is connected in the atomic graph, then the coarse cells it intersects form a connected set in the quotient graph.

## 9. Validity

Let \(\mathcal R(\mathcal P)\) contain:
- local outer allocation sets;
- population constraints;
- aggregate safety constraints;
- quotient connectivity;
- only other conditions known to be necessary for atomic feasibility.

### Theorem 2 — outer validity
Every exact atomic feasible plan embeds in \(\mathcal R(\mathcal P)\).

Therefore
\[
F(m)\le U_{\mathcal P}(m).
\]

## 10. Monotone refinement

If \(\mathcal P'\) refines \(\mathcal P\), require child relaxations to be compatible:
\[
\operatorname{proj}_{C}
\left(
\prod_{\ell}
\widehat{\mathcal H}_{C_\ell}^k
\right)
\subseteq
\widehat{\mathcal H}_{C}^k.
\]

### Theorem 3 — monotone refinement
\[
U_{\mathcal P'}(m)\le U_{\mathcal P}(m).
\]

## 11. Finite convergence

At singleton atomic cells, impose exact binary assignment, exact attribute tying, exact population, exact contiguity, and exact encoded regime.

### Theorem 4 — finite convergence
\[
U_{\mathcal P_{\rm atom}}(m)=F(m).
\]

## 12. Integer certificate

Any verified feasible witness gives
\[
L(m)\le F(m)\le U(m).
\]

If
\[
U(m)<L(m)+1,
\]
then
\[
F(m)=L(m).
\]

# Part III — stronger local cuts

## 13. Population-conditioned fractional-knapsack envelope

For a cell \(C\), atom populations \(p_i>0\), and nonnegative additive attribute \(q_i\), define

\[
\overline\phi_C(x)
=
\max
\left\{
\sum_iq_i\lambda_i:
\sum_ip_i\lambda_i=x,\;
0\le\lambda_i\le1
\right\},
\]

\[
\underline\phi_C(x)
=
\min
\left\{
\sum_iq_i\lambda_i:
\sum_ip_i\lambda_i=x,\;
0\le\lambda_i\le1
\right\}.
\]

These are piecewise-linear fractional-knapsack envelopes.

### Proposition 4 — validity
For any integral subset \(S\subseteq C\),
\[
\underline\phi_C\!\left(\sum_{i\in S}p_i\right)
\le
\sum_{i\in S}q_i
\le
\overline\phi_C\!\left(\sum_{i\in S}p_i\right).
\]

Therefore impose
\[
\underline\phi_C(p_{Cj})
\le q_{Cj}
\le\overline\phi_C(p_{Cj}).
\]

For signed attributes, use support-function upper/lower envelopes directly.

## 14. General local cuts

For vector attributes, add support-function inequalities:
\[
\lambda^\top z_{Cj}\le h_C(\lambda,p_{Cj})
\]
where \(h_C\) is any valid upper support function for fractional/relaxed local allocations.

# Part IV — algorithms

## 15. Spectrum by parametric search

Directly maximizing \(m\) creates products between \(m\) and assigned turnout. Keep \(m\) fixed and exploit monotonicity.

For each target seat count \(q\), bisection on \(m\) estimates/certifies \(\sigma^*(q)\).

## 16. Adaptive refinement

Refinement priority may combine:
- split entropy;
- phantom support;
- near-threshold contribution;
- local envelope slack;
- dual/reduced-cost impact.

Correctness is independent of the priority rule.

## 17. Lower bounds

Use verified feasible maps from:
- short-burst merge-split;
- local boundary search;
- MILP polishing.

The scientific object is always the bracket
\[
L(m)\le F(m)\le U(m).
\]

# Part V — interpretation

Mathematical optimality is conditional on:
- geographic atoms;
- election allocation;
- scenario set;
- encoded constraint regime.

The frontier does not prove intent, legal validity, or normative fairness.
