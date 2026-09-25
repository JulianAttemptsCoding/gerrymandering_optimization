#!/usr/bin/env python3
"""
QC harness for the audit of "Extremal gerrymandering / neutrality floor" research plan.

Everything here is EXACT on a toy state: a 5x5 grid of equal-population precincts
partitioned into 5 contiguous districts of 5 precincts each. All such plans are
enumerated (known count: 4006), so no sampling error enters any claim below
except where sampling is the object of study (check C7).

Checks (each prints PASS/FAIL or a measured quantity):
  C0  enumeration count == 4006 (known value for 5x5 -> 5 x pentomino districts)
  C1  argmax Gamma == argmax E[seats]            (doc Sec.6 degeneracy; doc is RIGHT)
  C2  envelope width U(v)-L(v) is ensemble-free  (doc Sec.12/27 claim of ensemble-relative
                                                  novelty is WRONG: width = plain seat range)
  C3  0 <= C <= 1                                (doc Sec.8; RIGHT)
  C4  integrality floor: G_min >= L_int > 0 for deterministic seats; ratio G_min/L_int
                                                 (doc Sec.10 "neutrality floor" is largely
                                                  a rounding artifact)
  C5  what does argmax G look like? (bias vs responsiveness)  (doc Sec.9 mislabel)
  C6  ensemble sensitivity: G rankings / argmin plan under 3 reasonable ensembles
  C7  finite-sample optimism of in-sample G_min (doc Sec.34; RIGHT, quantified)
  C8  certification hierarchy on seat max at margin m:
        exact <= county-support relaxation <= precinct-integer no-contiguity <= fractional
      (validity of the relaxation proposed in DIRECTION.md)

Run:  python3 qc_checks.py            (writes ../results/qc_results.json and prints a report)
Deps: numpy, scipy>=1.9 (scipy.optimize.milp / HiGHS), networkx
"""
import itertools, json, math, os, sys, time
import numpy as np
import networkx as nx
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.stats import norm, spearmanr

RNG = np.random.default_rng(20260923)
N_ROWS = N_COLS = 5
K = 5            # districts
SZ = 5           # precincts per district (equal population => exact balance)
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
os.makedirs(OUT_DIR, exist_ok=True)

# ------------------------------------------------------------------ geography
def cell(r, c): return r * N_COLS + c
G = nx.grid_2d_graph(N_ROWS, N_COLS)
G = nx.relabel_nodes(G, {(r, c): cell(r, c) for r, c in G.nodes})
NBR = {v: set(G.neighbors(v)) for v in G.nodes}
ROW = {cell(r, c): r for r in range(N_ROWS) for c in range(N_COLS)}

# Democratic two-party share per precinct: urban corner (D), rural remainder (R).
P = np.array([
    [.80, .75, .60, .45, .40],
    [.72, .62, .50, .42, .38],
    [.58, .50, .44, .40, .36],
    [.46, .43, .40, .37, .35],
    [.42, .40, .38, .36, .34],
]).reshape(-1)
V0 = P.mean()

# ------------------------------------------------------------------ enumeration
def connected_sets_containing(seed, allowed, size):
    """All connected subsets of `allowed` of given size containing `seed`."""
    found = set()
    def grow(cur, frontier):
        if len(cur) == size:
            found.add(frozenset(cur)); return
        for v in list(frontier):
            new = cur | {v}
            key = frozenset(new)
            if key in seen: continue
            seen.add(key)
            grow(new, (frontier | (NBR[v] & allowed)) - new)
    seen = {frozenset([seed])}
    grow({seed}, NBR[seed] & allowed)
    return found

def comps_ok(unassigned):
    sub = G.subgraph(unassigned)
    return all(len(c) % SZ == 0 for c in nx.connected_components(sub))

def enumerate_plans():
    plans = []
    def rec(unassigned, districts):
        if not unassigned:
            plans.append(tuple(sorted(tuple(sorted(d)) for d in districts))); return
        s = min(unassigned)
        for dset in connected_sets_containing(s, unassigned, SZ):
            rest = unassigned - dset
            if rest and not comps_ok(rest): continue
            rec(rest, districts + [dset])
    rec(frozenset(G.nodes), [])
    return sorted(set(plans))

