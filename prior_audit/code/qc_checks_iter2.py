#!/usr/bin/env python3
"""
Iteration-2 QC additions (imports the iteration-1 harness):
  C5b  Can a map score high on G with ~zero directional bias (C small)?  -> responsiveness
       contamination of the doc's "partisan distortion" label.
  C8b  Flow-based contiguity MILP (single-commodity flow, Shirabe-style) on a unit graph.
       (i)  units = precincts, integer x, y==x  -> must reproduce EXACT enumeration optimum
            (validates the formulation; QC gate)
       (ii) units = 9 blocks, fractional x      -> valid relaxation (upper bound)
       (iii)units = precincts, fractional x     -> valid relaxation (upper bound)
       Report the refinement hierarchy: exact <= (iii) <= (ii) <= rows <= geography-free.
"""
import itertools, json, os, time
import numpy as np, networkx as nx
from scipy.optimize import milp, LinearConstraint, Bounds
import qc_checks as Q

def flow_milp(m, units, x_integer, y_equals_x=False, time_limit=300):
    P, K, SZ = Q.P, Q.K, Q.SZ
    nP = len(P)
    unit_of = {}
    for u, cells in enumerate(units):
        for i in cells: unit_of[i] = u
    nU = len(units)
    UG = nx.Graph(); UG.add_nodes_from(range(nU))
    for a, b in Q.G.edges:
        if unit_of[a] != unit_of[b]: UG.add_edge(unit_of[a], unit_of[b])
    arcs = [(a, b) for a, b in UG.edges] + [(b, a) for a, b in UG.edges]
    idx = {}
    def add(k): idx[k] = len(idx)
    for i in range(nP):
        for j in range(K): add(("x", i, j))
    for j in range(K): add(("w", j))
    for u in range(nU):
        for j in range(K): add(("y", u, j)); add(("r", u, j))
    for (a, b) in arcs:
        for j in range(K): add(("f", a, b, j))
    nv = len(idx); c = np.zeros(nv)
    for j in range(K): c[idx[("w", j)]] = -1
    A, lo, hi = [], [], []
    def row(coefs, l, h):
        v = np.zeros(nv)
        for k, val in coefs.items(): v[k] += val
        A.append(v); lo.append(l); hi.append(h)
    for i in range(nP): row({idx[("x", i, j)]: 1 for j in range(K)}, 1, 1)
    Mbig, eps = SZ * 1.0, 1e-6
    for j in range(K):
        row({idx[("x", i, j)]: 1 for i in range(nP)}, SZ, SZ)
        co = {idx[("x", i, j)]: (P[i] - 0.5 - m) for i in range(nP)}
        co[idx[("w", j)]] = -(Mbig + eps); row(co, -Mbig, np.inf)
    for j in range(K - 1): row({idx[("w", j)]: 1, idx[("w", j + 1)]: -1}, 0, np.inf)
    for i in range(nP):
        for j in range(K):
            row({idx[("x", i, j)]: 1, idx[("y", unit_of[i], j)]: -1}, -np.inf, 0)   # x <= y
    for u in range(nU):
        for j in range(K):
            # valid strengthening: a true plan touching unit u takes >= 1 whole precinct from u
            co = {idx[("y", u, j)]: 1}
            for i in units[u]: co[idx[("x", i, j)]] = co.get(idx[("x", i, j)], 0) - 1
            row(co, -np.inf, 0)
            row({idx[("r", u, j)]: 1, idx[("y", u, j)]: -1}, -np.inf, 0)             # r <= y
    for j in range(K):
        row({idx[("r", u, j)]: 1 for u in range(nU)}, 1, 1)
        for u in range(nU):
            co = {}
            for (a, b) in arcs:
                if b == u: co[idx[("f", a, b, j)]] = co.get(idx[("f", a, b, j)], 0) + 1
                if a == u: co[idx[("f", a, b, j)]] = co.get(idx[("f", a, b, j)], 0) - 1
            co[idx[("y", u, j)]] = co.get(idx[("y", u, j)], 0) - 1
            co[idx[("r", u, j)]] = co.get(idx[("r", u, j)], 0) + nU
            row(co, 0, np.inf)                       # inflow-outflow >= y - nU*r
        for (a, b) in arcs:
            row({idx[("f", a, b, j)]: 1, idx[("y", a, j)]: -(nU - 1)}, -np.inf, 0)
            row({idx[("f", a, b, j)]: 1, idx[("y", b, j)]: -(nU - 1)}, -np.inf, 0)
    integ = np.zeros(nv); ub = np.ones(nv)
    for j in range(K): integ[idx[("w", j)]] = 1
    for u in range(nU):
        for j in range(K): integ[idx[("y", u, j)]] = 1; integ[idx[("r", u, j)]] = 1
    for (a, b) in arcs:
        for j in range(K): ub[idx[("f", a, b, j)]] = nU
    if x_integer:
        for i in range(nP):
            for j in range(K): integ[idx[("x", i, j)]] = 1
    if y_equals_x:
        for i in range(nP):
            for j in range(K): row({idx[("x", i, j)]: 1, idx[("y", unit_of[i], j)]: -1}, 0, 0)
    res = milp(c, constraints=LinearConstraint(np.array(A), lo, hi), integrality=integ,
               bounds=Bounds(np.zeros(nv), ub), options={"time_limit": time_limit, "mip_rel_gap": 0})
    if res.status != 0: return {"status": int(res.status), "msg": str(res.message)}
    # post-check: if integer & y==x, verify the returned plan is contiguous and balanced
    out = {"status": 0, "value": int(round(-res.fun))}
    if x_integer and y_equals_x:
        x = res.x; ok = True
        for j in range(K):
            cells = [i for i in range(nP) if x[idx[("x", i, j)]] > 0.5]
            ok &= len(cells) == SZ and nx.is_connected(Q.G.subgraph(cells))
        out["returned_plan_contiguous_balanced"] = bool(ok)
    return out

