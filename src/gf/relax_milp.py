"""Independent re-implementation of the aggregated relaxation R(P,q,s) as a MILP solved by HiGHS.

Purpose: cross-audit of CP-SAT verdicts.  Same mathematical relaxation, DIFFERENT encoding and solver:
  * connectivity of each district's cell support via a single-commodity flow (not parent pointers);
  * county-split budget as one linear row sum_K sum_j t[K,j] <= s + #counties;
  * floating-point HiGHS with OUTER-SAFE tolerances (populations widened by 0.5 person, safety rows loosened by a
    tiny fraction of a typical atom), so that an 'infeasible' verdict cannot come from round-off.
Only used for verification, never to produce reported bounds.
"""
from __future__ import annotations

import time

import numpy as np
import scipy.sparse as sp
from scipy.optimize import milp, LinearConstraint, Bounds

from .agg import cell_env
from .core import Regime, pop_window, safety_coeffs
from .data import Instance
from .hier import Partition


def solve_agg_milp(inst: Instance, reg: Regime, part: Partition, q: int, cap: int | None = None,
                   time_limit: float = 120.0, nb: int = 10):
    k, n = inst.k, inst.n
    T = int(inst.pop.sum())
    lo, hi = pop_window(T, k, reg.eps)
    C = safety_coeffs(inst, reg)
    W = C.shape[0]
    nc = part.ncells
    cells = part.cells
    env = [cell_env(inst, C, cells[c], nb) for c in range(nc)]
    single = [len(a) == 1 for a in cells]
    arcs = []
    for a, b in part.qedges:
        arcs.append((int(a), int(b)))
        arcs.append((int(b), int(a)))
    na = len(arcs)
    # ---- variable indexing -------------------------------------------------------------
    idx = {}
    nv = 0

    def var(name):
        nonlocal nv
        idx[name] = nv
        nv += 1
        return idx[name]

    for c in range(nc):
        for j in range(k):
            var(("y", c, j))
            if not single[c]:
                var(("p", c, j))
                var(("s", c, j))
                if j < q:
                    for w in range(W):
                        var(("c", c, j, w))
    for j in range(k):
        for c in range(nc):
            var(("r", c, j))            # root indicator
            var(("g", c, j))            # root supply (flow)
        for e in range(na):
            var(("f", e, j))
    ncty = int(inst.county.max()) + 1
    cty_of_cell = [int(inst.county[cells[c][0]]) for c in range(nc)]
    if cap is not None:
        for cty in range(ncty):
            for j in range(k):
                var(("t", cty, j))
    integrality = np.zeros(nv)
    lb = np.zeros(nv)
    ub = np.ones(nv)
    for name, i in idx.items():
        t = name[0]
        if t in ("y", "r", "s", "t"):
            integrality[i] = 1
        elif t == "p":
            ub[i] = env[name[1]].P
            integrality[i] = 0
        elif t == "c":
            e = env[name[1]]
            lb[i] = min(e.cneg[name[3]], 0)
            ub[i] = max(e.cpos[name[3]], 0)
        elif t == "g":
            ub[i] = nc
        elif t == "f":
            ub[i] = nc
    rows, cols, vals, rl, ru = [], [], [], [], []
    r = 0

    def add(terms, l, u):
        nonlocal r
        for i, v in terms:
            rows.append(r)
            cols.append(i)
            vals.append(v)
        rl.append(l)
        ru.append(u)
        r += 1

    INF = np.inf
    pslack = 0.5
    for c in range(nc):
        e = env[c]
        # exactly/at least one district supports the cell
        if single[c]:
            add([(idx[("y", c, j)], 1.0) for j in range(k)], 1.0, 1.0)
        else:
            add([(idx[("y", c, j)], 1.0) for j in range(k)], 1.0, INF)
            add([(idx[("p", c, j)], 1.0) for j in range(k)], e.P - 1e-6, e.P + 1e-6)
            for j in range(k):
                yv, pv, sv = idx[("y", c, j)], idx[("p", c, j)], idx[("s", c, j)]
                add([(pv, 1.0), (yv, -float(e.P))], -INF, 0.0)
                if e.pmin > 0:
                    add([(pv, 1.0), (yv, -float(e.pmin))], 0.0, INF)
                # s_j <= y_j ; s_j + y_j' <= 1 ; s_j >= y_j - sum_{j'!=j} y_j'
                add([(sv, 1.0), (yv, -1.0)], -INF, 0.0)
                for j2 in range(k):
                    if j2 != j:
                        add([(sv, 1.0), (idx[("y", c, j2)], 1.0)], -INF, 1.0)
                add([(sv, 1.0), (yv, -1.0)] + [(idx[("y", c, j2)], 1.0) for j2 in range(k) if j2 != j], -0.0, INF)
                # whole cell => p = P
                add([(pv, 1.0), (sv, -float(e.P))], 0.0, INF)          # p >= P*s
        # safety-mass variables and envelopes for j<q
        if not single[c]:
            for w in range(W):
                for j in range(q):
                    cv, pv, yv, sv = idx[("c", c, j, w)], idx[("p", c, j)], idx[("y", c, j)], idx[("s", c, j)]
                    add([(cv, 1.0), (yv, -float(e.cpos[w]))], -INF, 0.0)
                    add([(cv, 1.0), (yv, -float(e.cneg[w]))], 0.0, INF)
                    # c = csum when whole:  |c - csum| <= M (1 - s)
                    Mbig = float(e.cpos[w] - e.cneg[w]) + 1.0
                    add([(cv, 1.0), (sv, Mbig)], -INF, float(e.csum[w]) + Mbig)
                    add([(cv, 1.0), (sv, -Mbig)], float(e.csum[w]) - Mbig, INF)
                    for a, b, rr_ in e.up[w]:
                        add([(cv, float(a)), (pv, -float(b))], -INF, float(rr_) + 1e-3 * abs(a))
                    for a, b, rr_ in e.low[w]:
                        add([(cv, float(a)), (pv, -float(b))], float(rr_) - 1e-3 * abs(a), INF)
                if q >= 2:
                    terms_c = [(idx[("c", c, j, w)], 1.0) for j in range(q)]
                    terms_p = [(idx[("p", c, j)], 1.0) for j in range(q)]
                    for a, b, rr_ in e.up[w]:
                        add([(i, float(a) * v) for i, v in terms_c] + [(i, -float(b) * v) for i, v in terms_p], -INF,
                            float(rr_) + 1e-3 * abs(a))
                    for a, b, rr_ in e.low[w]:
                        add([(i, float(a) * v) for i, v in terms_c] + [(i, -float(b) * v) for i, v in terms_p],
                            float(rr_) - 1e-3 * abs(a), INF)

    def pop_terms(j):
        out = []
        for c in range(nc):
            if single[c]:
                out.append((idx[("y", c, j)], float(env[c].P)))
            else:
                out.append((idx[("p", c, j)], 1.0))
        return out

    def c_terms(j, w):
        out = []
        for c in range(nc):
            if single[c]:
                out.append((idx[("y", c, j)], float(env[c].csum[w])))
            else:
                out.append((idx[("c", c, j, w)], 1.0))
        return out

    for j in range(k):
        add(pop_terms(j), lo - pslack, hi + pslack)
    for j in range(q):
        for w in range(W):
            tol = 1e-3 * max(np.abs(C[w]).mean(), 1.0)
            add(c_terms(j, w), -tol, INF)

    # ---- connectivity via single-commodity flow on the quotient graph ----------------------
    for j in range(k):
        add([(idx[("r", c, j)], 1.0) for c in range(nc)], 1.0, 1.0)
        for c in range(nc):
            yv = idx[("y", c, j)]
            add([(idx[("r", c, j)], 1.0), (yv, -1.0)], -INF, 0.0)
            add([(idx[("g", c, j)], 1.0), (idx[("r", c, j)], -float(nc))], -INF, 0.0)
        for c in range(nc):
            terms = [(idx[("f", e, j)], 1.0) for e, (a, b) in enumerate(arcs) if b == c]
            terms += [(idx[("f", e, j)], -1.0) for e, (a, b) in enumerate(arcs) if a == c]
            terms += [(idx[("g", c, j)], 1.0), (idx[("y", c, j)], -1.0)]
            add(terms, 0.0, 0.0)          # inflow - outflow + supply = y
        for e, (a, b) in enumerate(arcs):
            add([(idx[("f", e, j)], 1.0), (idx[("y", a, j)], -float(nc))], -INF, 0.0)
            add([(idx[("f", e, j)], 1.0), (idx[("y", b, j)], -float(nc))], -INF, 0.0)

    # ---- county split budget ---------------------------------------------------------------
    if cap is not None:
        by = {}
        for c in range(nc):
            by.setdefault(cty_of_cell[c], []).append(c)
        for cty in range(ncty):
            for j in range(k):
                tv = idx[("t", cty, j)]
                for c in by.get(cty, []):
                    add([(tv, 1.0), (idx[("y", c, j)], -1.0)], 0.0, INF)          # t >= y
                add([(tv, 1.0)] + [(idx[("y", c, j)], -1.0) for c in by.get(cty, [])], -INF, 0.0)  # t <= sum y
        # sum_K (d_K - 1) <= s  with d_K = sum_j t[K,j]
        nonempty = sum(1 for cty in range(ncty) if by.get(cty))
        add([(idx[("t", cty, j)], 1.0) for cty in range(ncty) for j in range(k) if by.get(cty)], -INF, float(cap + nonempty))

    A = sp.csr_matrix((vals, (rows, cols)), shape=(r, nv))
    res = milp(np.zeros(nv), constraints=LinearConstraint(A, np.array(rl), np.array(ru)), integrality=integrality,
               bounds=Bounds(lb, ub), options={"time_limit": time_limit, "disp": False})
    if res.status == 2:
        return "infeasible"
    if res.status == 0 or (res.x is not None and res.status == 1):
        return "feasible"
    return "unknown"