# ------------------------------------------------------------------ plan features
THETAS = np.round(np.linspace(-0.08, 0.08, 33), 4)   # uniform additive swing grid
V_GRID = V0 + THETAS                                  # statewide D share (no clipping occurs)
SIGMA_D = 0.03                                        # district-level noise for probabilistic seats

def district_shares(plan):
    return np.array([P[list(d)].mean() for d in plan])

def seat_curves(plan):
    sh = district_shares(plan)[None, :] + THETAS[:, None]         # (T, K)
    det = (sh > 0.5).sum(axis=1).astype(float)
    prob = norm.cdf((sh - 0.5) / SIGMA_D).sum(axis=1)
    return det, prob

def n_spanning_trees(nodes):
    sub = G.subgraph(nodes)
    L = nx.laplacian_matrix(sub).toarray().astype(float)
    return round(np.linalg.det(L[1:, 1:]))

def cut_edges(plan):
    lab = {}
    for j, d in enumerate(plan):
        for v in d: lab[v] = j
    return sum(1 for u, v in G.edges if lab[u] != lab[v])

# ------------------------------------------------------------------ integrality floor
def integrality_floor(mu, n, w=None):
    """min over nondecreasing integer step functions f in {0..n} of sqrt(mean w (f-mu)^2)/n.
    Every deterministic uniform-swing seat curve S_M(v) is such a function, so this is a
    certified lower bound on G_min that needs no optimization over maps."""
    T = len(mu); w = np.ones(T) / T if w is None else w
    INF = 1e18
    dp = np.full((T, n + 1), INF)
    for s in range(n + 1): dp[0, s] = w[0] * (s - mu[0]) ** 2
    for t in range(1, T):
        best = np.minimum.accumulate(dp[t - 1])          # min over s' <= s
        for s in range(n + 1): dp[t, s] = best[s] + w[t] * (s - mu[t]) ** 2
    return math.sqrt(dp[-1].min()) / n

def pointwise_floor(mu, n):
    return math.sqrt(np.mean((mu - np.round(mu)) ** 2)) / n

# ------------------------------------------------------------------ certification MILPs
def seat_max_milp(m, mode):
    """Max # districts with D share >= 0.5+m at theta=0.
    mode: 'frac'   fractional precincts, no contiguity (geography-free relaxation)
          'int'    integer precincts, no contiguity
          'rows'   fractional precincts + county(row)-support binaries + interval contiguity
                   on the county graph (a path) -> valid relaxation of contiguous plans."""
    nP = len(P); idx = {}
    def add(name):
        idx[name] = len(idx); return idx[name]
    for i in range(nP):
        for j in range(K): add(("x", i, j))
    for j in range(K): add(("w", j))
    if mode == "rows":
        for r in range(N_ROWS):
            for j in range(K): add(("y", r, j))
    nv = len(idx); c = np.zeros(nv)
    for j in range(K): c[idx[("w", j)]] = -1.0
    A, lo, hi = [], [], []
    def row(coefs, l, h):
        a = np.zeros(nv)
        for k, v in coefs.items(): a[k] += v
        A.append(a); lo.append(l); hi.append(h)
    for i in range(nP):
        row({idx[("x", i, j)]: 1 for j in range(K)}, 1, 1)
    for j in range(K):
        row({idx[("x", i, j)]: 1 for i in range(nP)}, SZ, SZ)
        # sum_i (p_i - 0.5 - m) x_ij >= -Mbig (1 - w_j) + eps*w_j
        Mbig = SZ * 1.0; eps = 1e-6
        coefs = {idx[("x", i, j)]: (P[i] - 0.5 - m) for i in range(nP)}
        coefs[idx[("w", j)]] = -(Mbig + eps)
        row(coefs, -Mbig, np.inf)
    for j in range(K - 1):  # symmetry breaking: winners first
        row({idx[("w", j)]: 1, idx[("w", j + 1)]: -1}, 0, np.inf)
    if mode == "rows":
        for i in range(nP):
            for j in range(K):
                row({idx[("x", i, j)]: 1, idx[("y", ROW[i], j)]: -1}, -np.inf, 0)
        for j in range(K):
            for a, b, cc in itertools.combinations(range(N_ROWS), 3):
                row({idx[("y", a, j)]: 1, idx[("y", cc, j)]: 1, idx[("y", b, j)]: -1}, -np.inf, 1)
    integrality = np.zeros(nv)
    for j in range(K): integrality[idx[("w", j)]] = 1
    if mode == "int":
        for i in range(nP):
            for j in range(K): integrality[idx[("x", i, j)]] = 1
    if mode == "rows":
        for r in range(N_ROWS):
            for j in range(K): integrality[idx[("y", r, j)]] = 1
    res = milp(c, constraints=LinearConstraint(np.array(A), lo, hi),
               integrality=integrality, bounds=Bounds(0, 1),
               options={"time_limit": 120, "mip_rel_gap": 0})
    if res.status != 0:
        return {"status": int(res.status), "msg": res.message, "value": None}
    return {"status": 0, "value": int(round(-res.fun)), "dual_bound": float(-res.mip_dual_bound)
            if getattr(res, "mip_dual_bound", None) is not None else None}