def main():
    t0 = time.time(); R = {}
    plans = Q.enumerate_plans(); n_pl = len(plans)
    DET = np.array([Q.seat_curves(p)[0] for p in plans])
    mu = DET.mean(axis=0)
    delta = (DET - mu) / Q.K
    Gam = delta.mean(axis=1); Gm = np.sqrt((delta ** 2).mean(axis=1))
    Cc = np.abs(Gam) / Gm
    # C5b
    pct = lambda v: float((Gm < v).mean())
    low_c = np.flatnonzero(Cc < 0.25)
    best_lowc = int(low_c[np.argmax(Gm[low_c])])
    slope = np.array([np.polyfit(Q.V_GRID, DET[k] / Q.K, 1)[0] for k in range(n_pl)])
    slope_mu = np.polyfit(Q.V_GRID, mu / Q.K, 1)[0]
    R["C5b"] = {
        "max_G_among_plans_with_C<0.25": float(Gm[best_lowc]),
        "its_G_percentile": pct(Gm[best_lowc]),
        "its_Gamma": float(Gam[best_lowc]), "its_C": float(Cc[best_lowc]),
        "its_slope_minus_ensemble_slope": float(slope[best_lowc] - slope_mu),
        "share_of_top_decile_G_with_C<0.5": float(np.mean(Cc[Gm >= np.quantile(Gm, 0.9)] < 0.5)),
        "corr(G, |slope - slope_mu|)": float(np.corrcoef(Gm, np.abs(slope - slope_mu))[0, 1]),
        "corr(G, |Gamma|)": float(np.corrcoef(Gm, np.abs(Gam))[0, 1]),
    }
    # C8b
    cells = [[i] for i in range(len(Q.P))]
    rg = [[0, 1], [2], [3, 4]]
    blocks9 = [[Q.cell(r, c) for r in R_ for c in C_] for R_ in rg for C_ in rg]
    rows5 = [[Q.cell(r, c) for c in range(5)] for r in range(5)]
    sh0 = np.array([Q.district_shares(p) for p in plans])
    R["C8b"] = {}
    for m in [0.0, 0.02, 0.05]:
        exact = int((sh0 > 0.5).sum(axis=1).max()) if m == 0 else int((sh0 >= 0.5 + m).sum(axis=1).max())
        ex_milp = flow_milp(m, cells, x_integer=True, y_equals_x=True)
        fr_cells = flow_milp(m, cells, x_integer=False)
        fr_blk = flow_milp(m, blocks9, x_integer=False)
        fr_rows = flow_milp(m, rows5, x_integer=False)
        vals = [exact, fr_cells.get("value"), fr_blk.get("value"), fr_rows.get("value")]
        R["C8b"][f"m={m}"] = {
            "exact_enumeration": exact,
            "exact_flowMILP": ex_milp,
            "relax_units=precincts_fracx": fr_cells.get("value"),
            "relax_units=9blocks_fracx": fr_blk.get("value"),
            "relax_units=5rows_fracx": fr_rows.get("value"),
            "flowMILP_matches_enumeration": ex_milp.get("value") == exact,
            "all_bounds_valid(>=exact)": all(v is not None and v >= exact for v in vals[1:]),
        }
    R["runtime_sec"] = round(time.time() - t0, 1)
    out = os.path.join(Q.OUT_DIR, "qc_results_iter2.json")
    json.dump(R, open(out, "w"), indent=2)
    print(json.dumps(R, indent=2))

if __name__ == "__main__":
    main()
