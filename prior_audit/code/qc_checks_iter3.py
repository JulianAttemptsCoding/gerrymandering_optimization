#!/usr/bin/env python3
"""
Iteration-3 QC: adaptive refinement ("refine only units the relaxation splits").
Start from 9 coarse blocks; solve fractional-x flow relaxation; split every multi-precinct
unit that the optimal relaxed solution shares among >= 2 districts; repeat.
Each step is a valid upper bound (finer units => smaller relaxed feasible set).
Stop when bound == best known feasible value (certificate) or nothing left to split.
"""
import json, os, time
import numpy as np
import qc_checks as Q
import qc_checks_iter2 as Q2
from scipy.optimize import milp, LinearConstraint, Bounds

def solve_with_x(m, units):
    # re-use iter2 builder but we need x: monkeypatch by re-running milp inside a copy
    import networkx as nx
    P, K, SZ = Q.P, Q.K, Q.SZ; nP = len(P)
    unit_of = {i: u for u, cells in enumerate(units) for i in cells}; nU = len(units)
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
    def row(co, l, h):
        v = np.zeros(nv)
        for k, val in co.items(): v[k] += val
        A.append(v); lo.append(l); hi.append(h)
    for i in range(nP): row({idx[("x", i, j)]: 1 for j in range(K)}, 1, 1)
    for j in range(K):
        row({idx[("x", i, j)]: 1 for i in range(nP)}, SZ, SZ)
        co = {idx[("x", i, j)]: (P[i] - 0.5 - m) for i in range(nP)}
        co[idx[("w", j)]] = -(SZ + 1e-6); row(co, -SZ, np.inf)
    for j in range(K - 1): row({idx[("w", j)]: 1, idx[("w", j + 1)]: -1}, 0, np.inf)
    for i in range(nP):
        for j in range(K): row({idx[("x", i, j)]: 1, idx[("y", unit_of[i], j)]: -1}, -np.inf, 0)
    for u in range(nU):
        for j in range(K):
            co = {idx[("y", u, j)]: 1}
            for i in units[u]: co[idx[("x", i, j)]] = -1
            row(co, -np.inf, 0); row({idx[("r", u, j)]: 1, idx[("y", u, j)]: -1}, -np.inf, 0)
    for j in range(K):
        row({idx[("r", u, j)]: 1 for u in range(nU)}, 1, 1)
        for u in range(nU):
            co = {}
            for (a, b) in arcs:
                if b == u: co[idx[("f", a, b, j)]] = co.get(idx[("f", a, b, j)], 0) + 1
                if a == u: co[idx[("f", a, b, j)]] = co.get(idx[("f", a, b, j)], 0) - 1
            co[idx[("y", u, j)]] = co.get(idx[("y", u, j)], 0) - 1
            co[idx[("r", u, j)]] = co.get(idx[("r", u, j)], 0) + nU
            row(co, 0, np.inf)
        for (a, b) in arcs:
            row({idx[("f", a, b, j)]: 1, idx[("y", a, j)]: -(nU - 1)}, -np.inf, 0)
            row({idx[("f", a, b, j)]: 1, idx[("y", b, j)]: -(nU - 1)}, -np.inf, 0)
    integ = np.zeros(nv); ub = np.ones(nv)
    for j in range(K): integ[idx[("w", j)]] = 1
    for u in range(nU):
        for j in range(K): integ[idx[("y", u, j)]] = 1; integ[idx[("r", u, j)]] = 1
    for (a, b) in arcs:
        for j in range(K): ub[idx[("f", a, b, j)]] = nU
    res = milp(c, constraints=LinearConstraint(np.array(A), lo, hi), integrality=integ,
               bounds=Bounds(np.zeros(nv), ub), options={"time_limit": 300, "mip_rel_gap": 0})
    X = np.array([[res.x[idx[("x", i, j)]] for j in range(K)] for i in range(nP)])
    return int(round(-res.fun)), X

def main():
    t0 = time.time(); R = {}
    plans = Q.enumerate_plans()
    sh0 = np.array([Q.district_shares(p) for p in plans])
    rg = [[0, 1], [2], [3, 4]]
    for m in [0.0, 0.02]:
        exact = int((sh0 > 0.5).sum(axis=1).max()) if m == 0 else int((sh0 >= 0.5 + m).sum(axis=1).max())
        units = [[Q.cell(r, c) for r in R_ for c in C_] for R_ in rg for C_ in rg]
        trace = []
        for it in range(10):
            ub, X = solve_with_x(m, units)
            trace.append({"iter": it, "n_units": len(units), "upper_bound": ub})
            if ub == exact: break
            new_units, split_any = [], False
            for u in units:
                shared = int(np.sum(X[u].sum(axis=0) > 1e-6))
                if len(u) > 1 and shared >= 2:
                    new_units += [[i] for i in u]; split_any = True
                else:
                    new_units.append(u)
            if not split_any: break
            units = new_units
        R[f"m={m}"] = {"exact": exact, "trace": trace,
                       "certified": trace[-1]["upper_bound"] == exact,
                       "final_units_vs_precincts": f"{trace[-1]['n_units']}/25"}
    R["runtime_sec"] = round(time.time() - t0, 1)
    json.dump(R, open(os.path.join(Q.OUT_DIR, "qc_results_iter3.json"), "w"), indent=2)
    print(json.dumps(R, indent=2))

if __name__ == "__main__":
    main()