# ------------------------------------------------------------------ main
def main():
    t0 = time.time(); R = {"meta": {"V0": V0, "thetas": THETAS.tolist(), "sigma_d": SIGMA_D}}
    plans = enumerate_plans()
    n_pl = len(plans)
    R["C0_enumeration_count"] = n_pl
    print(f"[C0] plans enumerated: {n_pl}  -> {'PASS' if n_pl == 4006 else 'FAIL (expected 4006)'}")

    DET = np.zeros((n_pl, len(THETAS))); PROB = np.zeros_like(DET)
    tau = np.zeros(n_pl); cuts = np.zeros(n_pl)
    for k, pl in enumerate(plans):
        DET[k], PROB[k] = seat_curves(pl)
        tau[k] = np.prod([n_spanning_trees(d) for d in pl])
        cuts[k] = cut_edges(pl)
    ens = {
        "uniform": np.ones(n_pl) / n_pl,
        "spanning_tree(ReCom/SMC-like)": tau / tau.sum(),
        "cut_edge_tilt(beta=1)": np.exp(-1.0 * (cuts - cuts.min())) / np.exp(-1.0 * (cuts - cuts.min())).sum(),
    }
    R["ensembles"] = {}
    for curve_name, S in [("deterministic", DET), ("probabilistic", PROB)]:
        R["ensembles"][curve_name] = {}
        widths = {}
        Gs = {}
        for ename, wts in ens.items():
            mu = wts @ S
            delta = (S - mu[None, :]) / K
            Gam = delta.mean(axis=1); Gm = np.sqrt((delta ** 2).mean(axis=1))
            Cc = np.where(Gm > 0, np.abs(Gam) / np.where(Gm > 0, Gm, 1), 0.0)
            # C1
            c1 = int(np.argmax(Gam)) in set(np.flatnonzero(S.mean(axis=1) == S.mean(axis=1).max()))
            # C2
            U = (S - mu).max(axis=0); L = (S - mu).min(axis=0); widths[ename] = (U - L)
            # C3
            c3 = bool(np.all((Cc >= -1e-12) & (Cc <= 1 + 1e-12)))
            # C4
            gmin_i = int(np.argmin(Gm)); gmax_i = int(np.argmax(Gm))
            floor_mono = integrality_floor(mu, K) if curve_name == "deterministic" else None
            floor_pt = pointwise_floor(mu, K) if curve_name == "deterministic" else None
            # C5: decompose argmax-G plan deviation d(v)=S_M-mu into bias (mean) and slope
            d = (S[gmax_i] - mu) / K
            slope_plan = np.polyfit(V_GRID, S[gmax_i] / K, 1)[0]
            slope_mu = np.polyfit(V_GRID, mu / K, 1)[0]
            Gs[ename] = Gm
            R["ensembles"][curve_name][ename] = {
                "C1_argmaxGamma_is_argmaxMeanSeats": c1,
                "C3_C_in_[0,1]": c3,
                "Gmin": float(Gm[gmin_i]), "Gmin_plan": gmin_i,
                "Gmax": float(Gm[gmax_i]), "Gmax_plan": gmax_i,
                "Gmax_plan_Gamma": float(Gam[gmax_i]), "Gmax_plan_C": float(Cc[gmax_i]),
                "Gmax_plan_slope_seatshare_per_vote": float(slope_plan),
                "ensemble_mean_slope": float(slope_mu),
                "D_plus": float(Gam.max()), "D_minus": float(Gam.min()),
                "W=D+ - D-": float(Gam.max() - Gam.min()),
                "A=D+ + D-": float(Gam.max() + Gam.min()),
                "L_int_monotone": floor_mono, "L_int_pointwise": floor_pt,
                "Gmin_over_L_int": (float(Gm[gmin_i] / floor_mono) if floor_mono else None),
                "n_plans_at_Gmin": int(np.sum(np.isclose(Gm, Gm[gmin_i]))),
            }
        # C2: widths identical across ensembles
        wlist = list(widths.values())
        c2 = all(np.allclose(wlist[0], w) for w in wlist[1:])
        R["ensembles"][curve_name]["C2_envelope_width_ensemble_free"] = c2
        # C6: rank stability of G across ensembles
        names = list(Gs)
        rho = {f"{a} vs {b}": float(spearmanr(Gs[a], Gs[b]).correlation)
               for a, b in itertools.combinations(names, 2)}
        argmins = {nm: int(np.argmin(Gs[nm])) for nm in names}
        R["ensembles"][curve_name]["C6_spearman_G"] = rho
        R["ensembles"][curve_name]["C6_argmin_plans"] = argmins
        R["ensembles"][curve_name]["C6_argmin_same_across_ensembles"] = len(set(argmins.values())) == 1

    # C7: finite-sample optimism (uniform ensemble, deterministic seats)
    mu_true = ens["uniform"] @ DET
    Gtrue = np.sqrt((((DET - mu_true) / K) ** 2).mean(axis=1))
    opt = []
    for _ in range(300):
        idxs = RNG.choice(n_pl, size=100, replace=True)
        mu_hat = DET[idxs].mean(axis=0)
        G_in = np.sqrt((((DET[idxs] - mu_hat) / K) ** 2).mean(axis=1))
        b = int(np.argmin(G_in))
        opt.append(Gtrue[idxs[b]] - G_in[b])
    R["C7_insample_optimism"] = {"mean": float(np.mean(opt)), "sd": float(np.std(opt)),
                                 "frac_positive": float(np.mean(np.array(opt) > 0))}

    # C8: certification hierarchy at theta=0
    sh0 = np.array([district_shares(pl) for pl in plans])
    R["C8"] = {}
    for m in [0.0, 0.02, 0.05, 0.08]:
        exact = int((sh0 >= 0.5 + m + 1e-12).sum(axis=1).max()) if m > 0 else int((sh0 > 0.5).sum(axis=1).max())
        rows = seat_max_milp(m, "rows"); integ = seat_max_milp(m, "int"); frac = seat_max_milp(m, "frac")
        ok = all(x["value"] is not None for x in (rows, integ, frac)) and \
             exact <= rows["value"] <= frac["value"] and exact <= integ["value"] <= frac["value"]
        R["C8"][f"m={m}"] = {"exact": exact, "rows_relax": rows["value"], "int_nocontig": integ["value"],
                             "frac_nocontig": frac["value"], "hierarchy_valid": bool(ok)}
    R["runtime_sec"] = round(time.time() - t0, 1)
    with open(os.path.join(OUT_DIR, "qc_results.json"), "w") as f:
        json.dump(R, f, indent=2, default=float)
    print(json.dumps(R, indent=2, default=float))

if __name__ == "__main__":
    main()
